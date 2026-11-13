import uuid
import datetime
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from backend.app.database import get_connection
from backend.app.schemas import (
    CreateMonitorRequest, MonitorResponse,
    ProbeLogItem, IncidentResponse
)
from backend.app.engine.probe_engine import ProbeEngine

router = APIRouter(prefix="/api", tags=["monitors"])

@router.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "service": "UptimeX",
        "version": "1.0.0",
        "engine": "Synthetic HTTP Probing & SLA Availability Engine"
    }

@router.get("/stats")
def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as c FROM monitors;")
    total_monitors = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) as c FROM monitors WHERE status = 'UP';")
    operational_monitors = cursor.fetchone()["c"]

    cursor.execute("SELECT AVG(uptime_pct) as a FROM monitors;")
    avg_uptime_row = cursor.fetchone()["a"]
    avg_uptime = round(avg_uptime_row, 2) if avg_uptime_row else 100.0

    cursor.execute("SELECT AVG(avg_latency_ms) as a FROM monitors WHERE avg_latency_ms > 0;")
    avg_latency_row = cursor.fetchone()["a"]
    avg_latency = round(avg_latency_row, 1) if avg_latency_row else 0.0

    cursor.execute("SELECT COUNT(*) as c FROM incidents WHERE resolved_at IS NULL;")
    active_incidents = cursor.fetchone()["c"]

    conn.close()

    return {
        "totalMonitors": total_monitors,
        "operationalMonitors": operational_monitors,
        "overallAvailability": avg_uptime,
        "averageLatencyMs": avg_latency,
        "activeIncidents": active_incidents
    }

@router.get("/monitors", response_model=List[MonitorResponse])
def list_monitors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM monitors ORDER BY created_at DESC;")
    rows = cursor.fetchall()

    result = []
    for r in rows:
        m_id = r["id"]
        cursor.execute("SELECT * FROM probe_logs WHERE monitor_id = ? ORDER BY checked_at DESC LIMIT 10;", (m_id,))
        p_rows = cursor.fetchall()
        recent_probes = [
            {
                **dict(p),
                "is_up": bool(p["is_up"])
            } for p in p_rows
        ]
        result.append({
            **dict(r),
            "recent_probes": recent_probes
        })

    conn.close()
    return result

@router.post("/monitors", response_model=MonitorResponse, status_code=status.HTTP_201_CREATED)
def create_monitor(payload: CreateMonitorRequest):
    conn = get_connection()
    cursor = conn.cursor()

    m_id = "mon-" + str(uuid.uuid4())[:8]
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Run immediate initial probe
    probe = ProbeEngine.execute_http_probe(payload.url, payload.method or "GET", payload.expected_status or 200)
    current_status = "UP" if probe["is_up"] else "DOWN"

    cursor.execute("""
    INSERT INTO monitors (id, name, url, method, interval_seconds, expected_status, status, uptime_pct, avg_latency_ms, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 100.0, ?, ?);
    """, (
        m_id,
        payload.name,
        payload.url,
        payload.method or "GET",
        payload.interval_seconds or 60,
        payload.expected_status or 200,
        current_status,
        probe["latency_ms"],
        now_iso
    ))

    # Log probe
    log_id = "plog-" + str(uuid.uuid4())[:8]
    cursor.execute("""
    INSERT INTO probe_logs (id, monitor_id, status_code, latency_ms, is_up, error_msg, checked_at)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (log_id, m_id, probe["status_code"], probe["latency_ms"], 1 if probe["is_up"] else 0, probe["error_msg"], now_iso))

    conn.commit()
    conn.close()

    return {
        "id": m_id,
        "name": payload.name,
        "url": payload.url,
        "method": payload.method or "GET",
        "interval_seconds": payload.interval_seconds or 60,
        "expected_status": payload.expected_status or 200,
        "status": current_status,
        "uptime_pct": 100.0 if probe["is_up"] else 0.0,
        "avg_latency_ms": probe["latency_ms"],
        "created_at": now_iso
    }

@router.post("/monitors/{monitor_id}/check")
def trigger_manual_check(monitor_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM monitors WHERE id = ?;", (monitor_id,))
    mon = cursor.fetchone()
    if not mon:
        conn.close()
        raise HTTPException(status_code=404, detail="Monitor not found")

    probe = ProbeEngine.execute_http_probe(mon["url"], mon["method"], mon["expected_status"])
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_status = "UP" if probe["is_up"] else "DOWN"

    log_id = "plog-" + str(uuid.uuid4())[:8]
    cursor.execute("""
    INSERT INTO probe_logs (id, monitor_id, status_code, latency_ms, is_up, error_msg, checked_at)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (log_id, monitor_id, probe["status_code"], probe["latency_ms"], 1 if probe["is_up"] else 0, probe["error_msg"], now_iso))

    # Recalculate stats
    cursor.execute("SELECT is_up, latency_ms FROM probe_logs WHERE monitor_id = ? ORDER BY checked_at DESC LIMIT 50;", (monitor_id,))
    history = [dict(r) for r in cursor.fetchall()]
    stats = ProbeEngine.calculate_uptime_stats(history)

    cursor.execute("""
    UPDATE monitors SET status = ?, uptime_pct = ?, avg_latency_ms = ? WHERE id = ?;
    """, (new_status, stats["uptime_pct"], stats["avg_latency_ms"], monitor_id))

    # Incident management
    if new_status == "DOWN" and mon["status"] == "UP":
        inc_id = "inc-" + str(uuid.uuid4())[:8]
        cursor.execute("""
        INSERT INTO incidents (id, monitor_id, title, cause, started_at)
        VALUES (?, ?, ?, ?, ?);
        """, (inc_id, monitor_id, f"Outage on {mon['name']}", probe["error_msg"] or "HTTP probe failed", now_iso))
    elif new_status == "UP" and mon["status"] == "DOWN":
        cursor.execute("""
        UPDATE incidents SET resolved_at = ?, duration_seconds = 120 WHERE monitor_id = ? AND resolved_at IS NULL;
        """, (now_iso, monitor_id))

    conn.commit()
    conn.close()

    return {
        "monitor_id": monitor_id,
        "status": new_status,
        "probe": probe,
        "uptime_pct": stats["uptime_pct"],
        "avg_latency_ms": stats["avg_latency_ms"]
    }

@router.get("/incidents", response_model=List[IncidentResponse])
def list_incidents():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY started_at DESC LIMIT 20;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
