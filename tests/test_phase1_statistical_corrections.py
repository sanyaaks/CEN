import math
import datetime
import pytest
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.db_models import CleanFare, RawFare, IndexValue
from app.processing.index_engine import IndexEngine, PROTOTYPE_ROUTE_WEIGHTS
from app.processing.normalize import FareNormalizer
from app.config import settings


# -------------------------------------------------------------
# 1. OBSERVED vs ESTIMATED Data Tests
# -------------------------------------------------------------
def test_observation_type_separation():
    engine = IndexEngine()
    
    # Create sample fares with mixed observation types
    f1 = CleanFare(
        route="DEL-BOM",
        date=datetime.datetime(2026, 8, 29),
        horizon=7,
        airline="IndiGo",
        total_price=5000.0,
        observation_type="OBSERVED",
        is_outlier=False,
        cleaned_at=datetime.datetime(2026, 8, 29)
    )
    f2 = CleanFare(
        route="DEL-BOM",
        date=datetime.datetime(2026, 8, 29),
        horizon=7,
        airline="Air India",
        total_price=6000.0,
        observation_type="OBSERVED",
        is_outlier=False,
        cleaned_at=datetime.datetime(2026, 8, 29)
    )
    f_est = CleanFare(
        route="DEL-BOM",
        date=datetime.datetime(2026, 8, 29),
        horizon=7,
        airline="ModelCarrier",
        total_price=5500.0,
        observation_type="ESTIMATED",
        is_outlier=False,
        cleaned_at=datetime.datetime(2026, 8, 29)
    )

    all_fares = [f1, f2, f_est]
    coverage = engine.calculate_coverage(all_fares)
    assert coverage["total_count"] == 3
    assert coverage["observed_count"] == 2
    assert coverage["estimated_count"] == 1
    assert round(coverage["coverage_percent"], 2) == 66.67


def test_coverage_empty_dataset():
    engine = IndexEngine()
    cov = engine.calculate_coverage([])
    assert cov["total_count"] == 0
    assert cov["coverage_percent"] == 100.0


# -------------------------------------------------------------
# 2. Fare Decomposition Status Tests
# -------------------------------------------------------------
def test_fare_decomposition_unavailable_when_only_total_provided():
    normalizer = FareNormalizer()
    raw = RawFare(
        id=888,
        source="google_flights",
        origin="DEL",
        destination="BOM",
        travel_date=datetime.datetime(2026, 9, 1),
        booking_horizon_days=1,
        raw_payload={},
        payload_hash="testhash888"
    )
    flight = {"airline": "SpiceJet", "total_price": 4500.0}
    clean = normalizer.normalize_single_flight(raw, flight)

    assert clean.total_price == 4500.0
    assert clean.base_fare is None
    assert clean.tax is None
    assert clean.fare_decomposition_status == "UNAVAILABLE"
    assert clean.tax_estimated is True
    assert clean.observation_type == "OBSERVED"


def test_fare_decomposition_exact_when_components_provided():
    normalizer = FareNormalizer()
    raw = RawFare(
        id=889,
        source="ota_direct",
        origin="BLR",
        destination="DEL",
        travel_date=datetime.datetime(2026, 9, 1),
        booking_horizon_days=7,
        raw_payload={},
        payload_hash="testhash889"
    )
    flight = {
        "airline": "Air India",
        "total_price": 5500.0,
        "base_fare": 4700.0,
        "tax": 800.0,
        "gst": 235.0,
        "airport_charges": 565.0,
        "observation_type": "OBSERVED"
    }
    clean = normalizer.normalize_single_flight(raw, flight)

    assert clean.total_price == 5500.0
    assert clean.base_fare == 4700.0
    assert clean.tax == 800.0
    assert clean.gst == 235.0
    assert clean.airport_charges == 565.0
    assert clean.fare_decomposition_status == "EXACT"
    assert clean.tax_estimated is False


def test_fare_decomposition_partial_when_some_components_provided():
    normalizer = FareNormalizer()
    raw = RawFare(
        id=890,
        source="ota_direct",
        origin="HYD",
        destination="MAA",
        travel_date=datetime.datetime(2026, 9, 1),
        booking_horizon_days=15,
        raw_payload={},
        payload_hash="testhash890"
    )
    flight = {
        "airline": "IndiGo",
        "total_price": 4000.0,
        "base_fare": 3400.0,
        # tax is missing
    }
    clean = normalizer.normalize_single_flight(raw, flight)
    assert clean.base_fare == 3400.0
    assert clean.tax is None
    assert clean.fare_decomposition_status == "PARTIAL"


