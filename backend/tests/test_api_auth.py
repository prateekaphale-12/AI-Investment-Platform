"""Register / login / me — integration against real app + SQLite via TestClient."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Isolated SQLite so tests don't fight a dev server's data/app.db (or another test worker)."""
    import app.config as cfg

    monkeypatch.setattr(cfg.settings, "database_path", tmp_path / "auth_test.sqlite")
    monkeypatch.setattr(cfg.settings, "database_url", "")
    # Ensure fresh settings are read by init_db / get_connection.
    from app.main import app

    with TestClient(app) as c:
        yield c


def test_register_login_me_flow(client: TestClient) -> None:
    email = f"user_{uuid.uuid4().hex[:10]}@example.com"
    pw = "password12"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("access_token")
    assert body.get("user", {}).get("email") == email.lower()

    r2 = client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert r2.status_code == 200, r2.text
    token = r2.json()["access_token"]

    bad = client.get("/api/v1/auth/me")
    assert bad.status_code == 401

    r3 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200, r3.text
    assert r3.json()["email"] == email.lower()


def test_register_duplicate_email(client: TestClient) -> None:
    email = f"dup_{uuid.uuid4().hex[:10]}@example.com"
    pw = "password12"
    assert client.post("/api/v1/auth/register", json={"email": email, "password": pw}).status_code == 200
    r2 = client.post("/api/v1/auth/register", json={"email": email, "password": pw})
    assert r2.status_code == 400


def test_login_invalid_credentials(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpass1"},
    )
    assert r.status_code == 401
