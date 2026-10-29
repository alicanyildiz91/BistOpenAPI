import os
from datetime import datetime, timezone
from typing import Any

PROVIDER_ENV = "BISTOPENAPI_PROVIDER"
API_KEY_ENV = "BISTOPENAPI_API_KEY"


def provider_mode() -> str:
    return os.getenv(PROVIDER_ENV, "demo").strip().lower()


def market_status() -> dict[str, Any]:
    enabled = provider_mode() == "borsapy"
    configured = enabled and bool(os.getenv(API_KEY_ENV))
    return {
        "name": "borsapy" if enabled else "demo",
        "mode": "external_source_delay_unverified" if enabled else "demo",
        # Configuration only proves that the adapter is enabled; it does not
        # prove real-time delivery or per-symbol availability.
        "live_data_available": False,
        "provider_configured": configured,
        "access_protected": enabled,
        "note": (
            "borsapy aggregates external sources that vary by endpoint. Provider configuration does not prove real-time delivery; verify per-symbol timestamps and terms. Do not redistribute without permission."
            if enabled else "No real market prices are served in demo mode."
        ),
    }


def _ticker(symbol: str):
    if provider_mode() != "borsapy":
        raise RuntimeError("Market-data provider is not enabled.")
    if not os.getenv(API_KEY_ENV):
        raise RuntimeError("BISTOPENAPI_API_KEY must be configured before enabling market data.")
    try:
        import borsapy as bp
    except ImportError as exc:
        raise RuntimeError("borsapy is not installed in this deployment.") from exc
    clean_symbol = symbol.strip().upper()
    if not clean_symbol or not clean_symbol.replace(".", "").isalnum():
        raise ValueError("Invalid symbol.")
    return bp.Ticker(clean_symbol)


def _as_mapping(value: Any) -> dict[str, Any]:
    """Normalize dict-like provider objects without assuming every object is iterable."""
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    try:
        converted = dict(value)
        if isinstance(converted, dict):
            return converted
    except (TypeError, ValueError):
        pass
    # Some provider versions expose a mapping-like object with keys()/getitem().
    try:
        return {key: value[key] for key in value.keys()}
    except Exception:
        return {}


def get_quote(symbol: str) -> dict[str, Any]:
    ticker = _ticker(symbol)
    info: dict[str, Any] = {}

    # borsapy documents fast_info["last_price"] as the quick quote field.
    # Prefer it, then fall back to the detailed info object for compatibility.
    try:
        info = _as_mapping(ticker.fast_info)
    except Exception:
        info = {}

    if not info:
        try:
            info = _as_mapping(ticker.info)
        except Exception as exc:
            raise RuntimeError(f"Upstream quote request failed: {type(exc).__name__}") from exc

    price = None
    for key in (
        "last_price", "last", "currentPrice", "regularMarketPrice",
        "close", "price", "lastPrice",
    ):
        value = info.get(key)
        if value is not None:
            try:
                candidate = float(value)
                if candidate > 0:
                    price = candidate
                    break
            except (TypeError, ValueError, OverflowError):
                continue

    # If fast_info is present but has no usable price, try detailed info once.
    if price is None:
        try:
            detailed = _as_mapping(ticker.info)
        except Exception:
            detailed = {}
        for key in ("last", "last_price", "currentPrice", "regularMarketPrice", "close", "price"):
            value = detailed.get(key)
            try:
                candidate = float(value)
                if candidate > 0:
                    price = candidate
                    info = detailed
                    break
            except (TypeError, ValueError, OverflowError):
                continue

    if price is None:
        raise RuntimeError("Provider returned no usable price for this symbol.")
    return {
        "symbol": symbol.upper(),
        "price": price,
        "currency": info.get("currency") or "TRY",
        "source": "borsapy",
        "data_mode": "external_source_delay_unverified",
        "source_note": "borsapy; upstream source varies by endpoint",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timestamp_semantics": "retrieval_time_not_exchange_trade_time",
        "note": "Provider timestamps and delay may vary; verify before trading.",
    }


def get_ohlcv(symbol: str, interval: str, limit: int) -> dict[str, Any]:
    ticker = _ticker(symbol)
    try:
        frame = ticker.history(period="1y", interval=interval)
    except Exception as exc:
        raise RuntimeError(f"Upstream history request failed: {type(exc).__name__}") from exc
    if frame is None or getattr(frame, "empty", True):
        raise RuntimeError("Provider returned no historical candles for this symbol.")
    rows = []
    try:
        for index, row in frame.tail(limit).iterrows():
            stamp = index.isoformat() if hasattr(index, "isoformat") else str(index)
            item = {"timestamp": stamp}
            for source_key, target_key in (
                ("Open", "open"), ("High", "high"), ("Low", "low"),
                ("Close", "close"), ("Volume", "volume"),
            ):
                value = row.get(source_key)
                if value is None:
                    value = row.get(target_key)
                try:
                    value = float(value) if value is not None else None
                except (TypeError, ValueError):
                    value = None
                item[target_key] = value
            rows.append(item)
    except Exception as exc:
        raise RuntimeError("Could not normalize provider history response.") from exc
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "source": "borsapy",
        "data_mode": "external_source_delay_unverified",
        "source_note": "borsapy; upstream source varies by endpoint",
        "count": len(rows),
        "candles": rows,
        "note": "Availability and delay depend on the upstream source.",
    }
