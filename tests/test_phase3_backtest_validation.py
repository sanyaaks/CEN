import math
import datetime
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models.db_models import CleanFare, ReferenceData, ValidationResult
from app.processing.backtest_engine import BacktestEngine
from app.main import app


# -------------------------------------------------------------
# 1. Mathematical Metrics Tests
# -------------------------------------------------------------
def test_validation_metrics_calculations():
    y_true = [5000.0, 5200.0, 5400.0, 5800.0]
    y_pred = [5100.0, 5250.0, 5350.0, 5900.0]

    metrics = BacktestEngine.calculate_metrics(y_true, y_pred)
    assert metrics["mae"] == 75.0  # (|100| + |50| + |50| + |100|)/4 = 300/4 = 75.0
    assert metrics["rmse"] > 0
    assert metrics["pearson_corr"] is not None
    assert metrics["pearson_corr"] > 0.95
    assert metrics["directional_agreement_pct"] == 100.0


def test_validation_metrics_empty_handling():
    metrics = BacktestEngine.calculate_metrics([], [])
    assert metrics["mae"] is None
    assert metrics["pearson_corr"] is None


# -------------------------------------------------------------
# 2. Coverage Metrics Distinction Tests
# -------------------------------------------------------------
def test_route_vs_observation_coverage_distinction():
    # Scenario: 6 routes configured, 5 routes have data
    # 100 quotes total, 90 observed, 10 estimated
    configured_routes = ["DEL-BOM", "BLR-DEL", "HYD-MAA", "DEL-MAA", "BOM-BLR", "DEL-CCU"]
    observed_routes = ["DEL-BOM", "BLR-DEL", "HYD-MAA", "DEL-MAA", "BOM-BLR"]
    
    route_cov = (len(observed_routes) / len(configured_routes)) * 100.0
    obs_cov = (90 / 100) * 100.0

    assert round(route_cov, 2) == 83.33
    assert obs_cov == 90.0
    assert route_cov != obs_cov  # Clearly distinct concepts


# -------------------------------------------------------------
# 3. Deterministic Backtest Reproducibility Tests
# -------------------------------------------------------------
def test_backtest_engine_reproducibility():
    db: Session = SessionLocal()
    engine = BacktestEngine()
    
    start_date = datetime.date(2026, 8, 30)
    end_date = datetime.date(2026, 10, 13)

    try:
        # Run 1
        res1 = engine.run_backtest_and_validation(
            db=db,
            start_date=start_date,
            end_date=end_date,
            reference_source="SAMPLE_BENCHMARK",
            save_results=False
        )

        # Run 2
        res2 = engine.run_backtest_and_validation(
            db=db,
            start_date=start_date,
            end_date=end_date,
            reference_source="SAMPLE_BENCHMARK",
            save_results=False
        )

        # Deterministic assertions
        assert res1["our_mean_index"] == res2["our_mean_index"]
        assert res1["coverage_summary"] == res2["coverage_summary"]
        assert res1["base_period"] == res2["base_period"]
        assert len(res1["daily_series"]) == len(res2["daily_series"])

    finally:
        db.close()


# -------------------------------------------------------------
# 4. Reference Data Persistence & Query Tests
# -------------------------------------------------------------
def test_reference_data_integrity():
    db: Session = SessionLocal()
    try:
        sample_ref = db.query(ReferenceData).filter(ReferenceData.source == "SAMPLE_BENCHMARK").first()
        assert sample_ref is not None
        assert sample_ref.is_official is False
        assert sample_ref.value > 0
    finally:
        db.close()


# -------------------------------------------------------------
# 5. Validation API Endpoints Integration Tests
# -------------------------------------------------------------
def test_validation_api_endpoints():
    client = TestClient(app)

    # 1. Backtest endpoint
    r_bt = client.get("/validation/backtest?start_date=2026-08-30&end_date=2026-10-13")
    assert r_bt.status_code == 200
    data_bt = r_bt.json()
    assert "our_mean_index" in data_bt
    assert "daily_series" in data_bt

    # 2. Metrics endpoint
    r_met = client.get("/validation/metrics?start_date=2026-08-30&end_date=2026-10-13")
    assert r_met.status_code == 200
    data_met = r_met.json()
    assert "metrics" in data_met

    # 3. Coverage endpoint
    r_cov = client.get("/validation/coverage?start_date=2026-08-30&end_date=2026-10-13")
    assert r_cov.status_code == 200
    data_cov = r_cov.json()
    assert "average_route_coverage_percent" in data_cov["summary"]
    assert "average_observation_coverage_percent" in data_cov["summary"]

    # 4. Routes comparison endpoint
    r_rt = client.get("/validation/routes?start_date=2026-08-30&end_date=2026-10-13")
    assert r_rt.status_code == 200
    data_rt = r_rt.json()
    assert "routes" in data_rt

    # 5. Runs history endpoint
    r_runs = client.get("/validation/runs")
    assert r_runs.status_code == 200
    data_runs = r_runs.json()
    assert "runs" in data_runs
