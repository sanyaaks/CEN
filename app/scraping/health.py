import logging
import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SourceHealthRecord:
    source_name: str
    status: str = "HEALTHY"  # HEALTHY, DEGRADED, UNAVAILABLE, DISABLED
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    consecutive_failures: int = 0
    total_queries: int = 0
    successful_queries: int = 0
    total_quotes_collected: int = 0
    last_error: Optional[str] = None
    last_response_time_ms: float = 0.0


class SourceHealthTracker:
    """
    Monitors operational health, error rates, and response latency of scrapers.
    Never fabricates metrics; updates deterministically upon live query outcomes.
    """

    def __init__(self):
        self._health_map: Dict[str, SourceHealthRecord] = {}

    def get_or_create(self, source_name: str) -> SourceHealthRecord:
        if source_name not in self._health_map:
            self._health_map[source_name] = SourceHealthRecord(source_name=source_name)
        return self._health_map[source_name]

    def record_success(self, source_name: str, quote_count: int, response_time_ms: float = 0.0):
        rec = self.get_or_create(source_name)
        rec.total_queries += 1
        rec.successful_queries += 1
        rec.total_quotes_collected += quote_count
        rec.consecutive_failures = 0
        rec.last_success = datetime.datetime.utcnow().isoformat()
        rec.last_response_time_ms = round(response_time_ms, 2)
        rec.status = "HEALTHY"

    def record_failure(self, source_name: str, error_message: str, response_time_ms: float = 0.0):
        rec = self.get_or_create(source_name)
        rec.total_queries += 1
        rec.consecutive_failures += 1
        rec.last_failure = datetime.datetime.utcnow().isoformat()
        rec.last_error = error_message
        rec.last_response_time_ms = round(response_time_ms, 2)

        if rec.consecutive_failures >= 5:
            rec.status = "UNAVAILABLE"
        elif rec.consecutive_failures >= 2:
            rec.status = "DEGRADED"

        logger.warning(f"Source '{source_name}' failure recorded ({rec.status}, failures={rec.consecutive_failures}): {error_message}")

    def get_source_health(self, source_name: str) -> Dict[str, Any]:
        return asdict(self.get_or_create(source_name))

    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        return {name: asdict(rec) for name, rec in self._health_map.items()}


# Global Health Monitor
health_tracker = SourceHealthTracker()
