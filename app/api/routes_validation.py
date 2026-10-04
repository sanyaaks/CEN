import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.db_models import ValidationResult, ReferenceData
from app.processing.backtest_engine import BacktestEngine
from app.api.cache import api_cache

router = APIRouter(prefix="/validation", tags=["Historical Validation & Backtesting"])


@router.get("/backtest")
def get_historical_backtest(
    start_date: str = Query("2026-08-30", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query("2026-10-13", description="End date (YYYY-MM-DD)"),
    method: str = Query("Dutot", description="Dutot or Jevons"),
    reference_source: str = Query("SAMPLE_BENCHMARK", description="External reference source name"),
    db: Session = Depends(get_db)
):
    """
    GET /validation/backtest: Runs and returns deterministic historical backtest reconstruction
    with sensitivity comparisons and base period metadata.
    """
    cache_key = f"val_backtest_{start_date}_{end_date}_{method}_{reference_source}"
    cached = api_cache.get(cache_key)
    if cached:
        return cached

    try:
        s_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        e_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    engine = BacktestEngine()
    result = engine.run_backtest_and_validation(
        db=db,
        start_date=s_dt,
        end_date=e_dt,
        reference_source=reference_source,
        method=method,
        save_results=False
    )
    api_cache.set(cache_key, result, ttl_sec=30)
    return result


@router.get("/metrics")
def get_validation_metrics(
    start_date: str = Query("2026-08-30"),
    end_date: str = Query("2026-10-13"),
    reference_source: str = Query("SAMPLE_BENCHMARK"),
    db: Session = Depends(get_db)
):
    """
    GET /validation/metrics: Returns MAE, MAPE, RMSE, Pearson Correlation, and Directional Agreement
    against external reference benchmarks.
    """
    try:
        s_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        e_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    engine = BacktestEngine()
    result = engine.run_backtest_and_validation(
        db=db,
        start_date=s_dt,
        end_date=e_dt,
        reference_source=reference_source,
        save_results=False
    )

    return {
        "validation_period": result.get("validation_period"),
        "reference_source": reference_source,
        "reference_status": result.get("reference_status"),
        "our_mean_index": result.get("our_mean_index"),
        "reference_mean_value": result.get("reference_mean_value"),
        "metrics": result.get("metrics"),
        "methodology_version": result.get("methodology_version")
    }


@router.get("/coverage")
def get_validation_coverage(
    start_date: str = Query("2026-08-30"),
    end_date: str = Query("2026-10-13"),
    db: Session = Depends(get_db)
):
    """
    GET /validation/coverage: Returns separate metrics for Route Coverage and Observation Coverage.
    """
    cache_key = f"val_coverage_{start_date}_{end_date}"
    cached = api_cache.get(cache_key)
    if cached:
        return cached

    try:
        s_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        e_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    engine = BacktestEngine()
    daily_series = engine.reconstruct_daily_indices(
        db=db,
        start_date=s_dt,
        end_date=e_dt,
        include_estimated=False,
        filter_outliers=True
    )

    if not daily_series:
        return {"status": "NO_DATA", "coverage": {}}

    total_obs = sum(d["total_observations_count"] for d in daily_series)
    observed_obs = sum(d["observed_count"] for d in daily_series)

    res = {
        "period": {"start_date": start_date, "end_date": end_date, "days": len(daily_series)},
        "summary": {
            "total_observations": total_obs,
            "observed_observations": observed_obs,
            "average_route_coverage_percent": round(sum(d["route_coverage_percent"] for d in daily_series) / len(daily_series), 2),
            "average_observation_coverage_percent": round(sum(d["observation_coverage_percent"] for d in daily_series) / len(daily_series), 2)
        },
        "daily_breakdown": [
            {
                "date": d["date"],
                "observed_routes": d["observed_routes_count"],
                "configured_routes": d["configured_routes_count"],
                "route_coverage_percent": d["route_coverage_percent"],
                "observed_quotes": d["observed_count"],
                "total_quotes": d["total_observations_count"],
                "observation_coverage_percent": d["observation_coverage_percent"]
            }
            for d in daily_series
        ]
    }
    api_cache.set(cache_key, res, ttl_sec=30)
    return res


@router.get("/routes")
def get_route_level_validation(
    start_date: str = Query("2026-08-30"),
    end_date: str = Query("2026-10-13"),
    reference_source: str = Query("SAMPLE_BENCHMARK"),
    db: Session = Depends(get_db)
):
    """
    GET /validation/routes: Returns route-by-route index levels compared to external route-level reference benchmarks.
    """
    try:
        s_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        e_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    engine = BacktestEngine()
    daily_series = engine.reconstruct_daily_indices(
        db=db,
        start_date=s_dt,
        end_date=e_dt,
        include_estimated=False,
        filter_outliers=True
    )

    route_averages = {}
    for d in daily_series:
        for r_name, val in d.get("route_indices", {}).items():
            if r_name not in route_averages:
                route_averages[r_name] = []
            route_averages[r_name].append(val)

    ref_records = {
        r.route: r.value for r in db.query(ReferenceData).filter(
            ReferenceData.source == reference_source,
            ReferenceData.route != None
        ).all()
    }

    route_comparison = []
    for r_name, val_list in route_averages.items():
        our_avg = round(float(sum(val_list) / len(val_list)), 4)
        ref_val = ref_records.get(r_name)
        diff = round(our_avg - ref_val, 4) if ref_val is not None else None
        pct_diff = round(((our_avg - ref_val) / ref_val) * 100.0, 2) if ref_val is not None and ref_val != 0 else None

        route_comparison.append({
            "route": r_name,
            "our_mean_index": our_avg,
            "reference_benchmark_value": ref_val,
            "difference": diff,
            "pct_difference": pct_diff,
            "reference_source": reference_source if ref_val is not None else "PENDING_BENCHMARK",
            "days_observed": len(val_list)
        })

    return {
        "routes_count": len(route_comparison),
        "routes": route_comparison
    }


@router.get("/runs")
def get_validation_run_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    GET /validation/runs: Returns historical backtest validation runs saved in Neon PostgreSQL.
    """
    runs = db.query(ValidationResult).order_by(ValidationResult.created_at.desc()).limit(limit).all()
    return {
        "runs_count": len(runs),
        "runs": [
            {
                "id": r.id,
                "validation_id": r.validation_id,
                "validation_type": r.validation_type,
                "start_date": r.start_date.isoformat(),
                "end_date": r.end_date.isoformat(),
                "reference_source": r.reference_source,
                "index_method": r.index_method,
                "our_mean_index": r.our_mean_index,
                "reference_mean_value": r.reference_mean_value,
                "mae": r.mae,
                "mape": r.mape,
                "rmse": r.rmse,
                "pearson_corr": r.pearson_corr,
                "sample_size": r.sample_size,
                "coverage_percent": r.coverage_percent,
                "methodology_version": r.methodology_version,
                "created_at": r.created_at.isoformat(),
                "metadata": r.metadata_json
            }
            for r in runs
        ]
    }
