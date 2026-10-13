"""
Tests for the FastAPI backend (backend/api.py).

Uses FastAPI's TestClient (built on httpx) to make real HTTP calls
against the app without needing a running server.

Network calls and file I/O are mocked so tests are fast and isolated.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


# ---------- helpers ----------

def mock_check_up(url):
    return 200, "UP", 123.45, None


def mock_check_down_timeout(url):
    return None, "DOWN", None, "Request timed out."


def mock_check_down_ssl(url):
    return None, "DOWN", None, "SSL certificate error."


SAMPLE_HISTORY = [
    {
        "url": "https://example.com",
        "checked_at": "2026-10-13 09:00:00",
        "uptime_status": "UP",
        "status_code": 200,
        "response_time_ms": 123.45,
    },
    {
        "url": "https://example.com",
        "checked_at": "2026-10-13 09:05:00",
        "uptime_status": "DOWN",
        "status_code": None,
        "response_time_ms": None,
    },
    {
        "url": "https://other.com",
        "checked_at": "2026-10-13 09:10:00",
        "uptime_status": "UP",
        "status_code": 200,
        "response_time_ms": 88.0,
    },
]


# ---------- GET / ----------

class TestRoot:
    def test_returns_ok(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# ---------- POST /check ----------

class TestCheck:

    def test_successful_check_returns_up(self):
        with patch("api.check_website", side_effect=mock_check_up), \
             patch("api.save_history"):
            response = client.post("/check", json={"url": "https://example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"
        assert data["status_code"] == 200
        assert data["response_time_ms"] == 123.45
        assert data["error"] is None
        assert data["url"] == "https://example.com"
        assert "checked_at" in data

    def test_timeout_returns_down_with_error(self):
        with patch("api.check_website", side_effect=mock_check_down_timeout), \
             patch("api.save_history"):
            response = client.post("/check", json={"url": "https://example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DOWN"
        assert data["status_code"] is None
        assert data["response_time_ms"] is None
        assert "timed out" in data["error"].lower()

    def test_ssl_error_returns_down(self):
        with patch("api.check_website", side_effect=mock_check_down_ssl), \
             patch("api.save_history"):
            response = client.post("/check", json={"url": "https://example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DOWN"
        assert "ssl" in data["error"].lower()

    def test_empty_url_returns_422(self):
        response = client.post("/check", json={"url": ""})
        assert response.status_code == 422

    def test_localhost_returns_422(self):
        response = client.post("/check", json={"url": "http://localhost"})
        assert response.status_code == 422
        assert "localhost" in response.json()["detail"].lower()

    def test_private_ip_returns_422(self):
        with patch("main.is_private_ip", return_value=True):
            response = client.post("/check", json={"url": "http://192.168.1.1"})
        assert response.status_code == 422

    def test_url_auto_adds_https(self):
        with patch("api.check_website", side_effect=mock_check_up), \
             patch("api.save_history"):
            response = client.post("/check", json={"url": "example.com"})
        assert response.status_code == 200
        assert response.json()["url"].startswith("https://")

    def test_missing_url_field_returns_422(self):
        response = client.post("/check", json={})
        assert response.status_code == 422


# ---------- GET /history ----------

class TestHistory:

    def test_returns_all_records(self):
        with patch("api.load_history", return_value=SAMPLE_HISTORY):
            response = client.get("/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["status"] == "UP"

    def test_filter_by_url(self):
        with patch("api.load_history", return_value=SAMPLE_HISTORY):
            response = client.get("/history?url=other")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "other.com" in data[0]["url"]

    def test_filter_by_status_down(self):
        with patch("api.load_history", return_value=SAMPLE_HISTORY):
            response = client.get("/history?status=DOWN")
        assert response.status_code == 200
        data = response.json()
        assert all(r["status"] == "DOWN" for r in data)

    def test_limit_parameter(self):
        with patch("api.load_history", return_value=SAMPLE_HISTORY):
            response = client.get("/history?limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_empty_history_returns_empty_list(self):
        with patch("api.load_history", return_value=[]):
            response = client.get("/history")
        assert response.status_code == 200
        assert response.json() == []

    def test_invalid_status_returns_422(self):
        response = client.get("/history?status=UNKNOWN")
        assert response.status_code == 422

    def test_invalid_limit_returns_422(self):
        response = client.get("/history?limit=0")
        assert response.status_code == 422

    def test_each_record_has_required_fields(self):
        with patch("api.load_history", return_value=SAMPLE_HISTORY):
            response = client.get("/history")
        data = response.json()
        for record in data:
            assert "url" in record
            assert "checked_at" in record
            assert "status" in record
            assert "status_code" in record
            assert "response_time_ms" in record


# ---------- GET /stats ----------

class TestStats:

    def test_calculates_uptime_percent(self):
        with patch("api.load_history", return_value=SAMPLE_HISTORY):
            response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        # 2 UP out of 3 total = 66.67%
        assert data["total_checks"] == 3
        assert data["up_count"] == 2
        assert data["down_count"] == 1
        assert data["uptime_percent"] == pytest.approx(66.67, abs=0.01)

    def test_average_response_excludes_nulls(self):
        with patch("api.load_history", return_value=SAMPLE_HISTORY):
            response = client.get("/stats")
        data = response.json()
        # Only two records have response times: 123.45 and 88.0
        expected_avg = round((123.45 + 88.0) / 2, 2)
        assert data["average_response_ms"] == pytest.approx(expected_avg, abs=0.01)

    def test_filter_stats_by_url(self):
        with patch("api.load_history", return_value=SAMPLE_HISTORY):
            response = client.get("/stats?url=example")
        data = response.json()
        # example.com has 2 records: 1 UP, 1 DOWN
        assert data["total_checks"] == 2
        assert data["up_count"] == 1
        assert data["uptime_percent"] == 50.0

    def test_empty_history_returns_zero_stats(self):
        with patch("api.load_history", return_value=[]):
            response = client.get("/stats")
        data = response.json()
        assert data["total_checks"] == 0
        assert data["uptime_percent"] == 0.0
        assert data["average_response_ms"] is None
        assert data["last_checked"] is None

    def test_last_checked_is_most_recent(self):
        with patch("api.load_history", return_value=SAMPLE_HISTORY):
            response = client.get("/stats")
        data = response.json()
        assert data["last_checked"] == "2026-10-13 09:10:00"
