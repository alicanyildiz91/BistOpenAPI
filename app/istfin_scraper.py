"""Official Borsa Istanbul index catalogue reader.

The public BIST index pages identify benchmark indices, but do not expose a
complete live constituent list in their rendered public HTML. This module
therefore publishes only the four requested official index definitions and
fails closed for memberships until a complete official constituent source is
available. It never uses ISTFIN or fabricates symbols.
"""
from __future__ import annotations

import re
import threading
import time
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://www.borsaistanbul.com"
INDEX_URL = f"{BASE}/endeksler"
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


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.href: str | None = None
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.href is not None:
            self.links.append((self.href, " ".join("".join(self.text).split())))
            self.href = None
            self.text = []


def _get(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "BistOpenAPI/0.4 (+official Borsa Istanbul index reader)",
            "Accept": "text/html",
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

    html = _get(INDEX_URL)
    parser = _LinkParser()
    parser.feed(html)
    discovered = set()
    for href, _label in parser.links:
        match = re.search(r"/endeks/xu(030|050|100|500)(?:[/?#]|$)", href, re.I)
        if match:
            discovered.add("XU" + match.group(1))

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
