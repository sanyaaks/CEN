from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models.db_models import IndexValue
from app.api.cache import api_cache

router = APIRouter(prefix="/index", tags=["Airfare Index"])


ALLOWED_METHODS = {"Dutot", "Jevons", "DGCA_Weighted_Dutot", "DGCA_Weighted_Jevons"}
ALLOWED_FREQUENCIES = {"DAILY", "WEEKLY", "MONTHLY"}
ALLOWED_OBS_TYPES = {"OBSERVED", "ESTIMATED", "REFERENCE"}


@router.get("/")
@router.get("", include_in_schema=False)
def get_latest_indices(
    method: Optional[str] = Query(None, description="Filter by method: Dutot, Jevons, DGCA_Weighted_Dutot"),
    frequency: Optional[str] = Query("DAILY", description="Filter by frequency: DAILY, WEEKLY, MONTHLY"),
    observation_type: Optional[str] = Query("OBSERVED", description="Filter by provenance: OBSERVED, ESTIMATED"),
    db: Session = Depends(get_db)
):
    """
    GET /index: Returns the latest calculated airfare inflation index per route
    as well as the national composite index.
    """
    cache_key = f"latest_indices_{method}_{frequency}_{observation_type}"
    cached = api_cache.get(cache_key)
    if cached:
        return cached
    if method and method not in ALLOWED_METHODS:
        raise HTTPException(status_code=400, detail=f"Invalid method '{method}'. Allowed: {', '.join(sorted(ALLOWED_METHODS))}")
    if frequency and frequency not in ALLOWED_FREQUENCIES:
        raise HTTPException(status_code=400, detail=f"Invalid frequency '{frequency}'. Allowed: {', '.join(sorted(ALLOWED_FREQUENCIES))}")
    if observation_type and observation_type not in ALLOWED_OBS_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid observation_type '{observation_type}'. Allowed: {', '.join(sorted(ALLOWED_OBS_TYPES))}")
    # Subquery to find maximum date per route & method (handling NULL for composite)
    subquery = (
        db.query(
            func.coalesce(IndexValue.route, '__COMPOSITE__').label("route_key"),
            IndexValue.method,
            func.max(IndexValue.date).label("max_date")
        )
        .group_by(func.coalesce(IndexValue.route, '__COMPOSITE__'), IndexValue.method)
        .subquery()
    )

    query = (
        db.query(IndexValue)
        .join(
            subquery,
            (func.coalesce(IndexValue.route, '__COMPOSITE__') == subquery.c.route_key) &
            (IndexValue.method == subquery.c.method) &
            (IndexValue.date == subquery.c.max_date)
        )
    )

    if method:
        if method == "Dutot":
            query = query.filter(IndexValue.method.in_(["Dutot", "DGCA_Weighted_Dutot"]))
        elif method == "Jevons":
            query = query.filter(IndexValue.method.in_(["Jevons", "DGCA_Weighted_Jevons"]))
        else:
            query = query.filter(IndexValue.method == method)
    if frequency:
        query = query.filter(IndexValue.frequency == frequency)
    if observation_type:
        query = query.filter(IndexValue.observation_type == observation_type)

    latest_values = query.all()

    # Fallback to general query if strict filters returned no rows (backward compatibility)
    if not latest_values:
        q_fallback = db.query(IndexValue).join(
            subquery,
            (IndexValue.route == subquery.c.route) &
            (IndexValue.method == subquery.c.method) &
            (IndexValue.date == subquery.c.max_date)
        )
        if method:
            q_fallback = q_fallback.filter(IndexValue.method == method)
        latest_values = q_fallback.all()

    res = {
        "count": len(latest_values),
        "data": [
            {
                "id": rec.id,
                "route": rec.route or "ALL_INDIA_COMPOSITE",
                "date": rec.date.strftime("%Y-%m-%d"),
                "index_value": rec.index_value,
                "method": rec.method,
                "frequency": getattr(rec, "frequency", "DAILY"),
                "observation_type": getattr(rec, "observation_type", "OBSERVED"),
                "sample_size": rec.sample_size,
                "observed_count": getattr(rec, "observed_count", rec.sample_size),
                "estimated_count": getattr(rec, "estimated_count", 0),
                "coverage_percent": getattr(rec, "coverage_percent", 100.0),
                "base_period": rec.base_period,
                "base_period_is_real_data": getattr(rec, "base_period_is_real_data", True),
                "methodology_version": getattr(rec, "methodology_version", "v1.0-prototype"),
                "created_at": rec.created_at.isoformat(),
                "metadata": rec.metadata_json
            }
            for rec in latest_values
        ]
    }
    api_cache.set(cache_key, res, ttl_sec=30)
    return res


@router.get("/{route}")
def get_route_history(
    route: str,
    method: Optional[str] = Query(None, description="Filter by method: Dutot, Jevons"),
    frequency: Optional[str] = Query(None, description="Filter by frequency: DAILY, WEEKLY, MONTHLY"),
    limit: int = Query(60, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    GET /index/{route}: Returns chronological historical index time series for a specified route (e.g. DEL-BOM).
    """
    formatted_route = route.upper().strip()
    cache_key = f"route_history_{formatted_route}_{method}_{frequency}_{limit}"
    cached = api_cache.get(cache_key)
    if cached:
        return cached

    if formatted_route in ("COMPOSITE", "NATIONAL_COMPOSITE", "ALL_INDIA_COMPOSITE", "NATIONAL"):
        query = db.query(IndexValue).filter(IndexValue.route.is_(None))
    else:
        query = db.query(IndexValue).filter(IndexValue.route == formatted_route)

    if method:
        query = query.filter(IndexValue.method == method)
    if frequency:
        query = query.filter(IndexValue.frequency == frequency)

    history = query.order_by(IndexValue.date.desc(), IndexValue.id.desc()).limit(limit).all()

    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No index history records found for route '{formatted_route}'"
        )

    res = {
        "route": formatted_route,
        "records_count": len(history),
        "history": [
            {
                "id": rec.id,
                "date": rec.date.strftime("%Y-%m-%d"),
                "index_value": rec.index_value,
                "method": rec.method,
                "frequency": getattr(rec, "frequency", "DAILY"),
                "observation_type": getattr(rec, "observation_type", "OBSERVED"),
                "sample_size": rec.sample_size,
                "observed_count": getattr(rec, "observed_count", rec.sample_size),
                "estimated_count": getattr(rec, "estimated_count", 0),
                "coverage_percent": getattr(rec, "coverage_percent", 100.0),
                "base_period": rec.base_period,
                "base_period_is_real_data": getattr(rec, "base_period_is_real_data", True),
                "methodology_version": getattr(rec, "methodology_version", "v1.0-prototype"),
                "created_at": rec.created_at.isoformat(),
                "metadata": rec.metadata_json
            }
            for rec in history
        ]
    }
    api_cache.set(cache_key, res, ttl_sec=15)
    return res
