# BistOpenAPI

FastAPI service for personal BIST research with interchangeable delayed-data providers.

## Providers

- `yfinance`: unofficial Yahoo Finance client; Turkish tickers are requested with the `.IS` suffix.
- `borsapy`: alternative upstream adapter for quotes, history and index constituents.
- `demo`: default mode; no real market prices.

Provider coverage, delay, history depth, timestamps and fields vary by symbol and upstream. The API does not promise real-time data. Do not redistribute third-party data without the required rights.

## Render deployment

This repository is connected to the existing Render Web Service and deploys from `main`. For uninterrupted availability, keep it on an always-on paid Web Service plan; Render Free web services sleep after inactivity. The Telegram bot remains a separate Background Worker.

Set these environment variables on the API service:

- `BISTOPENAPI_PROVIDER=yfinance`
- `BISTOPENAPI_API_KEY=<long random secret>`
- Optional `BIST_SYMBOLS=THYAO,ASELS,...` for extra symbols.

All market-data endpoints require `X-API-Key`. Keep the key out of GitHub and client-side code. The bot must use the same key.

## Endpoints

- `GET /v1/health` and `GET /v1/providers`
- `GET /v1/stocks` and `GET /v1/stocks/meta`
- `GET /v1/quote/{symbol}` and `GET /v1/quotes?symbols=THYAO,ASELS`
- `GET /v1/ohlcv/{symbol}?interval=1d&period=1y&limit=250`
- `GET /v1/ohlcv-batch?symbols=THYAO,ASELS&interval=1d&period=1y&limit=250`
- `GET /v1/fundamentals/{symbol}`
- `GET /v1/financials/{symbol}`
- `GET /v1/actions/{symbol}`
- `GET /v1/news/{symbol}`
- `GET /v1/indexes` and `GET /v1/indexes/{code}`

Yahoo Finance intraday history has shorter upstream lookback limits than daily history. The API rejects unsupported long-lookback intraday requests.

## Security universe coverage

Automatic catalogue currently uses XU500 constituents from borsapy plus optional `BIST_SYMBOLS` additions. **This is not the full BIST listed-equity universe.** Full coverage needs an up-to-date official/licensed security master or a maintained Borsa İstanbul daily-bulletin parser. The API reports `universe_complete=false` until full coverage is implemented and verified.

## Run locally

Python 3.11+:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
pytest -q
```

The MIT license applies to this code only, not third-party market data. Not investment advice.
