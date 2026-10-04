import math
import uuid
import logging
import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.db_models import CleanFare, ReferenceData, ValidationResult
from app.processing.index_engine import IndexEngine, PROTOTYPE_ROUTE_WEIGHTS
from app.config import settings

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Historical Backtesting & Validation Engine (Phase 3).
    Reconstructs historical elementary and composite index series deterministically from
    stored observations, computes coverage and quality metrics, and evaluates performance
    against external reference benchmarks without data fabrication.
    """

    def __init__(
        self,
        routes: Optional[List[str]] = None,
        methodology_version: str = "v1.0-prototype",
        weight_version: str = "v1.0-prototype"
    ):
        self.routes = routes or settings.routes_list
        self.methodology_version = methodology_version
        self.weight_version = weight_version
        self.index_engine = IndexEngine(
            route_weights=PROTOTYPE_ROUTE_WEIGHTS,
            methodology_version=methodology_version
        )

    @staticmethod
    def calculate_metrics(y_true: List[float], y_pred: List[float]) -> Dict[str, Optional[float]]:
        """
        Calculates standard mathematical comparison metrics between our index and reference benchmarks.
        """
        if not y_true or not y_pred or len(y_true) != len(y_pred) or len(y_true) < 1:
            return {
                "mae": None,
                "mape": None,
                "rmse": None,
                "pearson_corr": None,
                "spearman_corr": None,
                "mean_pct_deviation": None,
                "directional_agreement_pct": None
            }

        arr_true = np.array(y_true, dtype=float)
        arr_pred = np.array(y_pred, dtype=float)
        n = len(arr_true)

        # 1. Mean Absolute Error (MAE)
        mae = float(np.mean(np.abs(arr_pred - arr_true)))

        # 2. Mean Absolute Percentage Error (MAPE) - safe when true != 0
        valid_mape_idx = arr_true != 0
        mape = float(np.mean(np.abs((arr_pred[valid_mape_idx] - arr_true[valid_mape_idx]) / arr_true[valid_mape_idx])) * 100.0) if np.any(valid_mape_idx) else None

        # 3. Root Mean Square Error (RMSE)
        rmse = float(np.sqrt(np.mean((arr_pred - arr_true) ** 2)))

        # 4. Pearson & Spearman Correlations (Requires at least 2 distinct points)
        if n >= 2 and np.std(arr_true) > 0 and np.std(arr_pred) > 0:
            pearson_corr = float(np.corrcoef(arr_true, arr_pred)[0, 1])
            spearman_corr = float(stats.spearmanr(arr_true, arr_pred).correlation)
        else:
            pearson_corr = None
            spearman_corr = None

        # 5. Mean Percentage Deviation
        mean_true = float(np.mean(arr_true))
        mean_pred = float(np.mean(arr_pred))
        mean_pct_dev = float(((mean_pred - mean_true) / mean_true) * 100.0) if mean_true != 0 else None

        # 6. Directional Agreement (Sign of period-over-period differences)
        if n >= 2:
            diff_true = np.diff(arr_true)
            diff_pred = np.diff(arr_pred)
            same_dir = (diff_true * diff_pred) > 0
            dir_agreement = float(np.mean(same_dir) * 100.0)
        else:
            dir_agreement = None

        return {
            "mae": round(mae, 4) if mae is not None else None,
            "mape": round(mape, 4) if mape is not None else None,
            "rmse": round(rmse, 4) if rmse is not None else None,
            "pearson_corr": round(pearson_corr, 4) if pearson_corr is not None else None,
            "spearman_corr": round(spearman_corr, 4) if spearman_corr is not None else None,
            "mean_pct_deviation": round(mean_pct_dev, 4) if mean_pct_dev is not None else None,
            "directional_agreement_pct": round(dir_agreement, 2) if dir_agreement is not None else None
        }

    def reconstruct_daily_indices(
        self,
        db: Session,
        start_date: datetime.date,
        end_date: datetime.date,
        method: str = "Dutot",
        include_estimated: bool = False,
        filter_outliers: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Deterministically reconstructs daily route indices and national composite series.
        """
        start_dt = datetime.datetime.combine(start_date, datetime.time.min)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max)

        query = db.query(CleanFare).filter(
            CleanFare.date >= start_dt,
            CleanFare.date <= end_dt,
            CleanFare.total_price > 0
        )
        if filter_outliers:
            query = query.filter(CleanFare.is_outlier == False)
        if not include_estimated:
            query = query.filter(CleanFare.observation_type == "OBSERVED")

        all_fares = query.all()
        if not all_fares:
            return []

        # Find base period: first valid day in dataset
        earliest_dt = min(f.date for f in all_fares)
        base_period_str = earliest_dt.strftime("%Y-%m-%d")

        # Derive base prices P0 per route from that first valid day
        base_day_fares = [f for f in all_fares if f.date.strftime("%Y-%m-%d") == base_period_str]
        dutot_p0: Dict[str, float] = {}
        jevons_p0: Dict[str, float] = {}
        for r_name in self.routes:
            p_list = [f.total_price for f in base_day_fares if f.route == r_name and f.total_price > 0]
            if p_list:
                dutot_p0[r_name] = round(float(np.mean(p_list)), 2)
                jevons_p0[r_name] = round(float(np.exp(np.mean(np.log(p_list)))), 2)

        # Group fares by calendar date
        df = pd.DataFrame([{
            "date": f.date.strftime("%Y-%m-%d"),
            "route": f.route,
            "total_price": f.total_price,
            "observation_type": f.observation_type
        } for f in all_fares])

        daily_results: List[Dict[str, Any]] = []

        for date_str, day_group in df.groupby("date"):
            route_indices = {}
            route_stats = {}
            observed_routes = []

            for r_name in self.routes:
                r_group = day_group[day_group["route"] == r_name]
                prices = [p for p in r_group["total_price"].tolist() if p > 0]
                if prices:
                    observed_routes.append(r_name)
                    p0 = dutot_p0.get(r_name, float(np.mean(prices))) if method == "Dutot" else jevons_p0.get(r_name, float(np.exp(np.mean(np.log(prices)))))
                    idx_val = self.index_engine.calculate_dutot(prices, p0) if method == "Dutot" else self.index_engine.calculate_jevons(prices, p0)
                    route_indices[r_name] = idx_val
                    route_stats[r_name] = {
                        "sample_size": len(prices),
                        "mean_price": round(float(np.mean(prices)), 2),
                        "index_value": idx_val
                    }

            # Composite Index Calculation with dynamic weight normalization
            total_w = 0.0
            weighted_sum = 0.0
            for r_name, idx_val in route_indices.items():
                w = PROTOTYPE_ROUTE_WEIGHTS.get(r_name, 0.10)
                weighted_sum += idx_val * w
                total_w += w

            composite_val = round(weighted_sum / total_w, 4) if total_w > 0 else 100.0

            route_coverage_pct = round((len(observed_routes) / len(self.routes)) * 100.0, 2)
            total_obs = len(day_group)
            obs_cnt = int((day_group["observation_type"] == "OBSERVED").sum())
            obs_cov_pct = round((obs_cnt / total_obs) * 100.0, 2) if total_obs > 0 else 100.0

            daily_results.append({
                "date": date_str,
                "base_period": base_period_str,
                "composite_index": composite_val,
                "method": method,
                "route_indices": route_indices,
                "route_stats": route_stats,
                "configured_routes_count": len(self.routes),
                "observed_routes_count": len(observed_routes),
                "route_coverage_percent": route_coverage_pct,
                "total_observations_count": total_obs,
                "observed_count": obs_cnt,
                "estimated_count": total_obs - obs_cnt,
                "observation_coverage_percent": obs_cov_pct,
                "methodology_version": self.methodology_version
            })

        return sorted(daily_results, key=lambda x: x["date"])

    def run_backtest_and_validation(
        self,
        db: Session,
        start_date: datetime.date,
        end_date: datetime.date,
        reference_source: str = "SAMPLE_BENCHMARK",
        method: str = "Dutot",
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Executes complete backtest, sensitivity comparisons, and reference validation.
        """
        validation_id = f"val_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # 1. Baseline Reconstruction (OBSERVED only, Outliers Filtered)
        baseline_daily = self.reconstruct_daily_indices(
            db=db,
            start_date=start_date,
            end_date=end_date,
            method=method,
            include_estimated=False,
            filter_outliers=True
        )

        if not baseline_daily:
            return {
                "validation_id": validation_id,
                "status": "NO_DATA",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "message": "No valid observations found in specified date range."
            }

        # 2. Sensitivity Scenarios
        # Scenario A: Unfiltered (Outliers Included)
        unfiltered_daily = self.reconstruct_daily_indices(
            db=db,
            start_date=start_date,
            end_date=end_date,
            method=method,
            include_estimated=False,
            filter_outliers=False
        )

        # Scenario B: Estimated Inclusive
        estimated_inclusive_daily = self.reconstruct_daily_indices(
            db=db,
            start_date=start_date,
            end_date=end_date,
            method=method,
            include_estimated=True,
            filter_outliers=True
        )

        # 3. Monthly Aggregation for Reference Comparison
        monthly_reconstructed: Dict[str, List[float]] = {}
        for d in baseline_daily:
            m_key = d["date"][:7]  # YYYY-MM
            if m_key not in monthly_reconstructed:
                monthly_reconstructed[m_key] = []
            monthly_reconstructed[m_key].append(d["composite_index"])

        monthly_averages = {m: float(np.mean(vals)) for m, vals in monthly_reconstructed.items()}

        # 4. Fetch External Reference Benchmarks
        ref_records = db.query(ReferenceData).filter(
            ReferenceData.source == reference_source,
            ReferenceData.route == None
        ).all()

        our_comparison_values = []
        ref_comparison_values = []
        for r in ref_records:
            if r.reference_period in monthly_averages:
                our_comparison_values.append(monthly_averages[r.reference_period])
                ref_comparison_values.append(r.value)

        # Compute Metrics against Reference
        metrics = self.calculate_metrics(ref_comparison_values, our_comparison_values)
        ref_status = "VALIDATED" if len(ref_comparison_values) > 0 else "PENDING_REFERENCE_DATA"

        # Overall summary statistics
        all_comp_indices = [d["composite_index"] for d in baseline_daily]
        mean_index = round(float(np.mean(all_comp_indices)), 4) if all_comp_indices else 100.0
        avg_route_cov = round(float(np.mean([d["route_coverage_percent"] for d in baseline_daily])), 2)
        avg_obs_cov = round(float(np.mean([d["observation_coverage_percent"] for d in baseline_daily])), 2)
        total_obs = sum(d["total_observations_count"] for d in baseline_daily)
        total_observed = sum(d["observed_count"] for d in baseline_daily)

        summary_report = {
            "validation_id": validation_id,
            "validation_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_count": len(baseline_daily)
            },
            "base_period": baseline_daily[0]["base_period"] if baseline_daily else None,
            "methodology_version": self.methodology_version,
            "weight_version": self.weight_version,
            "index_method": method,
            "reference_source": reference_source,
            "reference_status": ref_status,
            "our_mean_index": mean_index,
            "reference_mean_value": round(float(np.mean(ref_comparison_values)), 4) if ref_comparison_values else 0.0,
            "metrics": metrics,
            "coverage_summary": {
                "total_observations": total_obs,
                "observed_observations": total_observed,
                "average_route_coverage_percent": avg_route_cov,
                "average_observation_coverage_percent": avg_obs_cov
            },
            "sensitivity_analysis": {
                "baseline_mean_index": mean_index,
                "unfiltered_outliers_mean_index": round(float(np.mean([d["composite_index"] for d in unfiltered_daily])), 4) if unfiltered_daily else None,
                "estimated_inclusive_mean_index": round(float(np.mean([d["composite_index"] for d in estimated_inclusive_daily])), 4) if estimated_inclusive_daily else None
            },
            "daily_series": baseline_daily
        }

        # 5. Persist to Neon DB validation_results table if requested
        if save_results:
            val_record = ValidationResult(
                validation_id=validation_id,
                validation_type="HISTORICAL_BACKTEST",
                start_date=start_date,
                end_date=end_date,
                reference_source=reference_source,
                index_method=method,
                route=None,
                our_mean_index=mean_index,
                reference_mean_value=summary_report["reference_mean_value"],
                mae=metrics.get("mae"),
                mape=metrics.get("mape"),
                rmse=metrics.get("rmse"),
                pearson_corr=metrics.get("pearson_corr"),
                spearman_corr=metrics.get("spearman_corr"),
                mean_pct_deviation=metrics.get("mean_pct_deviation"),
                directional_agreement_pct=metrics.get("directional_agreement_pct"),
                sample_size=total_obs,
                observed_count=total_observed,
                coverage_percent=avg_obs_cov,
                route_coverage_percent=avg_route_cov,
                methodology_version=self.methodology_version,
                weight_version=self.weight_version,
                metadata_json={
                    "base_period": summary_report["base_period"],
                    "sensitivity": summary_report["sensitivity_analysis"],
                    "reference_status": ref_status
                },
                created_at=datetime.datetime.utcnow()
            )
            db.add(val_record)
            db.commit()
            db.refresh(val_record)

        return summary_report
