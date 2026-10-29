from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_marks_demo_mode():
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["live_data_available"] is False

def test_sample_stock_search():
    response = client.get("/v1/stocks", params={"q": "thyao"})
    assert response.status_code == 200
    assert [row["symbol"] for row in response.json()] == ["THYAO"]

def test_indexes_are_marked_demo():
    response = client.get("/v1/indexes")
    assert response.status_code == 200
    assert all(row["data_mode"] == "demo" for row in response.json())
    assert all(not row["constituents"] for row in response.json())

def test_no_fake_quote():
    response = client.get("/v1/quote/THYAO")
    assert response.status_code == 404

def test_docs_enabled():
    assert client.get("/docs").status_code == 200