# -------------------------------------------------------------
# 3. Dutot Index Mathematical Robustness Tests
# -------------------------------------------------------------
def test_dutot_normal_calculation():
    engine = IndexEngine()
    current_prices = [4000.0, 5000.0, 6000.0]  # mean = 5000.0
    base_price = 5000.0
    dutot = engine.calculate_dutot(current_prices, base_price)
    assert dutot == 100.0

    current_prices_increase = [5500.0, 6000.0, 6500.0]  # mean = 6000.0
    dutot_up = engine.calculate_dutot(current_prices_increase, base_price)
    assert dutot_up == 120.0


def test_dutot_edge_cases():
    engine = IndexEngine()
    # Empty dataset
    assert engine.calculate_dutot([], 5000.0) == 100.0
    # Zero or negative base price
    assert engine.calculate_dutot([5000.0], 0.0) == 100.0
    assert engine.calculate_dutot([5000.0], -100.0) == 100.0
    # None values inside array are filtered
    assert engine.calculate_dutot([None, 5000.0, 0.0, -100.0], 5000.0) == 100.0
    # Single observation
    assert engine.calculate_dutot([5500.0], 5000.0) == 110.0


# -------------------------------------------------------------
# 4. Jevons Index Mathematical Robustness Tests
# -------------------------------------------------------------
def test_jevons_normal_calculation():
    engine = IndexEngine()
    current_prices = [4000.0, 6000.0]  # geom mean = sqrt(24,000,000) ~ 4898.979
    base_price = 4898.979486
    jevons = engine.calculate_jevons(current_prices, base_price)
    assert math.isclose(jevons, 100.0, abs_tol=1e-2)


def test_jevons_edge_cases():
    engine = IndexEngine()
    # Empty dataset
    assert engine.calculate_jevons([], 5000.0) == 100.0
    # Zero or negative base price
    assert engine.calculate_jevons([5000.0], 0.0) == 100.0
    assert engine.calculate_jevons([5000.0], -500.0) == 100.0
    # Non-positive values filtered out
    assert engine.calculate_jevons([-10.0, 0.0, 5000.0], 5000.0) == 100.0


# -------------------------------------------------------------
# 5. Route Weights & Composite Normalization Tests
# -------------------------------------------------------------
def test_prototype_route_weights_metadata():
    engine = IndexEngine()
    assert isinstance(PROTOTYPE_ROUTE_WEIGHTS, dict)
    assert math.isclose(sum(PROTOTYPE_ROUTE_WEIGHTS.values()), 1.0, abs_tol=1e-3)
    assert engine.methodology_version == "v1.0-prototype"


def test_composite_dynamic_weight_normalization():
    engine = IndexEngine(route_weights={"DEL-BOM": 0.40, "BLR-DEL": 0.60})
    
    fares = [
        CleanFare(route="DEL-BOM", total_price=5500.0, is_outlier=False, observation_type="OBSERVED"),
        CleanFare(route="DEL-BOM", total_price=5500.0, is_outlier=False, observation_type="OBSERVED")
    ]
    # Only DEL-BOM is observed (BLR-DEL missing). Weight should normalize to 1.0
    p0_map = {"DEL-BOM": 5000.0}
    computed = engine._compute_index_records(
        fares=fares,
        period_dt=datetime.datetime(2026, 8, 29),
        frequency="DAILY",
        include_estimated=False,
        base_period="2026-08-28",
        dutot_p0_map=p0_map,
        jevons_p0_map=p0_map,
        is_real_data=True
    )
    
    composite_recs = [r for r in computed if r.route is None]
    assert len(composite_recs) == 1
    comp = composite_recs[0]
    # DEL-BOM index is (5500/5000)*100 = 110.0. Since it is the only route, composite is 110.0
    assert comp.index_value == 110.0
    assert "DEL-BOM" in comp.metadata_json["observed_routes"]
    assert comp.metadata_json["is_official_weight"] == settings.WEIGHT_SOURCE_METADATA["is_official"]
