import pytest
import math
import datetime
from app.processing.index_engine import IndexEngine
from app.models.db_models import CleanFare
from app.config import settings


def test_dutot_hand_calculated_worked_example():
    """
    WORKED EXAMPLE: Dutot Elementary Index
    Formula: I_D = (mean(current_prices) / mean(base_prices)) * 100
    
    Route A (DEL-BOM):
      Base prices:    [4000.0, 5000.0, 6000.0] -> Mean = 5000.0
      Current prices: [4400.0, 5500.0, 6600.0] -> Mean = 5500.0
      Expected Dutot = (5500.0 / 5000.0) * 100 = 110.0000
    """
    engine = IndexEngine()
    base_fare = 5000.0
    current_fares = [4400.0, 5500.0, 6600.0]

    dutot_result = engine.calculate_dutot(current_fares, base_fare)
    assert dutot_result == 110.0000


def test_jevons_hand_calculated_worked_example():
    """
    WORKED EXAMPLE: Jevons Elementary Index
    Formula: I_J = (geometric_mean(current_prices) / geometric_mean(base_prices)) * 100
             I_J = exp( mean(ln(current_prices)) - ln(base_geom) ) * 100
    
    Route A (DEL-BOM):
      Base prices:    [4000.0, 5000.0, 6000.0]
        Geometric Mean Base = (4000 * 5000 * 6000)^(1/3) = (1.2e11)^(1/3) = 4932.42414866
      Current prices: [4400.0, 5500.0, 6600.0]
        Geometric Mean Curr = (4400 * 5500 * 6600)^(1/3) = (1.5972e11)^(1/3) = 5425.66656353
      Expected Jevons = (5425.66656353 / 4932.42414866) * 100 = 110.0000
    """
    engine = IndexEngine()
    base_geom = (4000.0 * 5000.0 * 6000.0) ** (1.0 / 3.0)
    current_fares = [4400.0, 5500.0, 6600.0]

    jevons_result = engine.calculate_jevons(current_fares, base_geom)
    assert round(jevons_result, 4) == 110.0000


def test_two_route_weighted_composite_worked_example():
    """
    WORKED EXAMPLE: 2-Route National Composite
    
    Route 1: DEL-BOM (Weight = 0.60)
      Base prices:    [4000.0, 5000.0, 6000.0] -> P0_Dutot = 5000.0, P0_Jevons = 4932.42
      Current prices: [4400.0, 5500.0, 6600.0] -> Mean = 5500.0 -> Dutot_1 = 110.0000
      
    Route 2: BLR-DEL (Weight = 0.40)
      Base prices:    [3000.0, 3500.0, 4000.0] -> P0_Dutot = 3500.0, P0_Jevons = 3476.03
      Current prices: [3600.0, 3500.0, 4900.0] -> Mean = 4000.0 -> Dutot_2 = (4000/3500)*100 = 114.2857
      
    Weights sum: 0.60 + 0.40 = 1.00 (100%)
    Theoretical Composite Dutot:
      (0.60 * 110.0000 + 0.40 * 114.2857) / 1.00 = 66.0000 + 45.71428 = 111.7143
    """
    custom_weights = {
        "DEL-BOM": 0.60,
        "BLR-DEL": 0.40
    }
    engine = IndexEngine(route_weights=custom_weights)

    # Base Fare Map
    dutot_p0_map = {
        "DEL-BOM": 5000.0,
        "BLR-DEL": 3500.0
    }
    jevons_p0_map = {
        "DEL-BOM": 4932.42,
        "BLR-DEL": 3476.03
    }

    # Synthetic CleanFare objects for testing
    now = datetime.datetime.now(datetime.timezone.utc)
    fares = [
        # Route 1 (DEL-BOM): 3 fares
        CleanFare(id=1, route="DEL-BOM", total_price=4400.0, observation_type="OBSERVED", is_outlier=False, date=now),
        CleanFare(id=2, route="DEL-BOM", total_price=5500.0, observation_type="OBSERVED", is_outlier=False, date=now),
        CleanFare(id=3, route="DEL-BOM", total_price=6600.0, observation_type="OBSERVED", is_outlier=False, date=now),
        # Route 2 (BLR-DEL): 3 fares
        CleanFare(id=4, route="BLR-DEL", total_price=3600.0, observation_type="OBSERVED", is_outlier=False, date=now),
        CleanFare(id=5, route="BLR-DEL", total_price=3500.0, observation_type="OBSERVED", is_outlier=False, date=now),
        CleanFare(id=6, route="BLR-DEL", total_price=4900.0, observation_type="OBSERVED", is_outlier=False, date=now),
    ]

    records = engine._compute_index_records(
        fares=fares,
        period_dt=now,
        frequency="DAILY",
        include_estimated=False,
        base_period="2026-08-01",
        dutot_p0_map=dutot_p0_map,
        jevons_p0_map=jevons_p0_map,
        is_real_data=True
    )

    # 2 routes * 2 methods (Dutot + Jevons) + 1 National Composite = 5 records
    assert len(records) == 5

    # Check DEL-BOM Dutot
    del_bom_dutot = next(r for r in records if r.route == "DEL-BOM" and r.method == "Dutot")
    assert del_bom_dutot.index_value == 110.0

    # Check BLR-DEL Dutot
    blr_del_dutot = next(r for r in records if r.route == "BLR-DEL" and r.method == "Dutot")
    assert blr_del_dutot.index_value == 114.2857

    # Check Composite record (route is None)
    composite = next(r for r in records if r.route is None)
    assert composite.method == "DGCA_Weighted_Dutot"
    assert composite.index_value == 111.7143


