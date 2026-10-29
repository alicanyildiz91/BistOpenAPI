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
- `GET /v1/stocks?q=thyao&limit=20` — current sample catalogue (not a full official stock universe)
- `GET /v1/stocks/{symbol}` — read a sample symbol
- `GET /v1/indexes` — official Borsa İstanbul catalogue for XU030, XU050, XU100 and XU500
- `GET /v1/indexes/{code}` — index constituents sourced through borsapy's external index adapter; validates expected count and fails closed if incomplete
- `GET /v1/quote/{symbol}` — optional quote endpoint (API key required)
- `GET /v1/ohlcv/{symbol}?interval=1d&limit=30` — optional candles (API key required)

## Data provenance

| Data | Current implementation | Limitations |
|---|---|---|
| Official index names/codes | Borsa İstanbul public index pages | The catalogue is limited to XU030, XU050, XU100 and XU500. |
| Index constituents | `borsapy.Index(code).components` | External TradingView/BIST-linked adapter, not a direct licensed BIST reference-data feed. Expected counts (30/50/100/500) are checked; mismatched lists are rejected. A correct count alone cannot prove the upstream list is current. |
| Quote and OHLCV API | `borsapy` | Upstream source varies by endpoint; timestamps and delays are not guaranteed to be exchange timestamps. API `timestamp` means retrieval time, not necessarily trade time. |
| Full listed-stock universe | Not yet implemented in this API; `/v1/stocks` remains a 10-symbol demo catalogue | Borsa İstanbul's daily bulletin documentation points to session-specific bulletin files, and the official market-data products include reference data. The daily bulletin parser or a licensed reference-data feed is required before this endpoint can claim full coverage. |
| Official real-time/delayed/EOD data | Not connected | Borsa İstanbul distributes these through licensed data vendors. A personal-use wrapper does not grant data redistribution rights. |
| Company disclosures | KAP official website is the primary public record | This API does not currently provide a KAP feed. Automated full-feed integration should use the documented MKK/KAP data-dissemination route and comply with access terms. |

## Official sources and next steps

- [Borsa İstanbul data dissemination](https://www.borsaistanbul.com/en/data/data-dissemination)
- [Market data products, including index constituents](https://www.borsaistanbul.com/en/data/data-dissemination/market-data-products)
- [Licensed data vendors directory](https://www.borsaistanbul.com/en/data/data-dissemination/data-vendors-directory)
- [Official BIST equity-market data and daily bulletin information](https://www.borsaistanbul.com/en/data/equity-market-data)
- [Official KAP website](https://www.kap.org.tr/tr)

For a production-quality, complete and permitted data pipeline, request a quote for the exact combination of historical OHLCV, intraday bars, quote delay, index membership/weights, security master and KAP disclosures. Do not describe the service as real-time until per-symbol source timestamps and latency have been measured.

## Optional personal-use provider

The default provider is demo and returns no real prices. To enable the optional `borsapy` adapter, set these Render environment variables:

- `BISTOPENAPI_PROVIDER=borsapy`
- `BISTOPENAPI_API_KEY=<long-random-secret>`

Quote and OHLCV requests require the header `X-API-Key: <same-secret>`. Keep the key private; never commit it to GitHub or expose it in client-side code.

The application code is MIT licensed; that license does not grant rights to third-party market data. Not investment advice.
