# BistOpenAPI

Open-source Turkish stock-market API built with Python and FastAPI. Designed for personal BIST analysis bots with interchangeable data providers.

> The default mode is demo and does not return real market prices. A third-party Python package does not itself grant permission to redistribute its underlying market data.

## Run locally
Requires Python 3.11+ (Python 3.12 recommended).

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API endpoints
- `GET /v1/health` — service and provider status
- `GET /v1/providers` — active provider and limitations
- `GET /v1/stocks?q=thyao&limit=20` — search sample symbols
- `GET /v1/stocks/{symbol}` — read sample symbol
- `GET /v1/indexes` — sample index metadata
- `GET /v1/quote/{symbol}` — optional quote endpoint (API key required)
- `GET /v1/ohlcv/{symbol}?interval=1d&limit=30` — optional candles (API key required)

## Optional personal-use provider
The default provider is demo and returns no real prices. To enable the optional `borsapy` adapter, set these Render environment variables:
- `BISTOPENAPI_PROVIDER=borsapy`
- `BISTOPENAPI_API_KEY=<long-random-secret>`

Quote and OHLCV requests require the header `X-API-Key: <same-secret>`. Keep the key private; never commit it to GitHub or expose it in client-side code.

This adapter is intended for personal/educational use. Data availability, delays and upstream terms may change. Enabling the adapter does not grant redistribution rights. Review current package terms and Borsa İstanbul data licensing before sharing data beyond personal analysis.

The application code is MIT licensed; that license does not grant rights to third-party market data. Not investment advice.
