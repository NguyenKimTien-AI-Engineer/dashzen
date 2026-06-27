"""In-process metrics registry — no external dependencies required.

All counters and gauges are thread-safe via threading.Lock and survive across
requests within the same worker process. For multi-worker deployments, expose
per-worker metrics and aggregate at the scraper layer.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any


class _MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.time()

        # Counters (monotonically increasing)
        self._counters: dict[str, int | float] = defaultdict(int)

        # Gauges (can go up or down)
        self._gauges: dict[str, int | float] = {}

        # Histograms stored as (sum, count, max)
        self._histograms: dict[str, list[float]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Write API
    # ------------------------------------------------------------------

    def inc(self, name: str, value: int | float = 1, **labels: str) -> None:
        key = _label_key(name, labels)
        with self._lock:
            self._counters[key] += value

    def set_gauge(self, name: str, value: int | float, **labels: str) -> None:
        key = _label_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def observe(self, name: str, value: float, **labels: str) -> None:
        key = _label_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            hist_summary: dict[str, Any] = {}
            for key, values in self._histograms.items():
                if values:
                    hist_summary[key] = {
                        "count": len(values),
                        "sum": sum(values),
                        "max": max(values),
                        "p50": _percentile(values, 50),
                        "p95": _percentile(values, 95),
                    }
            return {
                "uptime_seconds": round(time.time() - self._started_at, 1),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": hist_summary,
            }

    def reset(self) -> None:
        """Reset all metrics — useful in tests."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._started_at = time.time()


def _label_key(name: str, labels: dict[str, str]) -> str:
    if not labels:
        return name
    label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    return f"{name}{{{label_str}}}"


def _percentile(data: list[float], p: int) -> float:
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * p / 100)
    idx = min(idx, len(sorted_data) - 1)
    return sorted_data[idx]


# Global singleton — import and use directly
registry = _MetricsRegistry()


# ------------------------------------------------------------------
# Named metric helpers (avoid typos in callers)
# ------------------------------------------------------------------


def record_agent_run(*, status: str, iterations: int, token_total: int) -> None:
    registry.inc("agent_run_total", status=status)
    registry.observe("agent_run_iterations", iterations)
    if token_total > 0:
        registry.inc("agent_token_total", token_total)


def record_tool_call(tool_name: str) -> None:
    registry.inc("tool_call_total", name=tool_name)


def record_compaction(task_id: str) -> None:
    registry.inc("compaction_total")


def record_gate_timeout() -> None:
    registry.inc("gate_timeout_total")


def record_stream_error() -> None:
    registry.inc("stream_error_total")


def record_cleanup_run(*, deleted: int) -> None:
    registry.inc("cleanup_run_total")
    registry.inc("cleanup_deleted_versions_total", deleted)
