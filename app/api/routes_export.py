import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.db_models import IndexValue

router = APIRouter(prefix="/export", tags=["MoSPI / NSO Export"])


@router.get("/")
def export_index_table(
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: csv or json"),
    method: Optional[str] = Query(None, description="Filter by method: Dutot, Jevons, DGCA_Weighted_Dutot"),
    frequency: Optional[str] = Query(None, description="Filter by frequency: DAILY, WEEKLY, MONTHLY"),
    observation_type: Optional[str] = Query(None, description="Filter by provenance: OBSERVED, ESTIMATED"),
    db: Session = Depends(get_db)
):
    """
    GET /export?format=csv|json: Dumps the IndexValue table formatted
    for official MoSPI / NSO statistical CPI integration.
    """
    query = db.query(IndexValue).order_by(IndexValue.date.asc(), IndexValue.id.asc())
    if method:
        query = query.filter(IndexValue.method == method)
    if frequency:
        query = query.filter(IndexValue.frequency == frequency)
    if observation_type:
        query = query.filter(IndexValue.observation_type == observation_type)

    indices = query.all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Standard MoSPI / COICOP Economic Statistics CSV Header
        writer.writerow([
            "index_id",
            "period_date",
            "frequency",
            "observation_type",
            "coicop_classification",
            "commodity_description",
            "route_code",
            "aggregation_formula",
            "base_period",
            "base_period_is_real_data",
            "methodology_version",
            "index_value",
            "observation_sample_size",
            "observed_count",
            "coverage_percent",
            "created_at"
        ])

        for idx in indices:
            writer.writerow([
                idx.id,
                idx.date.strftime("%Y-%m-%d"),
                getattr(idx, "frequency", "DAILY"),
                getattr(idx, "observation_type", "OBSERVED"),
                "07.3.3.1",
                "Passenger Transport by Air - Domestic Scheduled",
                idx.route or "ALL_INDIA_COMPOSITE",
                idx.method,
                idx.base_period,
                getattr(idx, "base_period_is_real_data", True),
                getattr(idx, "methodology_version", "v1.0-prototype"),
                f"{idx.index_value:.4f}",
                idx.sample_size,
                getattr(idx, "observed_count", idx.sample_size),
                f"{getattr(idx, 'coverage_percent', 100.0):.2f}%",
                idx.created_at.isoformat()
            ])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=mospi_airfare_index_series.csv"}
        )

    # JSON export format
    return {
        "dataset_name": "MoSPI Domestic Airfare Consumer Price Sub-Index (Prototype)",
        "ministry": "Ministry of Statistics and Programme Implementation",
        "coicop_item_code": "07.3.3.1",
        "methodology_version": "v1.0-prototype",
        "total_records": len(indices),
        "data": [
            {
                "id": idx.id,
                "date": idx.date.strftime("%Y-%m-%d"),
                "frequency": getattr(idx, "frequency", "DAILY"),
                "observation_type": getattr(idx, "observation_type", "OBSERVED"),
                "route": idx.route or "ALL_INDIA_COMPOSITE",
                "method": idx.method,
                "index_value": idx.index_value,
                "base_period": idx.base_period,
                "base_period_is_real_data": getattr(idx, "base_period_is_real_data", True),
                "sample_size": idx.sample_size,
                "observed_count": getattr(idx, "observed_count", idx.sample_size),
                "estimated_count": getattr(idx, "estimated_count", 0),
                "coverage_percent": getattr(idx, "coverage_percent", 100.0),
                "methodology_version": getattr(idx, "methodology_version", "v1.0-prototype"),
                "metadata": idx.metadata_json,
                "created_at": idx.created_at.isoformat()
            }
            for idx in indices
        ]
    }
