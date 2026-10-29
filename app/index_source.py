"""Borsa İstanbul index catalogue and external constituent adapter.

Index names/codes are verified against official Borsa İstanbul detail pages.
Constituents are obtained via borsapy's external TradingView/BIST-linked adapter,
validated for expected count, and rejected if incomplete. This is not a direct
licensed BIST reference-data feed.
"""
from __future__ import annotations

import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://www.borsaistanbul.com"
CACHE_TTL = 6 * 60 * 60
INDEX_NAMES = {
    "XU030": "BIST 30",
    "XU050": "BIST 50",
    "XU100": "BIST 100",
    "XU500": "BIST 500",
}
_lock = threading.Lock()
_indexes_cache: list[dict] = []
_indexes_at = 0.0


def _get(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; BistOpenAPI/0.4; official index catalogue check)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise RuntimeError(f"Borsa İstanbul page returned HTTP {response.status}")
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not fetch Borsa İstanbul page: {type(exc).__name__}") from exc


def get_indexes(force_refresh: bool = False) -> list[dict]:
    global _indexes_cache, _indexes_at
    with _lock:
        if _indexes_cache and not force_refresh and time.monotonic() - _indexes_at < CACHE_TTL:
            return [dict(row) for row in _indexes_cache]

    # The main catalogue table is populated client-side. Verify each official
    # detail page directly instead of searching for links on /endeksler.
    discovered: set[str] = set()
    for code, name in INDEX_NAMES.items():
        html = _get(f"{BASE}/endeks/{code.lower()}")
        if re.search(rf"\b{re.escape(code)}\b", html, re.I) and re.search(
            rf"\b{re.escape(name)}\b", html, re.I
        ):
            discovered.add(code)

    missing = set(INDEX_NAMES) - discovered
    if missing:
        raise RuntimeError(
            "Borsa İstanbul endeks kataloğu doğrulanamadı; eksik kodlar: "
            + ", ".join(sorted(missing))
        )

    rows = [
        {
            "code": code,
            "name": name,
            "constituentCount": None,
            "asOfDay": None,
            "constituents": [],
            "source": f"{BASE}/endeks/{code.lower()}",
            "data_mode": "official_catalog_only",
            "membership_available": False,
        }
        for code, name in INDEX_NAMES.items()
    ]
    with _lock:
        _indexes_cache, _indexes_at = rows, time.monotonic()
    return [dict(row) for row in rows]


def get_index(code: str, force_refresh: bool = False) -> dict:
    """Return index members from borsapy's TradingView/BIST-backed index adapter.

    Index metadata is still checked against Borsa İstanbul's official pages.
    Constituents are sourced through borsapy and are not represented as a
    licensed BIST real-time feed. Validate the expected count and fail closed
    if the upstream list is incomplete.
    """
    code = code.strip().upper()
    record = next((dict(row) for row in get_indexes(force_refresh) if row["code"] == code), None)
    if record is None:
        raise KeyError(code)

    expected_counts = {"XU030": 30, "XU050": 50, "XU100": 100, "XU500": 500}
    try:
        import borsapy as bp
        index_obj = bp.Index(code)
        raw = index_obj.components
    except Exception as exc:
        raise RuntimeError(
            f"{code}: endeks bileşenleri borsapy/TradingView kaynağından alınamadı "
            f"({type(exc).__name__}). Eski veya tahmini liste kullanılmadı."
        ) from exc

    if raw is None:
        raise RuntimeError(f"{code}: kaynak boş endeks bileşen listesi döndürdü.")

    symbols: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            symbol = item.get("symbol") or item.get("ticker") or item.get("code")
        else:
            symbol = item
        symbol = str(symbol or "").strip().upper()
        # Ignore malformed rows rather than passing them to the scanner.
        if symbol and symbol.replace(".", "").isalnum() and symbol not in symbols:
            symbols.append(symbol)

    expected = expected_counts[code]
    if len(symbols) != expected:
        raise RuntimeError(
            f"{code}: endeks bileşen listesi eksik veya beklenmeyen uzunlukta "
            f"({len(symbols)}/{expected}). Sinyal üretimi için liste reddedildi."
        )

    record.update({
        "constituents": [{"symbol": symbol} for symbol in symbols],
        "constituentCount": len(symbols),
        "asOfDay": None,
        "source": "borsapy → TradingView/BIST index components",
        "data_mode": "external_index_components",
        "membership_available": True,
        "membership_note": (
            "Bileşenler borsapy'nin harici endeks sağlayıcısından alınır; "
            "resmî BIST lisanslı veri akışı değildir. Kaynak güncelliği değişebilir."
        ),
    })
    return record
