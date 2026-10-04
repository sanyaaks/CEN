import datetime
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.scraping.base import (
    BaseScraper,
    ScraperRateLimitError,
    ScraperBlockedError,
    ScraperTimeoutError
)
from app.scraping.flight_client import (
    FlightClient,
    GoogleFlightsFastScraper,
    CalibratedFallbackScraper
)
from app.scraping.ota_client import OTAPortalScraper
from app.scraping.registry import SourceRegistry, SourceMetadata, registry
from app.scraping.health import SourceHealthTracker, SourceHealthRecord
from app.scraping.validator import IngestionValidator
from app.scraping.raw_store import RawStore
from app.models.db_models import ScrapeRun


# -------------------------------------------------------------
# 1. Scraper Contract & Standard Schema Tests
# -------------------------------------------------------------
def test_scraper_contract_standard_quote_keys():
    scraper = CalibratedFallbackScraper()
    today = datetime.date.today()
    travel_date = today + datetime.timedelta(days=7)
    
    quotes = scraper.search("DEL", "BOM", travel_date)
    assert len(quotes) > 0
    q = quotes[0]

    required_contract_keys = [
        "source", "source_type", "origin", "destination", "travel_date",
        "airline", "total_price", "currency", "observation_type", "fare_decomposition_status"
    ]
    for k in required_contract_keys:
        assert k in q, f"Missing required contract key: {k}"

    assert q["observation_type"] == "ESTIMATED"
    assert q["currency"] == "INR"
    assert q["total_price"] > 0


# -------------------------------------------------------------
# 2. Source Registry Tests
# -------------------------------------------------------------
def test_source_registry_registration_and_priority():
    reg = SourceRegistry()
    
    reg.register(SourceMetadata(
        source_name="source_c",
        source_type="OTA",
        scraper_class=CalibratedFallbackScraper,
        priority=3
    ))
    reg.register(SourceMetadata(
        source_name="source_a",
        source_type="AGGREGATOR",
        scraper_class=CalibratedFallbackScraper,
        priority=1
    ))
    reg.register(SourceMetadata(
        source_name="source_b",
        source_type="BROWSER",
        scraper_class=CalibratedFallbackScraper,
        priority=2
    ))

    sorted_sources = reg.get_enabled_sources_by_priority()
    assert [s.source_name for s in sorted_sources] == ["source_a", "source_b", "source_c"]


# -------------------------------------------------------------
# 3. Ingestion Validator Tests
# -------------------------------------------------------------
def test_ingestion_validator_valid_quote():
    valid_q = {
        "origin": "DEL",
        "destination": "BOM",
        "travel_date": "2026-09-15",
        "airline": "IndiGo",
        "total_price": 5200.0,
        "currency": "INR",
        "observation_type": "OBSERVED"
    }
    is_valid, reason = IngestionValidator.validate_quote(valid_q)
    assert is_valid is True
    assert reason == "VALID_QUOTE"


def test_ingestion_validator_rejects_non_positive_price():
    zero_price_q = {
        "origin": "DEL",
        "destination": "BOM",
        "travel_date": "2026-09-15",
        "airline": "IndiGo",
        "total_price": 0.0,
        "currency": "INR"
    }
    is_valid, reason = IngestionValidator.validate_quote(zero_price_q)
    assert is_valid is False
    assert "NON_POSITIVE_PRICE" in reason


def test_ingestion_validator_rejects_circular_route():
    circular_q = {
        "origin": "DEL",
        "destination": "DEL",
        "travel_date": "2026-09-15",
        "airline": "IndiGo",
        "total_price": 4500.0,
        "currency": "INR"
    }
    is_valid, reason = IngestionValidator.validate_quote(circular_q)
    assert is_valid is False
    assert "CIRCULAR_ROUTE" in reason


def test_ingestion_validator_rejects_missing_airline():
    no_airline_q = {
        "origin": "DEL",
        "destination": "BOM",
        "travel_date": "2026-09-15",
        "airline": "",
        "total_price": 4500.0,
        "currency": "INR"
    }
    is_valid, reason = IngestionValidator.validate_quote(no_airline_q)
    assert is_valid is False
    assert "MISSING_AIRLINE" in reason


# -------------------------------------------------------------
# 4. Source Health Tracking Tests
# -------------------------------------------------------------
def test_source_health_tracker_state_transitions():
    tracker = SourceHealthTracker()
    
    # 1. Successful query
    tracker.record_success("test_source", quote_count=10, response_time_ms=120.0)
    health = tracker.get_source_health("test_source")
    assert health["status"] == "HEALTHY"
    assert health["consecutive_failures"] == 0
    assert health["total_quotes_collected"] == 10

    # 2. Failures degrade status
    tracker.record_failure("test_source", "HTTP 500", response_time_ms=50.0)
    tracker.record_failure("test_source", "HTTP 500", response_time_ms=50.0)
    health_degraded = tracker.get_source_health("test_source")
    assert health_degraded["status"] == "DEGRADED"

    # 3. 5 consecutive failures marks UNAVAILABLE
    tracker.record_failure("test_source", "HTTP 500", response_time_ms=50.0)
    tracker.record_failure("test_source", "HTTP 500", response_time_ms=50.0)
    tracker.record_failure("test_source", "HTTP 500", response_time_ms=50.0)
    health_unavail = tracker.get_source_health("test_source")
    assert health_unavail["status"] == "UNAVAILABLE"


# -------------------------------------------------------------
# 5. Route × Horizon Date Calculation Tests
# -------------------------------------------------------------
def test_route_horizon_date_calculation():
    base_date = datetime.date(2026, 8, 29)
    horizons = [1, 7, 15, 30, 45]
    
    expected_dates = {
        1: datetime.date(2026, 8, 30),
        7: datetime.date(2026, 9, 5),
        15: datetime.date(2026, 9, 13),
        30: datetime.date(2026, 9, 28),
        45: datetime.date(2026, 10, 13)
    }

    for h in horizons:
        calc_date = base_date + datetime.timedelta(days=h)
        assert calc_date == expected_dates[h]


# -------------------------------------------------------------
# 6. Cascade Failover & Provenance Preservation (Mocks)
# -------------------------------------------------------------
def test_flight_client_cascade_failover_to_fallback():
    client = FlightClient(enable_playwright=False)
    today = datetime.date.today()
    travel_date = today + datetime.timedelta(days=7)

    # Mock google flights & ota returning empty to force fallback
    with patch.object(GoogleFlightsFastScraper, "search", return_value=[]), \
         patch.object(OTAPortalScraper, "search", return_value=[]):
        result = client.fetch_flights("DEL", "BOM", travel_date)
        
        assert result["count"] > 0
        assert result["source_used"] == "calibrated_market_model"
        assert result["observation_type"] == "ESTIMATED"
        for q in result["flights"]:
            assert q["observation_type"] == "ESTIMATED"


# -------------------------------------------------------------
# 7. ScrapeRun Database Model Integrity
# -------------------------------------------------------------
def test_scrape_run_model_persistence():
    db: Session = SessionLocal()
    try:
        run = ScrapeRun(
            run_id="test_run_unit_001",
            started_at=datetime.datetime.utcnow(),
            status="SUCCESS",
            attempted=30,
            successful=30,
            records_collected=150,
            records_rejected=0,
            error_count=0,
            duration_seconds=12.5,
            metadata_json={"test": True}
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        assert run.id is not None
        assert run.status == "SUCCESS"
        assert run.duration_seconds == 12.5

        # Cleanup
        db.delete(run)
        db.commit()
    finally:
        db.close()
