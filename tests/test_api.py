from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_marks_demo_mode_by_default(monkeypatch):
    monkeypatch.delenv("BISTOPENAPI_PROVIDER", raising=False)
    monkeypatch.delenv("BISTOPENAPI_API_KEY", raising=False)
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "demo"
    assert body["live_data_available"] is False


def test_sample_stock_search():
    response = client.get("/v1/stocks", params={"q": "thyao"})
    assert response.status_code == 200
    assert [row["symbol"] for row in response.json()] == ["THYAO"]


def test_stock_meta_never_claims_full_coverage():
    response = client.get("/v1/stocks/meta")
    assert response.status_code == 200
    assert response.json()["universe_complete"] is False


def test_market_data_requires_provider():
    response = client.get("/v1/quote/THYAO")
    assert response.status_code == 503


def test_quote_requires_api_key(monkeypatch):
    monkeypatch.setenv("BISTOPENAPI_PROVIDER", "yfinance")
    monkeypatch.setenv("BISTOPENAPI_API_KEY", "test-secret")
    response = client.get("/v1/quote/THYAO")
    assert response.status_code == 401
    response = client.get("/v1/quote/THYAO", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_docs_enabled():
    assert client.get("/docs").status_code == 200
