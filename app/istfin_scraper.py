"""Official Borsa Istanbul index catalogue reader.

Borsa İstanbul's catalogue page renders its index table dynamically and does
not expose individual index links in the static HTML. Verify the four official
index detail pages directly instead. Memberships remain disabled until a
complete official constituent source is available; never fabricate symbols.
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
    code = code.strip().upper()
    record = next((dict(row) for row in get_indexes(force_refresh) if row["code"] == code), None)
    if record is None:
        raise KeyError(code)
    raise RuntimeError(
        f"{code}: Borsa İstanbul public index page confirms the index but does not expose "
        "the complete current constituent list in its public HTML. Membership was not guessed. "
        "A complete official constituent file or authorized BIST data feed is required."
    )
