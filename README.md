# BistOpenAPI

Open-source Turkish stock-market API built with Python and FastAPI. The project is designed around interchangeable data providers, public API documentation and transparent data-source metadata.

> **Important:** This initial version is a scaffold, not a live BIST feed. The demo provider exposes a small example symbol catalogue only. Quote and OHLCV endpoints intentionally return 404 rather than fabricate market prices. Index constituents are not yet populated.

## Features
- FastAPI REST API with Swagger UI at `/docs` and ReDoc at `/redoc`
- Health/status endpoint clearly identifies demo mode and live-data availability
- Searchable sample symbols and sample index names
- Render deployment blueprint and automated tests
- No API key required for the initial public development version

## Run locally

Requires Python 3.11+ (Python 3.12 recommended).

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:
- Home: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/v1/health
- Sample stocks: http://127.0.0.1:8000/v1/stocks
- Sample indexes: http://127.0.0.1:8000/v1/indexes

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/v1/health` | Service and provider status |
| GET | `/v1/providers` | Active provider and limitations |
| GET | `/v1/stocks?q=thyao&limit=20` | Search the configured sample universe |
| GET | `/v1/stocks/{symbol}` | Read one sample symbol |
| GET | `/v1/indexes` | List configured index metadata |
| GET | `/v1/indexes/{index_code}` | Read one index |
| GET | `/v1/quote/{symbol}` | Latest quote (404 until a provider is configured) |
| GET | `/v1/ohlcv/{symbol}?interval=1d&limit=30` | Candles (404 until a provider is configured) |

## Deploy to Render
1. Push this project to GitHub.
2. In Render, choose **New + → Blueprint** and connect this repository.
3. Render reads `render.yaml` and creates the web service.
4. After deployment, open `https://YOUR-SERVICE.onrender.com/docs`.

Free services may sleep after inactivity, so this is suitable for an initial demo, not a guaranteed always-on low-latency feed.

## Data and licensing
Implement a provider adapter before returning real prices. The source must explicitly permit intended server-side access and public redistribution. Public access to a webpage or an open-source Python package does not by itself grant rights to republish live market data. Review Borsa İstanbul market-data licensing and each provider's terms.

## Roadmap
- [x] Public FastAPI scaffold and API documentation
- [x] Render blueprint and tests
- [ ] Verify allowed market-data providers and redistribution terms
- [ ] Add a validated historical/delayed provider
- [ ] Add live data only if a permitted source exists
- [ ] Populate and validate official index constituents
- [ ] Add status page with last successful fetch and data freshness
- [ ] Add rate limiting before heavy public usage

## License
Application code: MIT. This license does not grant rights to third-party market data, logos or external content.

## Disclaimer
For software development and informational purposes only; not investment advice. Data coverage, timestamps and delays depend on the configured provider.
