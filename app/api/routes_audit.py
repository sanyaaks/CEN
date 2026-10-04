import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models.db_models import RawFare, CleanFare, ScrapeRun
from app.scraping.registry import registry
from app.scraping.health import health_tracker
from app.api.cache import api_cache

router = APIRouter(prefix="/audit", tags=["Data Provenance & Audit Trail"])


@router.get("/")
@router.get("", include_in_schema=False)
def get_audit_summary(db: Session = Depends(get_db)):
    """
    GET /audit: Returns system-wide statistical audit summary including raw-to-clean ratios,
    outlier exclusion rates, and fare decomposition status breakdown.
    """
    cache_key = "audit_summary"
    cached = api_cache.get(cache_key)
    if cached:
        return cached

    # 1. Total Raw Scrapes count
    total_raw = db.query(func.count(RawFare.id)).scalar() or 0

    # 2. Single high-performance combined query for clean fares statistics
    clean_stats = db.execute(text("""
        SELECT 
            COUNT(*) as total_clean,
            COUNT(*) FILTER (WHERE observation_type = 'OBSERVED') as total_observed,
            COUNT(*) FILTER (WHERE observation_type = 'ESTIMATED') as total_estimated,
            COUNT(*) FILTER (WHERE is_outlier = true) as total_outliers,
            COUNT(*) FILTER (WHERE fare_decomposition_status = 'EXACT') as exact_decomp,
            COUNT(*) FILTER (WHERE fare_decomposition_status = 'PARTIAL') as partial_decomp,
            COUNT(*) FILTER (WHERE fare_decomposition_status = 'UNAVAILABLE') as unavail_decomp
        FROM clean_fares
    """)).fetchone()

    total_clean = clean_stats[0] or 0
    total_observed = clean_stats[1] or 0
    total_estimated = clean_stats[2] or 0
    total_outliers = clean_stats[3] or 0
    exact_cnt = clean_stats[4] or 0
    partial_cnt = clean_stats[5] or 0
    unavail_cnt = clean_stats[6] or 0

    # 3. Fetch recent raw scrapes with eager loading of quotes to prevent N+1 queries
    recent_raw = (
        db.query(RawFare)
        .options(selectinload(RawFare.clean_fares))
        .order_by(RawFare.timestamp.desc())
        .limit(15)
        .all()
    )

    result = {
        "summary": {
            "total_raw_scrapes": total_raw,
            "total_clean_observations": total_clean,
            "total_observed_quotes": total_observed,
            "total_estimated_quotes": total_estimated,
            "observed_coverage_pct": round((total_observed / total_clean * 100.0), 2) if total_clean > 0 else 100.0,
            "total_outliers_flagged": total_outliers,
            "outlier_rate_pct": round((total_outliers / total_clean * 100.0), 2) if total_clean > 0 else 0.0,
            "fare_decomposition_breakdown": {
                "exact": exact_cnt,
                "partial": partial_cnt,
                "unavailable": unavail_cnt
            }
        },
        "recent_scrapes": [
            {
                "raw_id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "source": r.source,
                "origin": r.origin,
                "destination": r.destination,
                "travel_date": r.travel_date.isoformat(),
                "booking_horizon_days": r.booking_horizon_days,
                "payload_hash": r.payload_hash,
                "quotes_count": len(r.clean_fares) if r.clean_fares else 0
            }
            for r in recent_raw
        ]
    }

    api_cache.set(cache_key, result, ttl_sec=15)
    return result


