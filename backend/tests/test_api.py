import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_healthcheck():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "UptimeX"

def test_stats_endpoint():
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "totalMonitors" in data
    assert "overallAvailability" in data

def test_create_monitor_and_list():
    payload = {
        "name": "Auth Microservice Health",
        "url": "http://127.0.0.1:8000/api/health",
        "interval_seconds": 30,
        "expected_status": 200
    }
    res = client.post("/api/monitors", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Auth Microservice Health"
    m_id = data["id"]

    list_res = client.get("/api/monitors")
    assert list_res.status_code == 200
    assert any(m["id"] == m_id for m in list_res.json())

def test_trigger_manual_check():
    payload = {
        "name": "Payment Gateway Probe",
        "url": "http://127.0.0.1:8000/api/health",
        "interval_seconds": 60
    }
    create_res = client.post("/api/monitors", json=payload)
    m_id = create_res.json()["id"]

    check_res = client.post(f"/api/monitors/{m_id}/check")
    assert check_res.status_code == 200
    c_data = check_res.json()
    assert c_data["monitor_id"] == m_id
    assert "probe" in c_data

def test_incidents_listing():
    res = client.get("/api/incidents")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
