import os

os.environ["DATABASE_URL"] = "sqlite:///./test_rental.db"
os.environ["JWT_SECRET"] = "test-secret-key-ci"
os.environ["INTERNAL_API_KEY"] = "test-internal-key-ci"
os.environ["SEED_DEMO_DATA"] = "false"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"service": "rental-service", "status": "ok"}


def test_openapi_schema_available():
    res = client.get("/openapi.json")
    assert res.status_code == 200
    assert "paths" in res.json()


def test_unauthenticated_reservation_rejected():
    res = client.post(
        "/reservations",
        json={"category": "compact", "start_date": "2026-12-01", "end_date": "2026-12-05"},
    )
    assert res.status_code in (401, 403)
