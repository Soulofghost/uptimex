import pytest
from backend.app.engine.probe_engine import ProbeEngine

def test_http_probe_structure():
    # Probe loopback or invalid address
    probe = ProbeEngine.execute_http_probe("http://127.0.0.1:65432/nonexistent", timeout_s=0.1)
    assert "status_code" in probe
    assert "latency_ms" in probe
    assert "is_up" in probe
    assert probe["is_up"] is False

def test_calculate_uptime_stats_100_percent():
    logs = [
        {"is_up": True, "latency_ms": 45.0},
        {"is_up": True, "latency_ms": 55.0},
        {"is_up": True, "latency_ms": 50.0}
    ]
    stats = ProbeEngine.calculate_uptime_stats(logs)
    assert stats["uptime_pct"] == 100.0
    assert stats["avg_latency_ms"] == 50.0

def test_calculate_uptime_stats_partial():
    logs = [
        {"is_up": True, "latency_ms": 40.0},
        {"is_up": False, "latency_ms": 0.0},
        {"is_up": True, "latency_ms": 60.0},
        {"is_up": True, "latency_ms": 50.0}
    ]
    stats = ProbeEngine.calculate_uptime_stats(logs)
    assert stats["uptime_pct"] == 75.0
    assert stats["avg_latency_ms"] == 50.0