def test_prototype_weights_sum_to_one_hundred_percent():
    """
    CONFIRMATION: All prototype route weights in settings sum to 1.0 (100%).
    """
    weights = settings.PROTOTYPE_ROUTE_WEIGHTS
    total_sum = sum(weights.values())
    assert round(total_sum, 6) == 1.0, f"Prototype route weights must sum to 1.0, got {total_sum}"


def test_missing_route_dynamic_weight_renormalization():
    """
    INTEGRITY CHECK: Zero Data for a Route
    If Route B (BLR-DEL, weight 0.40) has zero data on a given day,
    the engine must dynamically renormalize remaining weights so the composite
    does not falsely drop to 66.0 (0.60 * 110.0).
    It must yield 110.0 (100% weight given to observed Route A).
    """
    custom_weights = {
        "DEL-BOM": 0.60,
        "BLR-DEL": 0.40
    }
    engine = IndexEngine(route_weights=custom_weights)

    dutot_p0_map = {"DEL-BOM": 5000.0, "BLR-DEL": 3500.0}
    jevons_p0_map = {"DEL-BOM": 4932.42, "BLR-DEL": 3476.03}

    now = datetime.datetime.now(datetime.timezone.utc)
    # ONLY DEL-BOM fares present (BLR-DEL has zero data)
    fares_only_route_a = [
        CleanFare(id=1, route="DEL-BOM", total_price=4400.0, observation_type="OBSERVED", is_outlier=False, date=now),
        CleanFare(id=2, route="DEL-BOM", total_price=5500.0, observation_type="OBSERVED", is_outlier=False, date=now),
        CleanFare(id=3, route="DEL-BOM", total_price=6600.0, observation_type="OBSERVED", is_outlier=False, date=now),
    ]

    records = engine._compute_index_records(
        fares=fares_only_route_a,
        period_dt=now,
        frequency="DAILY",
        include_estimated=False,
        base_period="2026-08-01",
        dutot_p0_map=dutot_p0_map,
        jevons_p0_map=jevons_p0_map,
        is_real_data=True
    )

    composite = next(r for r in records if r.route is None)
    # With normalization: (0.60 * 110.0) / 0.60 = 110.0
    assert composite.index_value == 110.0
    assert composite.metadata_json["normalized_weight_sum"] == 0.6
    assert "BLR-DEL" in composite.metadata_json["excluded_routes"]
    assert "DEL-BOM" in composite.metadata_json["observed_routes"]
