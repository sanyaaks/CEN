import pytest
import datetime
from app.processing.normalize import FareNormalizer
from app.processing.index_engine import IndexEngine
from app.processing.outliers import OutlierDetector
from app.models.db_models import RawFare


def test_normalize_flight_total_price_only_decomposition_unavailable():
    """When raw payload has only total_price (Google Flights case), base_fare & tax remain None and status is UNAVAILABLE."""
    normalizer = FareNormalizer()
    raw = RawFare(
        id=999,
        timestamp=datetime.datetime.utcnow(),
        source="google_flights",
        origin="DEL",
        destination="BOM",
        travel_date=datetime.datetime(2026, 9, 15),
        booking_horizon_days=7,
        raw_payload={},
        payload_hash="dummyhash123"
    )
    flight_dict = {
        "airline": "IndiGo",
        "flight_number": "6E-204",
        "total_price": 5000.0,
    }
    clean = normalizer.normalize_single_flight(raw, flight_dict)
    assert clean.airline == "IndiGo"
    assert clean.total_price == 5000.0
    assert clean.base_fare is None
    assert clean.tax is None
    assert clean.fare_decomposition_status == "UNAVAILABLE"
    assert clean.tax_estimated is True
    assert clean.observation_type == "OBSERVED"
    assert clean.route == "DEL-BOM"
    assert clean.horizon == 7


def test_normalize_flight_with_exact_real_breakdown():
    """When raw payload contains real base_fare and tax fields, use them directly with EXACT status."""
    normalizer = FareNormalizer()
    raw = RawFare(
        id=1000,
        timestamp=datetime.datetime.utcnow(),
        source="airline_api",
        origin="BLR",
        destination="DEL",
        travel_date=datetime.datetime(2026, 10, 1),
        booking_horizon_days=15,
        raw_payload={},
        payload_hash="realhash456"
    )
    flight_dict = {
        "airline": "Vistara",
        "flight_number": "UK-805",
        "total_price": 6000.0,
        "base_fare": 4800.0,
        "tax": 1200.0,
        "gst": 240.0,
        "observation_type": "OBSERVED"
    }
    clean = normalizer.normalize_single_flight(raw, flight_dict)
    assert clean.total_price == 6000.0
    assert clean.base_fare == 4800.0
    assert clean.tax == 1200.0
    assert clean.gst == 240.0
    assert clean.fare_decomposition_status == "EXACT"
    assert clean.tax_estimated is False
    assert clean.observation_type == "OBSERVED"


def test_dutot_calculation():
    engine = IndexEngine()
    current_fares = [4800.0, 5280.0, 5760.0]  # Mean: 5280.0
    base_fare = 4800.0
    dutot = engine.calculate_dutot(current_fares, base_fare)
    assert round(dutot, 1) == 110.0


def test_jevons_calculation():
    engine = IndexEngine()
    current_fares = [4800.0, 5280.0, 5760.0]
    base_fare = 4800.0
    jevons = engine.calculate_jevons(current_fares, base_fare)
    assert jevons > 0
