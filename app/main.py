from datetime import datetime, timezone
import hmac
import os
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.providers import get_provider
from app.market_data import get_quote, get_ohlcv, market_status, provider_mode, get_fundamentals, get_financials, get_actions, get_news, get_quotes_batch, get_ohlcv_batch
from app import index_source

app = FastAPI(
    title="BistOpenAPI",
    version="0.3.0",
    description="Personal BIST analysis API. Demo mode is the default; optional delayed data is API-key protected.",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return """<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BistOpenAPI — Açık BIST API</title><style>
:root{color-scheme:dark;--muted:#9aa8c7;--text:#edf2ff;--accent:#76e0b5;--line:#25314b}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top right,#172b3b 0,#0b1020 48%);font:16px/1.6 system-ui,sans-serif;color:var(--text)}
main{max-width:1050px;margin:auto;padding:30px 22px 70px}.nav{display:flex;justify-content:space-between;align-items:center;margin-bottom:75px}.brand{font-weight:800}.tag{color:var(--accent);border:1px solid #2e6557;padding:4px 10px;border-radius:99px;font-size:12px}
h1{font-size:clamp(2.6rem,7vw,5rem);line-height:1.02;letter-spacing:-.05em;margin:12px 0 22px;max-width:800px}.accent{color:var(--accent)}p{color:var(--muted);max-width:700px}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin:30px 0 55px}a.btn{display:inline-block;background:var(--accent);color:#081611;text-decoration:none;padding:11px 17px;border-radius:10px;font-weight:750}a.secondary{background:#131b2f;border:1px solid var(--line);color:var(--text)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.card{background:#111a2b;border:1px solid var(--line);padding:20px;border-radius:16px}.card h2{margin:0 0 6px;font-size:1.08rem}.card p{font-size:.92rem;margin:0}footer{margin-top:45px;border-top:1px solid var(--line);padding-top:22px;color:var(--muted);font-size:.86rem}
</style></head><body><main><div class="nav"><div class="brand">◈ BistOpenAPI</div><span class="tag">OPEN SOURCE · V0.2</span></div>
<p>Türkiye hisse piyasası için geliştirilen açık kaynak API projesi</p><h1>Piyasa verisine <span class="accent">açık erişim.</span></h1>
<p>Kişisel BIST analiz botları için REST API, otomatik dokümantasyon ve değiştirilebilir veri sağlayıcıları.</p>
<div class="actions"><a class="btn" href="/docs">API dokümantasyonu ↗</a><a class="btn secondary" href="https://github.com/alicanyildiz91/BistOpenAPI">GitHub kaynak kodu ↗</a></div>
<div class="grid"><div class="card"><h2>REST + JSON</h2><p>Basit HTTP GET uç noktaları, standart JSON yanıtları.</p></div>
<div class="card"><h2>Şeffaf veri durumu</h2><p>Kaynak ve veri modu API yanıtlarında belirtilir.</p></div>
<div class="card"><h2>Kişisel kullanım</h2><p>İsteğe bağlı gecikmeli veri sağlayıcısı, API anahtarı koruması.</p></div>
<div class="card"><h2>Veri lisansı</h2><p>Açık kaynak kod, üçüncü taraf verisini yeniden dağıtma izni vermez.</p></div></div>
<footer>Demo modu gerçek fiyat üretmez. Harici veri sağlayıcılarının güncelliği ve kullanım koşulları değişebilir. Finansal tavsiye değildir.</footer></main></body></html>"""


@app.get("/v1/health", tags=["Status"])
def health():
    status = market_status()
    configured = provider_mode() in {"yfinance", "borsapy"} and bool(os.getenv("BISTOPENAPI_API_KEY"))
    return {
        "status": "ok",
        "service": "BistOpenAPI",
        "version": "0.2.0",
        "provider": status["name"],
        "data_mode": status["mode"],
        "live_data_available": status["live_data_available"] and configured,
        "market_data_access_protected": status["access_protected"],
        "market_data_configured": configured,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/v1/providers", tags=["Status"])
def providers():
    status = market_status()
    status["catalogue"] = get_provider()
    return status


@app.get("/v1/stocks", tags=["Securities"])
def stocks(q: str | None = None, limit: int = Query(100, ge=1, le=500)):
    catalogue = get_provider()
    rows = catalogue["stocks"]
    if q:
        term = q.strip().upper()
        rows = [r for r in rows if term in r["symbol"].upper() or term in r["name"].upper()]
    return rows[:limit]


@app.get("/v1/stocks/meta", tags=["Securities"])
def stocks_meta():
    catalogue = get_provider()
    return {key: catalogue.get(key) for key in ("name", "mode", "universe", "universe_complete", "notes")}


@app.get("/v1/stocks/{symbol}", tags=["Securities"])
def stock(symbol: str):
    item = next((r for r in stocks() if r["symbol"] == symbol.upper()), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Symbol not found in sample catalogue")
    return item


@app.get("/v1/indexes", tags=["Indexes"])
def indexes(search: str | None = Query(default=None, min_length=1, max_length=40)):
    """List known BIST index codes/names; optional case-insensitive search by code or name."""
    try:
        rows = index_source.get_indexes()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if search:
        term = search.strip().casefold()
        rows = [row for row in rows if term in row["code"].casefold() or term in row["name"].casefold()]
    return rows


@app.get("/v1/indexes/{index_code}", tags=["Indexes"])
def index(index_code: str):
    try:
        return index_source.get_index(index_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Index code not found in catalogue") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def verify_market_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if provider_mode() not in {"yfinance", "borsapy"}:
        raise HTTPException(status_code=503, detail="Market data provider is disabled.")
    expected = os.getenv("BISTOPENAPI_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="Configure BISTOPENAPI_API_KEY in the hosting environment.")
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="A valid X-API-Key header is required.")
    return True


@app.get("/v1/quote/{symbol}", tags=["Market data"])
def quote(symbol: str, _: bool = Depends(verify_market_api_key)):
    try:
        return get_quote(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/v1/quotes", tags=["Market data"])
def quotes(symbols: str = Query(..., description="Comma-separated BIST symbols"), _: bool = Depends(verify_market_api_key)):
    try:
        return get_quotes_batch([s for s in symbols.split(",") if s.strip()])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/ohlcv/{symbol}", tags=["Market data"])
def ohlcv(symbol: str, interval: str = Query("1d"), period: str = Query("1y"), limit: int = Query(30, ge=1, le=500), _: bool = Depends(verify_market_api_key)):
    try:
        return get_ohlcv(symbol, interval, limit, period)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/v1/ohlcv-batch", tags=["Market data"])
def ohlcv_batch(symbols: str = Query(...), interval: str = Query("1d"), period: str = Query("1y"), limit: int = Query(100, ge=1, le=500), _: bool = Depends(verify_market_api_key)):
    try:
        return get_ohlcv_batch([s for s in symbols.split(",") if s.strip()], interval, limit, period)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/fundamentals/{symbol}", tags=["Fundamentals"])
def fundamentals(symbol: str, _: bool = Depends(verify_market_api_key)):
    try:
        return get_fundamentals(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/v1/financials/{symbol}", tags=["Fundamentals"])
def financials(symbol: str, _: bool = Depends(verify_market_api_key)):
    try:
        return get_financials(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/v1/actions/{symbol}", tags=["Corporate actions"])
def actions(symbol: str, _: bool = Depends(verify_market_api_key)):
    try:
        return get_actions(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/v1/news/{symbol}", tags=["News"])
def news(symbol: str, _: bool = Depends(verify_market_api_key)):
    try:
        return get_news(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
