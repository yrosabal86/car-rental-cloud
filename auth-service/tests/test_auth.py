import os
os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"
os.environ["JWT_SECRET"] = "test-secret-key-ci"
os.environ["INTERNAL_API_KEY"] = "test-internal-key-ci"

from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"service": "auth-service", "status": "ok"}


def test_register_and_login_flow():
    with TestClient(app) as client:
        payload = {
            "email": "cliente.hito2@example.com",
            "full_name": "Cliente Prueba Hito2",
            "password": "Password123!",
            "birth_date": "1995-05-15",
            "driver_license": "12345678A",
            "phone": "+34600112233",
        }
        res_reg = client.post("/auth/register", json=payload)
        assert res_reg.status_code in (201, 409)

        res_login = client.post(
            "/auth/login",
            data={"username": "cliente.hito2@example.com", "password": "Password123!"},
        )
        assert res_login.status_code == 200
        data = res_login.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


def test_underage_registration_rejected():
    with TestClient(app) as client:
        payload = {
            "email": "menor.hito2@example.com",
            "full_name": "Menor Edad",
            "password": "Password123!",
            "birth_date": "2012-01-01",
            "driver_license": "99999999Z",
            "phone": "+34600998877",
        }
        res = client.post("/auth/register", json=payload)
        assert res.status_code == 422