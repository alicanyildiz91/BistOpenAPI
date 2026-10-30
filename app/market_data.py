"""Yahoo Finance and borsapy adapters. Third-party delay/coverage are not guaranteed."""
import os
from datetime import datetime, timezone
from typing import Any

PROVIDER_ENV = "BISTOPENAPI_PROVIDER"
API_KEY_ENV = "BISTOPENAPI_API_KEY"
VALID_PROVIDERS = {"demo", "yfinance", "borsapy"}
INTRADAY_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m"}
VALID_INTERVALS = INTRADAY_INTERVALS | {"1d", "5d", "1wk", "1mo", "3mo"}
VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"}


def provider_mode() -> str:
    mode = os.getenv(PROVIDER_ENV, "demo").strip().lower()
    return mode if mode in VALID_PROVIDERS else "demo"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _symbol(symbol: str) -> str:
    clean = symbol.strip().upper().removesuffix(".IS")
    if not clean or not clean.replace(".", "").isalnum():
        raise ValueError("Invalid BIST symbol.")
    return clean


def _yahoo_symbol(symbol: str) -> str:
    return f"{_symbol(symbol)}.IS"


def market_status() -> dict[str, Any]:
    mode = provider_mode()
    enabled = mode in {"yfinance", "borsapy"}
    return {
        "name": mode,
        "mode": "delayed_external_unverified" if enabled else "demo",
        "live_data_available": False,
        "provider_configured": enabled and bool(os.getenv(API_KEY_ENV)),
        "access_protected": enabled,
        "note": (
            "Yahoo Finance via yfinance is unofficial; BIST coverage, delay and fields vary by symbol. "
            "Retrieved time is not necessarily the exchange trade time. No real-time guarantee."
            if mode == "yfinance" else
            "borsapy aggregates external sources; endpoint coverage and delay vary."
            if mode == "borsapy" else
            "Demo mode does not return real market prices."
        ),
    }


def _enabled_mode() -> str:
    mode = provider_mode()
    if mode == "demo":
        raise RuntimeError("Market-data provider is disabled.")
    if not os.getenv(API_KEY_ENV):
        raise RuntimeError(f"{API_KEY_ENV} must be configured before enabling market data.")
    return mode


def _ticker(symbol: str):
    mode = _enabled_mode()
    clean = _symbol(symbol)
    try:
        if mode == "yfinance":
            import yfinance as yf
            return yf.Ticker(_yahoo_symbol(clean)), clean
        import borsapy as bp
        return bp.Ticker(clean), clean
    except ImportError as exc:
        raise RuntimeError(f"{mode} package is not installed.") from exc


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    try:
        return dict(value)
    except Exception:
        try:
            return {key: value[key] for key in value.keys()}
        except Exception:
            return {}


def _number(info: dict, *keys: str):
    for key in keys:
        try:
            value = float(info.get(key))
            if value > 0:
                return value
        except (TypeError, ValueError, OverflowError):
            pass
    return None


def get_quote(symbol: str) -> dict[str, Any]:
    ticker, clean = _ticker(symbol)
    mode = provider_mode()
    try:
        info = _mapping(ticker.fast_info)
        if not info:
            info = _mapping(ticker.info)
    except Exception as exc:
        raise RuntimeError(f"Upstream quote request failed: {type(exc).__name__}") from exc
    price = _number(info, "last_price", "last", "currentPrice", "regularMarketPrice", "close", "price", "lastPrice")
    if price is None:
        try:
            info = _mapping(ticker.info)
            price = _number(info, "last", "last_price", "currentPrice", "regularMarketPrice", "close", "price")
        except Exception:
            pass
    if price is None:
        raise RuntimeError("Provider returned no usable price for this symbol.")
    return {
        "symbol": clean, "provider_symbol": _yahoo_symbol(clean) if mode == "yfinance" else clean,
        "price": price, "currency": info.get("currency") or "TRY",
        "open": _number(info, "open", "regularMarketOpen"),
        "day_high": _number(info, "day_high", "dayHigh", "regularMarketDayHigh"),
        "day_low": _number(info, "day_low", "dayLow", "regularMarketDayLow"),
        "previous_close": _number(info, "previous_close", "previousClose", "regularMarketPreviousClose"),
        "volume": info.get("volume") or info.get("regularMarketVolume"),
        "market_cap": info.get("market_cap") or info.get("marketCap"),
        "source": mode, "data_mode": "delayed_external_unverified",
        "provider_timestamp": info.get("last_trade_time") or info.get("regularMarketTime"),
        "retrieved_at": _now(),
        "timestamp_semantics": "provider_timestamp_may_be_missing; retrieved_at_is_fetch_time",
    }


def _rows(frame, limit: int) -> list[dict]:
    if frame is None or getattr(frame, "empty", True):
        return []
    rows = []
    for stamp, row in frame.tail(limit).iterrows():
        item = {"timestamp": stamp.isoformat() if hasattr(stamp, "isoformat") else str(stamp)}
        for col in ("Open", "High", "Low", "Close", "Adj Close", "Volume"):
            key = {"Adj Close": "adj_close"}.get(col, col.lower())
            try:
                value = row.get(col)
                item[key] = None if value is None else float(value)
            except (TypeError, ValueError, OverflowError):
                item[key] = None
        rows.append(item)
    return rows


