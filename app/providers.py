"""Security catalogue sourced from XU500 constituents and explicit additions."""
import os
from functools import lru_cache


def _clean_symbols(values):
    result = []
    for value in values:
        symbol = str(value or "").strip().upper().removesuffix(".IS")
        if symbol and symbol.replace(".", "").isalnum() and symbol not in result:
            result.append(symbol)
    return result


@lru_cache(maxsize=1)
def _xu500_symbols():
    try:
        import borsapy as bp
        raw = bp.Index("XU500").components
        values = []
        for item in raw or []:
            values.append(item.get("symbol") or item.get("ticker") or item.get("code")
                          if isinstance(item, dict) else item)
        return _clean_symbols(values)
    except Exception:
        return []


def get_provider():
    additions = _clean_symbols(os.getenv("BIST_SYMBOLS", "").split(","))
    symbols = _clean_symbols(_xu500_symbols() + additions)
    if symbols:
        return {
            "name": "borsapy_index_catalogue",
            "mode": "external_index_components",
            "live_data_available": False,
            "universe": "XU500 constituents plus BIST_SYMBOLS additions",
            "universe_complete": False,
            "stocks": [{"symbol": s, "name": s, "exchange": "BIST", "currency": "TRY",
                        "source": "borsapy", "data_mode": "external_index_components"} for s in symbols],
            "indexes": [],
            "notes": [
                "XU500 membership is not the full BIST listed-equity universe.",
                "Use an official/licensed security master or a maintained BIST daily-bulletin parser for full coverage.",
            ],
        }
    demo = [
        ("THYAO", "Türk Hava Yolları"), ("ASELS", "Aselsan"),
        ("BIMAS", "BİM Birleşik Mağazalar"), ("TUPRS", "Tüpraş"),
        ("AKBNK", "Akbank"), ("GARAN", "Garanti BBVA"),
        ("ISCTR", "Türkiye İş Bankası C"), ("EREGL", "Ereğli Demir ve Çelik"),
        ("KCHOL", "Koç Holding"), ("SISE", "Şişecam"),
    ]
    return {
        "name": "demo", "mode": "demo", "live_data_available": False,
        "universe": "sample_only", "universe_complete": False,
        "stocks": [{"symbol": s, "name": n, "exchange": "BIST", "currency": "TRY",
                    "source": "demo", "data_mode": "demo"} for s, n in demo],
        "indexes": [], "notes": ["Sample list only; no real market prices are served."],
    }
