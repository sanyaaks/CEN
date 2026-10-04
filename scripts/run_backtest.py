import sys
import os
import json
import csv
import argparse
import datetime
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal
from app.processing.backtest_engine import BacktestEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_backtest")


def execute_backtest(
    start_date_str: str,
    end_date_str: str,
    method: str = "Dutot",
    reference_source: str = "SAMPLE_BENCHMARK",
    output_dir: str = "reports/backtest"
):
    print("=" * 80)
    print("   HISTORICAL AIRFARE INDEX BACKTEST & VALIDATION SUITE (PHASE 3)")
    print("=" * 80)

    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()

    print(f"• Backtest Window        : {start_date} to {end_date} ({(end_date - start_date).days + 1} days)")
    print(f"• Elementary Formula     : {method}")
    print(f"• Reference Source       : {reference_source}")
    print("-" * 80)

    db = SessionLocal()
    engine = BacktestEngine()

    try:
        report = engine.run_backtest_and_validation(
            db=db,
            start_date=start_date,
            end_date=end_date,
            reference_source=reference_source,
            method=method,
            save_results=True
        )

        if report.get("status") == "NO_DATA":
            print(f"❌ Backtest failed: {report.get('message')}")
            return False

        print(f"\n[BACKTEST RESULTS SUMMARY]")
        print(f"• Validation ID          : {report['validation_id']}")
        print(f"• Base Period P0 Date    : {report['base_period']}")
        print(f"• Days Reconstructed     : {report['validation_period']['days_count']}")
        print(f"• Our Mean Index Value   : {report['our_mean_index']:.4f}")
        print(f"• Reference Mean Value   : {report['reference_mean_value']:.4f}")
        print(f"• Reference Status       : {report['reference_status']}")

        cov = report["coverage_summary"]
        print(f"\n[DATA COVERAGE METRICS]")
        print(f"• Total Observations     : {cov['total_observations']}")
        print(f"• Observed (Real Quotes) : {cov['observed_observations']}")
        print(f"• Avg Route Coverage     : {cov['average_route_coverage_percent']:.2f}%")
        print(f"• Avg Observation Cov    : {cov['average_observation_coverage_percent']:.2f}%")

        m = report["metrics"]
        mape_str = f"{m['mape']:.2f}%" if m.get("mape") is not None else "N/A"
        pct_dev_str = f"{m['mean_pct_deviation']:.2f}%" if m.get("mean_pct_deviation") is not None else "N/A"
        dir_agr_str = f"{m['directional_agreement_pct']:.2f}%" if m.get("directional_agreement_pct") is not None else "N/A"

        print(f"\n[VALIDATION METRICS vs {reference_source}]")
        print(f"• Mean Absolute Error    : {m['mae']}")
        print(f"• Mean Abs Pct Error     : {mape_str}")
        print(f"• Root Mean Square Error : {m['rmse']}")
        print(f"• Pearson Correlation    : {m['pearson_corr']}")
        print(f"• Mean % Deviation       : {pct_dev_str}")
        print(f"• Directional Agreement  : {dir_agr_str}")

        sens = report["sensitivity_analysis"]
        print(f"\n[SENSITIVITY ANALYSIS]")
        print(f"• Baseline (Clean) Index : {sens['baseline_mean_index']:.4f}")
        print(f"• Unfiltered (Outliers)  : {sens['unfiltered_outliers_mean_index']}")
        print(f"• Estimated Inclusive    : {sens['estimated_inclusive_mean_index']}")

        # Write reports
        os.makedirs(output_dir, exist_ok=True)
        summary_path = os.path.join(output_dir, "backtest_summary.json")
        metrics_path = os.path.join(output_dir, "validation_metrics.json")
        csv_path = os.path.join(output_dir, "backtest_results.csv")

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(report["metrics"], f, indent=2)

        daily_rows = report.get("daily_series", [])
        if daily_rows:
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "date",
                    "base_period",
                    "composite_index",
                    "method",
                    "observed_routes_count",
                    "route_coverage_percent",
                    "total_observations_count",
                    "observed_count",
                    "observation_coverage_percent"
                ])
                for d in daily_rows:
                    writer.writerow([
                        d["date"],
                        d["base_period"],
                        d["composite_index"],
                        d["method"],
                        d["observed_routes_count"],
                        d["route_coverage_percent"],
                        d["total_observations_count"],
                        d["observed_count"],
                        d["observation_coverage_percent"]
                    ])

        print(f"\n[REPORT ARTIFACTS SAVED]")
        print(f"• Summary JSON           : {summary_path}")
        print(f"• Metrics JSON           : {metrics_path}")
        print(f"• Daily Series CSV       : {csv_path}")
        print("=" * 80)
        return True

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run historical backtest and reference validation pipeline.")
    parser.add_argument("--start-date", type=str, default="2026-08-30", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2026-10-13", help="End date (YYYY-MM-DD)")
    parser.add_argument("--method", type=str, default="Dutot", help="Dutot or Jevons")
    parser.add_argument("--reference-source", type=str, default="SAMPLE_BENCHMARK", help="Reference source name")
    parser.add_argument("--output-dir", type=str, default="reports/backtest", help="Report output folder")

    args = parser.parse_args()
    execute_backtest(
        start_date_str=args.start_date,
        end_date_str=args.end_date,
        method=args.method,
        reference_source=args.reference_source,
        output_dir=args.output_dir
    )
