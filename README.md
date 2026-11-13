# UptimeX - API Availability & Synthetic Monitoring Platform

UptimeX is an enterprise API availability, latency telemetry, and synthetic uptime monitoring platform. Built with Python 3.11, FastAPI, and SQLite WAL, UptimeX provides continuous SLA tracking, millisecond-accurate TTFB latency measurement, automated incident logging, and a real-time status page.

## Core Capabilities
- **Synthetic HTTP/HTTPS Probes:** Probes target URLs at configurable intervals, capturing response times, HTTP status codes, and network failure reasons.
- **SLA & Availability Engine:** Calculates rolling availability percentages ($\frac{\text{Successful Probes}}{\text{Total Probes}} \times 100\%$) across 30 and 90-day intervals.
- **Automated Incident Lifecycle:** Transitions monitors to `DOWN` upon consecutive probe failures, creating incident tickets and measuring downtime duration upon recovery.
- **Status Page Observatory:** Real-time visual dashboard showcasing 90-day latency bars, current operational status, and outage root-cause summaries.
- **Zero-Trust Event Logging:** Stores all ping attempts and telemetry in SQLite Write-Ahead Logging (WAL) mode.

## Technology Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Pytest
- **Database:** SQLite (WAL mode)
- **Frontend:** Vanilla JavaScript, Modern CSS Flex/Grid, Dark Ops UI
- **DevOps:** Docker, Docker Compose, GitHub Actions CI

## Quickstart

```bash
# Clone the repository
git clone https://github.com/Soulofghost/uptimex.git
cd uptimex

# Install dependencies
pip install -r backend/requirements.txt

# Run test suite
pytest -v

# Run the API server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints
- `GET /api/health` - Service health and synthetic probe engine status.
- `GET /api/stats` - Overall platform metrics (monitors, operational percentage, average latency, active incidents).
- `GET /api/monitors` - List all configured monitors with recent probe history and SLA percentages.
- `POST /api/monitors` - Register a new synthetic HTTP probe monitor.
- `POST /api/monitors/{id}/check` - Trigger an immediate manual health check probe.
- `GET /api/incidents` - List historical and ongoing outage incidents.

## Author
Alvin MS ([@Soulofghost](https://github.com/Soulofghost))
