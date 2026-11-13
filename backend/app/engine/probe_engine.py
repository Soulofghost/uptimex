import time
import urllib.request
import urllib.error
from typing import Dict, Any, List

class ProbeEngine:
    @staticmethod
    def execute_http_probe(url: str, method: str = "GET", expected_status: int = 200, timeout_s: float = 3.0) -> Dict[str, Any]:
        """
        Executes a real or loopback HTTP probe and measures duration.
        """
        start = time.perf_counter()
        status_code = 0
        error_msg = None
        is_up = False

        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "UptimeX-SyntheticProbe/1.0"})
            with urllib.request.urlopen(req, timeout=timeout_s) as response:
                status_code = response.getcode()
                is_up = (status_code == expected_status) or (200 <= status_code < 400 and expected_status == 200)
        except urllib.error.HTTPError as e:
            status_code = e.code
            is_up = (status_code == expected_status)
            if not is_up:
                error_msg = f"HTTP Error: {e.code} {e.reason}"
        except urllib.error.URLError as e:
            status_code = 0
            is_up = False
            error_msg = f"Connection Failed: {e.reason}"
        except Exception as e:
            status_code = 0
            is_up = False
            error_msg = str(e)

        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        return {
            "status_code": status_code,
            "latency_ms": latency_ms,
            "is_up": is_up,
            "error_msg": error_msg or ""
        }

    @staticmethod
    def calculate_uptime_stats(logs: List[Dict[str, Any]]) -> Dict[str, float]:
        if not logs:
            return {"uptime_pct": 100.0, "avg_latency_ms": 0.0}

        total = len(logs)
        up_count = sum(1 for l in logs if l.get("is_up"))
        uptime_pct = round((up_count / total) * 100.0, 2)

        latencies = [l.get("latency_ms", 0.0) for l in logs if l.get("is_up")]
        avg_lat = round(sum(latencies) / len(latencies), 1) if latencies else 0.0

        return {
            "uptime_pct": uptime_pct,
            "avg_latency_ms": avg_lat
        }