def get_ohlcv(symbol: str, interval: str, limit: int, period: str = "1y") -> dict[str, Any]:
    ticker, clean = _ticker(symbol)
    if interval not in VALID_INTERVALS or period not in VALID_PERIODS:
        raise ValueError("Unsupported interval or period.")
    if interval in INTRADAY_INTERVALS and period not in {"1d", "5d", "1mo", "3mo", "6mo"}:
        raise ValueError("Intraday lookback is limited upstream; use period 6mo or shorter.")
    try:
        try:
            frame = ticker.history(period=period, interval=interval, auto_adjust=False)
        except TypeError:
            frame = ticker.history(period=period, interval=interval)
    except Exception as exc:
        raise RuntimeError(f"Upstream history request failed: {type(exc).__name__}") from exc
    candles = _rows(frame, limit)
    if not candles:
        raise RuntimeError("Provider returned no historical candles for this symbol/interval.")
    return {
        "symbol": clean, "interval": interval, "period": period,
        "source": provider_mode(), "data_mode": "delayed_external_unverified",
        "count": len(candles), "candles": candles, "retrieved_at": _now(),
        "note": "History depth and delay depend on the upstream provider.",
    }


def _yahoo_only():
    if provider_mode() != "yfinance":
        raise RuntimeError("This endpoint currently requires BISTOPENAPI_PROVIDER=yfinance.")


def get_fundamentals(symbol: str) -> dict[str, Any]:
    ticker, clean = _ticker(symbol)
    _yahoo_only()
    try:
        info = _mapping(ticker.info)
    except Exception as exc:
        raise RuntimeError(f"Upstream fundamentals request failed: {type(exc).__name__}") from exc
    fields = (
        "shortName", "longName", "sector", "industry", "marketCap", "enterpriseValue",
        "trailingPE", "forwardPE", "priceToBook", "priceToSalesTrailing12Months",
        "enterpriseToEbitda", "profitMargins", "operatingMargins", "returnOnEquity",
        "returnOnAssets", "revenueGrowth", "earningsGrowth", "debtToEquity",
        "currentRatio", "quickRatio", "dividendYield", "beta", "sharesOutstanding",
        "floatShares", "currency",
    )
    return {"symbol": clean, "source": "yfinance", "retrieved_at": _now(),
            "data": {key: info.get(key) for key in fields if info.get(key) is not None},
            "note": "BIST field coverage may be incomplete or stale."}


def get_financials(symbol: str) -> dict[str, Any]:
    ticker, clean = _ticker(symbol)
    _yahoo_only()
    statements = {}
    for key, attr in (("income_statement", "income_stmt"), ("balance_sheet", "balance_sheet"),
                      ("cash_flow", "cashflow")):
        try:
            frame = getattr(ticker, attr)
            statements[key] = frame.where(frame.notna(), None).to_dict() if frame is not None and not frame.empty else {}
        except Exception:
            statements[key] = {}
    return {"symbol": clean, "source": "yfinance", "retrieved_at": _now(), "statements": statements}


def get_actions(symbol: str) -> dict[str, Any]:
    ticker, clean = _ticker(symbol)
    _yahoo_only()
    try:
        frame = ticker.actions
        actions = []
        if frame is not None and not frame.empty:
            for stamp, row in frame.tail(100).iterrows():
                actions.append({
                    "date": stamp.isoformat() if hasattr(stamp, "isoformat") else str(stamp),
                    "dividends": float(row.get("Dividends", 0) or 0),
                    "stock_splits": float(row.get("Stock Splits", 0) or 0),
                })
        return {"symbol": clean, "source": "yfinance", "retrieved_at": _now(), "actions": actions}
    except Exception as exc:
        raise RuntimeError(f"Upstream corporate-actions request failed: {type(exc).__name__}") from exc


def get_news(symbol: str) -> dict[str, Any]:
    ticker, clean = _ticker(symbol)
    _yahoo_only()
    try:
        raw = ticker.news or []
        items = []
        for item in raw[:30]:
            data = item.get("content", item)
            provider = data.get("provider") or {}
            canonical = data.get("canonicalUrl") or {}
            items.append({
                "title": data.get("title"),
                "publisher": provider.get("displayName") if isinstance(provider, dict) else None,
                "link": canonical.get("url") if isinstance(canonical, dict) else data.get("link"),
                "published_at": data.get("pubDate") or data.get("providerPublishTime"),
            })
        return {"symbol": clean, "source": "yfinance", "retrieved_at": _now(), "news": items}
    except Exception as exc:
        raise RuntimeError(f"Upstream news request failed: {type(exc).__name__}") from exc


def get_quotes_batch(symbols: list[str]) -> dict[str, Any]:
    if not symbols or len(symbols) > 100:
        raise ValueError("Provide between 1 and 100 symbols.")
    quotes, errors = [], []
    for symbol in symbols:
        try:
            quotes.append(get_quote(symbol))
        except Exception as exc:
            errors.append({"symbol": symbol, "error": str(exc)})
    return {"source": provider_mode(), "retrieved_at": _now(), "count": len(quotes), "errors": errors, "quotes": quotes}


def get_ohlcv_batch(symbols: list[str], interval: str, limit: int, period: str) -> dict[str, Any]:
    if not symbols or len(symbols) > 50:
        raise ValueError("Provide between 1 and 50 symbols.")
    data, errors = [], []
    for symbol in symbols:
        try:
            data.append(get_ohlcv(symbol, interval, limit, period))
        except Exception as exc:
            errors.append({"symbol": symbol, "error": str(exc)})
    return {"source": provider_mode(), "retrieved_at": _now(), "count": len(data), "errors": errors, "data": data}
