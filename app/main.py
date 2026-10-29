from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.providers import get_provider

app = FastAPI(
    title="BistOpenAPI",
    version="0.1.0",
    description=(
        "Open-source Turkish stock-market API scaffold. "
        "The default demo provider does not return real market prices."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return """<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BistOpenAPI — Açık BIST API</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#131b2f;--muted:#9aa8c7;--text:#edf2ff;--accent:#76e0b5;--line:#25314b}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top right,#172b3b 0,#0b1020 48%);font:16px/1.6 system-ui,sans-serif;color:var(--text)}
main{max-width:1050px;margin:auto;padding:30px 22px 70px}.nav{display:flex;justify-content:space-between;align-items:center;margin-bottom:75px}.brand{font-weight:800}.tag{color:var(--accent);border:1px solid #2e6557;padding:4px 10px;border-radius:99px;font-size:12px}
h1{font-size:clamp(2.6rem,7vw,5rem);line-height:1.02;letter-spacing:-.05em;margin:12px 0 22px;max-width:800px}.accent{color:var(--accent)}p{color:var(--muted);max-width:700px}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin:30px 0 55px}a.btn{display:inline-block;background:var(--accent);color:#081611;text-decoration:none;padding:11px 17px;border-radius:10px;font-weight:750}a.secondary{background:var(--panel);border:1px solid var(--line);color:var(--text)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.card{background:#111a2b;border:1px solid var(--line);padding:20px;border-radius:16px}.card h2{margin:0 0 6px;font-size:1.08rem}.card p{font-size:.92rem;margin:0}.endpoint{margin-top:32px;background:#080d18;border:1px solid var(--line);border-radius:16px;overflow:hidden}.endpoint header{padding:12px 16px;border-bottom:1px solid var(--line);color:var(--muted)}pre{padding:18px;overflow:auto;color:#c5f6df;margin:0;font-size:.92rem}footer{margin-top:45px;border-top:1px solid var(--line);padding-top:22px;color:var(--muted);font-size:.86rem}
</style></head><body><main>
<div class="nav"><div class="brand">◈ BistOpenAPI</div><span class="tag">OPEN SOURCE · V0.1</span></div>
<p>Türkiye hisse piyasası için geliştirilen açık kaynak API projesi</p>
<h1>Piyasa verisine <span class="accent">açık erişim.</span></h1>
<p>Geliştiriciler için sade bir REST API, otomatik dokümantasyon ve değiştirilebilir veri sağlayıcıları. Kaynak ve veri güncelliği her zaman açıkça belirtilir.</p>
<div class="actions"><a class="btn" href="/docs">API dokümantasyonu ↗</a><a class="btn secondary" href="https://github.com/alicanyildiz91/BistOpenAPI">GitHub kaynak kodu ↗</a></div>
<div class="grid">
<div class="card"><h2>REST + JSON</h2><p>Basit HTTP GET uç noktaları, standart JSON yanıtları.</p></div>
<div class="card"><h2>Şeffaf veri durumu</h2><p>Kaynak, zaman damgası ve veri gecikmesi bilgileri.</p></div>
<div class="card"><h2>Takılabilir kaynaklar</h2><p>Veri sağlayıcısını API yüzeyini değiştirmeden değiştirmek üzere tasarlanır.</p></div>
<div class="card"><h2>Ücretsiz ve açık kaynak</h2><p>Kod açık lisanslıdır; piyasa verisi lisansları ayrıca geçerlidir.</p></div>
</div>
<div class="endpoint"><header>Örnek · servis durumu</header><pre>GET /v1/health

{
  "status": "ok",
  "provider": "demo",
  "data_mode": "demo",
  "live_data_available": false
}</pre></div>
<footer>Demo sürümü gerçek fiyat üretmez. Canlı veya yeniden dağıtılan piyasa verileri ilgili sağlayıcının lisans koşullarına tabidir. Finansal tavsiye değildir.</footer>
</main></body></html>"""

@app.get("/v1/health", tags=["Status"])
def health():
    provider = get_provider()
    return {
        "status": "ok",
        "service": "BistOpenAPI",
        "version": "0.1.0",
        "provider": provider["name"],
        "data_mode": provider["mode"],
        "live_data_available": provider["live_data_available"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/v1/providers", tags=["Status"])
def providers():
    return get_provider()

@app.get("/v1/stocks", tags=["Securities"])
def stocks(q: str | None = None, limit: int = Query(100, ge=1, le=500)):
    provider = get_provider()
    rows = provider["stocks"]
    if q:
        term = q.strip().upper()
        rows = [r for r in rows if term in r["symbol"].upper() or term in r["name"].upper()]
    return rows[:limit]

@app.get("/v1/stocks/{symbol}", tags=["Securities"])
def stock(symbol: str):
    item = next((r for r in stocks() if r["symbol"] == symbol.upper()), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Symbol not found in sample catalogue")
    return item

@app.get("/v1/indexes", tags=["Indexes"])
def indexes():
    return get_provider()["indexes"]

@app.get("/v1/indexes/{index_code}", tags=["Indexes"])
def index(index_code: str):
    item = next((r for r in indexes() if r["code"] == index_code.upper()), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Index not found")
    return item

@app.get("/v1/quote/{symbol}", tags=["Market data"])
def quote(symbol: str):
    raise HTTPException(
        status_code=404,
        detail="No quote provider is configured. This API does not invent market prices.",
    )

@app.get("/v1/ohlcv/{symbol}", tags=["Market data"])
def ohlcv(
    symbol: str,
    interval: str = Query("1d", pattern="^(1d|1wk|1mo)$"),
    limit: int = Query(30, ge=1, le=500),
):
    raise HTTPException(
        status_code=404,
        detail="No OHLCV provider is configured. No synthetic candles are returned.",
    )
