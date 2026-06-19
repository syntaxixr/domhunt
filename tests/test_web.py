"""Tests for the FastAPI web layer."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from domhunt.checker import CheckResult, Status
from domhunt.web import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_healthz(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_index_serves_html(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "domhunt" in resp.text.lower()


def test_api_check_rejects_invalid_name(client: TestClient) -> None:
    resp = client.get("/api/check", params={"name": "-bad-"})
    assert resp.status_code == 400


def test_api_check_returns_results(client: TestClient) -> None:
    fake = [
        CheckResult("demo.com", Status.TAKEN),
        CheckResult("demo.io", Status.AVAILABLE),
    ]

    async def fake_check_many(name, tlds, concurrency=10):
        return fake

    with patch("domhunt.web.check_many", side_effect=fake_check_many):
        resp = client.get("/api/check", params={"name": "demo", "tlds": "com,io"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "demo"
    assert len(data["results"]) == 2
    assert data["results"][0]["domain"] == "demo.com"
    assert data["results"][0]["status"] == "taken"
    assert data["results"][1]["status"] == "available"


def test_api_check_rejects_too_many_tlds(client: TestClient) -> None:
    big_list = ",".join(f"t{i}" for i in range(50))
    resp = client.get("/api/check", params={"name": "demo", "tlds": big_list})
    assert resp.status_code == 400


def test_api_check_includes_price_and_buy_url(client: TestClient) -> None:
    fake = [CheckResult("demo.com", Status.AVAILABLE, "", price_usd=10.0, buy_url="x")]

    async def fake_check_many(name, tlds, concurrency=10):
        return fake

    with patch("domhunt.web.check_many", side_effect=fake_check_many):
        resp = client.get("/api/check", params={"name": "demo", "tlds": "com"})

    assert resp.status_code == 200
    row = resp.json()["results"][0]
    assert row["price_usd"] == 10.0
    assert row["buy_url"] == "x"


def test_api_suggest_returns_candidates(client: TestClient) -> None:
    async def fake_check_many(name, tlds, concurrency=10):
        return [CheckResult(f"{name}.{tlds[0]}", Status.AVAILABLE)]

    with patch("domhunt.web.check_many", side_effect=fake_check_many):
        resp = client.get("/api/suggest", params={"name": "demo", "tlds": "com"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "demo"
    assert len(data["candidates"]) > 0
    first = data["candidates"][0]
    assert "name" in first
    assert "results" in first
    assert first["results"][0]["status"] == "available"
