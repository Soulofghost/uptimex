from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CreateMonitorRequest(BaseModel):
    name: str = Field(..., description="Monitor name, e.g. Core API Gateway")
    url: str = Field(..., description="Target HTTP/HTTPS URL, e.g. https://api.service.io/health")
    method: Optional[str] = Field(default="GET")
    interval_seconds: Optional[int] = Field(default=60, ge=10)
    expected_status: Optional[int] = Field(default=200)

class ProbeLogItem(BaseModel):
    id: str
    monitor_id: str
    status_code: int
    latency_ms: float
    is_up: bool
    error_msg: Optional[str]
    checked_at: str

class IncidentResponse(BaseModel):
    id: str
    monitor_id: str
    title: str
    cause: str
    started_at: str
    resolved_at: Optional[str]
    duration_seconds: Optional[int]

class MonitorResponse(BaseModel):
    id: str
    name: str
    url: str
    method: str
    interval_seconds: int
    expected_status: int
    status: str
    uptime_pct: float
    avg_latency_ms: float
    created_at: str
    recent_probes: Optional[List[ProbeLogItem]] = None