@router.get("/sources/health")
def get_sources_health():
    """
    GET /audit/sources/health: Returns real-time health, response time, and consecutive
    failure metrics for all registered data sources.
    """
    all_sources = registry.list_all_sources()
    live_health = health_tracker.get_all_health()

    report = []
    for src in all_sources:
        name = src["source_name"]
        health_info = live_health.get(name, {
            "status": "HEALTHY" if src["enabled"] else "DISABLED",
            "last_success": None,
            "last_failure": None,
            "consecutive_failures": 0,
            "total_queries": 0,
            "successful_queries": 0,
            "total_quotes_collected": 0,
            "last_error": None,
            "last_response_time_ms": 0.0
        })
        report.append({
            "source_name": name,
            "source_type": src["source_type"],
            "enabled": src["enabled"],
            "priority": src["priority"],
            "is_fallback_model": src["is_fallback_model"],
            "compliance_status": src["compliance_status"],
            "health": health_info
        })

    return {
        "sources_count": len(report),
        "sources": report
    }


@router.get("/runs")
def get_scrape_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    GET /audit/runs: Returns chronological scrape execution run logs.
    """
    cache_key = f"scrape_runs_{limit}"
    cached = api_cache.get(cache_key)
    if cached:
        return cached

    runs = db.query(ScrapeRun).order_by(ScrapeRun.started_at.desc()).limit(limit).all()
    res = {
        "runs_count": len(runs),
        "runs": [
            {
                "id": r.id,
                "run_id": r.run_id,
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "status": r.status,
                "source": r.source,
                "route": r.route,
                "horizon": r.horizon,
                "attempted": r.attempted,
                "successful": r.successful,
                "records_collected": r.records_collected,
                "records_rejected": r.records_rejected,
                "error_count": r.error_count,
                "error_message": r.error_message,
                "duration_seconds": r.duration_seconds,
                "metadata": r.metadata_json
            }
            for r in runs
        ]
    }
    api_cache.set(cache_key, res, ttl_sec=15)
    return res


@router.get("/{route}")
def get_route_audit_lineage(
    route: str,
    only_outliers: bool = Query(False, description="Filter solely to outlier flagged observations"),
    db: Session = Depends(get_db)
):
    """
    GET /audit/{route}: Returns full provenance audit trail for individual clean observations on a route.
    """
    query = db.query(CleanFare).filter(CleanFare.route == route)
    if only_outliers:
        query = query.filter(CleanFare.is_outlier == True)

    fares = query.order_by(CleanFare.date.asc(), CleanFare.horizon.asc()).all()

    if not fares:
        raise HTTPException(status_code=404, detail=f"No audit observations found for corridor {route}")

    total_count = len(fares)
    observed_count = sum(1 for f in fares if f.observation_type == "OBSERVED")
    estimated_count = sum(1 for f in fares if f.observation_type == "ESTIMATED")
    outlier_count = sum(1 for f in fares if f.is_outlier)

    records = []
    for f in fares:
        raw_fare_parent = f.raw_fare
        records.append({
            "clean_fare_id": f.id,
            "route": f.route,
            "travel_date": f.date.isoformat(),
            "horizon_days": f.horizon,
            "airline": f.airline,
            "flight_number": f.flight_number,
            "observation_type": f.observation_type,
            "fare_decomposition_status": f.fare_decomposition_status,
            "total_price": f.total_price,
            "base_fare": f.base_fare,
            "tax": f.tax,
            "gst": f.gst,
            "tax_estimated": f.tax_estimated,
            "ancillary_fees_dropped": f.ancillary_fees,
            "is_outlier": f.is_outlier,
            "outlier_reason": f.outlier_reason,
            "outlier_score": f.outlier_score,
            "cleaned_at": f.cleaned_at.isoformat(),
            "lineage": {
                "source_raw_fare_id": f.source_raw_fare_id,
                "scrape_timestamp": raw_fare_parent.timestamp.isoformat() if raw_fare_parent else None,
                "source_engine": raw_fare_parent.source if raw_fare_parent else None,
                "sha256_payload_hash": raw_fare_parent.payload_hash if raw_fare_parent else None
            }
        })

    return {
        "route": route,
        "sample_count": total_count,
        "observed_count": observed_count,
        "estimated_count": estimated_count,
        "outlier_count": outlier_count,
        "observations": records
    }
