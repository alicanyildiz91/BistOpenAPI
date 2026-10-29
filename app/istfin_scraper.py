"""Read public BIST index names and constituents from istfin.com public pages.

This scrapes only public page HTML (not the paid API). It is cached in-process and
fails closed: if a page changes or no constituents are found, callers get an error
rather than fabricated membership.
"""
from __future__ import annotations

from html.parser import HTMLParser
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.index_catalog import INDEX_NAMES

BASE = "https://istfin.com"
INDEX_URL = f"{BASE}/endeksler"
CACHE_TTL = 6 * 60 * 60
_lock = threading.Lock()
_indexes_cache: list[dict] = []
_indexes_at = 0.0
_members_cache: dict[str, tuple[float, list[str]]] = {}


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None
            self._text = []


def _get(url: str) -> str:
    request = Request(url, headers={"User-Agent": "BistOpenAPI/0.3 (+public index catalogue reader)", "Accept": "text/html"})
    try:
        with urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise RuntimeError(f"istfin page returned HTTP {response.status}")
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not fetch public istfin page: {type(exc).__name__}") from exc


def get_indexes(force_refresh: bool = False) -> list[dict]:
    global _indexes_cache, _indexes_at
    with _lock:
        if _indexes_cache and not force_refresh and time.monotonic() - _indexes_at < CACHE_TTL:
            return [dict(row) for row in _indexes_cache]
    parser = _LinkParser()
    parser.feed(_get(INDEX_URL))
    found: dict[str, str] = {}
    for href, label in parser.links:
        match = re.fullmatch(r"/endeksler/([A-Za-z0-9]+)", href.split("?", 1)[0].rstrip("/"))
        if not match:
            continue
        code = match.group(1).upper()
        if code in ("ENDEKSLER",):
            continue
        found.setdefault(code, INDEX_NAMES.get(code, label or code))
    if len(found) < 30:
        raise RuntimeError(f"istfin index page returned too few index links ({len(found)})")
    rows = [
        {
            "code": code,
            "name": name,
            "constituentCount": None,
            "asOfDay": None,
            "constituents": [],
            "source": "istfin.com public index page",
            "data_mode": "public_page_scrape",
            "membership_available": False,
        }
        for code, name in sorted(found.items())
    ]
    with _lock:
        _indexes_cache, _indexes_at = rows, time.monotonic()
    return [dict(row) for row in rows]


def get_index(code: str, force_refresh: bool = False) -> dict:
    code = code.strip().upper()
    indexes = get_indexes(force_refresh=force_refresh)
    record = next((dict(row) for row in indexes if row["code"] == code), None)
    if record is None:
        raise KeyError(code)
    now = time.monotonic()
    with _lock:
        cached = _members_cache.get(code)
        if cached and not force_refresh and now - cached[0] < CACHE_TTL:
            record["constituents"] = [{"symbol": symbol, "weight": None} for symbol in cached[1]]
            record["constituentCount"] = len(cached[1])
            record["membership_available"] = True
            return record

    parser = _LinkParser()
    parser.feed(_get(f"{INDEX_URL}/{code}"))
    symbols = []
    for href, label in parser.links:
        path = href.split("?", 1)[0].rstrip("/")
        # Public constituent tables link to /hisseler/SYMBOL.
        match = re.fullmatch(r"/hisseler/([A-Za-z0-9]+)", path)
        if match:
            symbol = match.group(1).upper()
            if 2 <= len(symbol) <= 6 and symbol not in symbols:
                symbols.append(symbol)
    if not symbols:
        raise RuntimeError(f"istfin public page did not expose constituents for {code}")
    with _lock:
        _members_cache[code] = (time.monotonic(), symbols)
    record["constituents"] = [{"symbol": symbol, "weight": None} for symbol in symbols]
    record["constituentCount"] = len(symbols)
    record["membership_available"] = True
    record["asOfDay"] = None
    record["source"] = f"istfin.com/endeksler/{code}"
    record["data_mode"] = "public_page_scrape"
    return record
