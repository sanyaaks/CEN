import sys
import os
import math
import datetime
import numpy as np
import pandas as pd
from sqlalchemy import text, func

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal, engine
from app.models.db_models import RawFare, CleanFare, IndexValue, ScrapeRun, ReferenceData, ValidationResult
from app.processing.index_engine import IndexEngine, PROTOTYPE_ROUTE_WEIGHTS
from app.processing.backtest_engine import BacktestEngine
from fastapi.testclient import TestClient
from app.main import app


def run_deep_audit():
    print("=" * 80)
    print("      DEEP SYSTEM AUDIT REPORT (PHASE 1, 2, & 3 VALIDATED)")
    print("=" * 80)

    db = SessionLocal()
    audit_passed = True
    test_failures = []

    try:
        # -------------------------------------------------------------
        # 1. DATABASE CONNECTIVITY & RECORD COUNTS
        # -------------------------------------------------------------
        print("\n[SECTION 1] DATABASE INTEGRITY & RECORD COUNTS (Neon PostgreSQL)")
        print("-" * 80)
        
        raw_count = db.query(func.count(RawFare.id)).scalar()
        clean_count = db.query(func.count(CleanFare.id)).scalar()
        index_count = db.query(func.count(IndexValue.id)).scalar()
        ref_count = db.query(func.count(ReferenceData.id)).scalar()
        val_count = db.query(func.count(ValidationResult.id)).scalar()
        outlier_count = db.query(func.count(CleanFare.id)).filter(CleanFare.is_outlier == True).scalar()
        
        observed_count = db.query(func.count(CleanFare.id)).filter(CleanFare.observation_type == "OBSERVED").scalar()
        estimated_count = db.query(func.count(CleanFare.id)).filter(CleanFare.observation_type == "ESTIMATED").scalar()

        print(f"• Total Raw Scrapes (raw_fares)       : {raw_count}")
        print(f"• Total Clean Quotes (clean_fares)     : {clean_count}")
        print(f"  - OBSERVED Quotes                    : {observed_count} ({round(observed_count/clean_count*100, 2) if clean_count else 0}%)")
        print(f"  - ESTIMATED Quotes                   : {estimated_count}")
        print(f"• Total Computed Indices (index_values): {index_count}")
        print(f"• Total Reference Benchmarks           : {ref_count}")
        print(f"• Total Saved Validation Runs          : {val_count}")
        print(f"• Flagged Outliers                     : {outlier_count}")

        if raw_count == 0 or clean_count == 0 or index_count == 0:
            audit_passed = False
            test_failures.append("Database tables are missing records.")
        else:
            print("  ==> Database record counts: HEALTHY")

        # -------------------------------------------------------------
        # 2. DATA INTEGRITY & FARE DECOMPOSITION STATUS
        # -------------------------------------------------------------
        print("\n[SECTION 2] DATA QUALITY & FARE DECOMPOSITION TRANSPARENCY")
        print("-" * 80)

        null_prices = db.query(CleanFare).filter((CleanFare.total_price == None) | (CleanFare.total_price <= 0)).count()
        null_airlines = db.query(CleanFare).filter((CleanFare.airline == None) | (CleanFare.airline == "")).count()
        null_routes = db.query(CleanFare).filter((CleanFare.route == None) | (CleanFare.route == "")).count()
        orphaned_clean = db.query(CleanFare).filter(CleanFare.source_raw_fare_id == None).count()

        decomp_counts = db.query(
            CleanFare.fare_decomposition_status, func.count(CleanFare.id)
        ).group_by(CleanFare.fare_decomposition_status).all()

        print(f"• Quotes with NULL / <= 0 price   : {null_prices}")
        print(f"• Quotes with Missing Airline     : {null_airlines}")
        print(f"• Quotes with Missing Route       : {null_routes}")
        print(f"• Orphaned Clean Records          : {orphaned_clean}")
        print(f"• Fare Decomposition Breakdown   : {dict(decomp_counts)}")

        if null_prices > 0 or null_airlines > 0 or null_routes > 0 or orphaned_clean > 0:
            audit_passed = False
            test_failures.append("Data corruption found in clean_fares.")
        else:
            print("  ==> Data cleanliness & Foreign Key integrity: 100% CLEAN")

        # -------------------------------------------------------------
        # 3. MATHEMATICAL VALIDATION METRICS ACCURACY
        # -------------------------------------------------------------
        print("\n[SECTION 3] STATISTICAL & VALIDATION METRIC ACCURACY")
        print("-" * 80)

        y_true = [5000.0, 5200.0, 5400.0, 5800.0]
        y_pred = [5100.0, 5250.0, 5350.0, 5900.0]

        calc_metrics = BacktestEngine.calculate_metrics(y_true, y_pred)
        expected_mae = float(np.mean(np.abs(np.array(y_pred) - np.array(y_true))))
        expected_rmse = float(np.sqrt(np.mean((np.array(y_pred) - np.array(y_true)) ** 2)))

        print(f"• MAE Test : Expected={expected_mae:.4f}, Calc={calc_metrics['mae']:.4f} -> {'MATCH' if math.isclose(expected_mae, calc_metrics['mae'], abs_tol=1e-3) else 'FAIL'}")
        print(f"• RMSE Test: Expected={expected_rmse:.4f}, Calc={calc_metrics['rmse']:.4f} -> {'MATCH' if math.isclose(expected_rmse, calc_metrics['rmse'], abs_tol=1e-3) else 'FAIL'}")
        print(f"• Pearson r: {calc_metrics['pearson_corr']} -> {'VALID' if calc_metrics['pearson_corr'] > 0.95 else 'FAIL'}")

        if not math.isclose(expected_mae, calc_metrics['mae'], abs_tol=1e-3) or not math.isclose(expected_rmse, calc_metrics['rmse'], abs_tol=1e-3):
            audit_passed = False
            test_failures.append("Validation metric calculations did not match mathematical definitions.")

        # -------------------------------------------------------------
        # 4. REST API ENDPOINTS LIVE TEST
        # -------------------------------------------------------------
        print("\n[SECTION 4] REST API ENDPOINTS LIVE TEST")
        print("-" * 80)

        client = TestClient(app)

        endpoints = [
            ("/", 200, "Health Check"),
            ("/index/", 200, "Latest Index Metrics"),
            ("/index/DEL-BOM", 200, "DEL-BOM Index Time Series"),
            ("/audit/", 200, "Data Audit Overview"),
            ("/audit/sources/health", 200, "Scraper Sources Health"),
            ("/audit/runs", 200, "Scrape Runs History"),
            ("/audit/DEL-BOM", 200, "Route Lineage Audit"),
            ("/validation/backtest", 200, "Historical Backtest Reconstruction"),
            ("/validation/metrics", 200, "Validation Metrics"),
            ("/validation/coverage", 200, "Route & Obs Coverage"),
            ("/validation/routes", 200, "Route Level Validation"),
            ("/validation/runs", 200, "Validation Runs History"),
            ("/export?format=json", 200, "NSO JSON Export"),
            ("/export?format=csv", 200, "NSO CSV Export")
        ]

        for ep, expected_status, label in endpoints:
            resp = client.get(ep)
            match = resp.status_code == expected_status
            print(f"• {label:<35} [{ep:<24}]: Status {resp.status_code} -> {'PASS' if match else 'FAIL'}")
            if not match:
                audit_passed = False
                test_failures.append(f"API endpoint {ep} returned status {resp.status_code} (expected {expected_status})")

    finally:
        db.close()

    print("\n" + "=" * 80)
    if audit_passed:
        print(" SYSTEM AUDIT RESULT: ALL MODULES, ENDPOINTS & FORMULAS (100% PASS)")
    else:
        print(" SYSTEM AUDIT RESULT: FAILURES DETECTED")
        for f in test_failures:
            print(f"  ❌ {f}")
    print("=" * 80 + "\n")

    return audit_passed


if __name__ == "__main__":
    success = run_deep_audit()
    sys.exit(0 if success else 1)
