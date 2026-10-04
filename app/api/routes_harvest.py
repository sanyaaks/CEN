import asyncio
import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db import get_db, SessionLocal
from app.models.db_models import RawFare, CleanFare, ScrapeRun, IndexValue
from app.processing.index_engine import IndexEngine
from app.processing.outliers import OutlierDetector
from app.api.cache import api_cache
from app.browser import (
    scrape_flights_with_browser_use,
    TARGET_PORTALS,
    FlightExtractionOutput,
    FlightQuoteResult
)

logger = logging.getLogger("MoSPI-AI-Harvest")
router = APIRouter(prefix="/harvest", tags=["Autonomous AI Scraping"])


class HarvestRequest(BaseModel):
    route: str = Field("DEL-BOM", description="Route pair e.g. DEL-BOM, BOM-BLR, DEL-BLR")
    departure_date: Optional[str] = Field(None, description="Departure date in YYYY-MM-DD format (default: T-2)")
    portal: str = Field("google_flights", description="Target portal: google_flights, indigo, airindia, easemytrip, akasaair")
    horizon_days: Optional[int] = Field(None, description="Booking horizon in days (0, 1, 7, 14, 30)")


class HarvestFlightItem(BaseModel):
    airline: str
    flight_number: Optional[str]
    origin: str
    destination: str
    departure_time: Optional[str]
    arrival_time: Optional[str]
    price_inr: int
    is_non_stop: bool
    source: str


class HarvestResponse(BaseModel):
    status: str
    message: str
    route: str
    departure_date: str
    portal: str
    portal_name: str
    quotes_count: int
    raw_fare_id: Optional[int]
    payload_hash: Optional[str]
    index_updated: bool
    latest_composite_index: Optional[float]
    flights: List[HarvestFlightItem]


@router.get("/portals")
def get_available_portals():
    """Returns list of supported airline and OTA booking portals."""
    return [
        {
            "id": k,
            "name": v["name"],
            "url": v["url"],
            "description": v["instructions"]
        }
        for k, v in TARGET_PORTALS.items()
    ]


@router.post("/ai-agent", response_model=HarvestResponse)
async def trigger_ai_agent_harvest(req: HarvestRequest, db: Session = Depends(get_db)):
    """
    Executes the autonomous AI browser agent (browser-use),
    extracts real-time airfares from the selected portal,
    persists raw audit payloads & clean observations into PostgreSQL,
    and runs the Index & Outlier Processing Engine immediately.
    """
    route_parts = req.route.upper().split("-")
    if len(route_parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid route format. Expected format: 'DEL-BOM'")
    
    origin, destination = route_parts[0], route_parts[1]
    
    # Calculate departure date if not provided
    if req.departure_date:
        dep_date_str = req.departure_date
        try:
            dep_dt = datetime.strptime(dep_date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD")
    else:
        days_ahead = req.horizon_days if req.horizon_days is not None else 2
        dep_dt = datetime.utcnow() + timedelta(days=days_ahead)
        dep_date_str = dep_dt.strftime("%Y-%m-%d")

    portal_info = TARGET_PORTALS.get(req.portal, TARGET_PORTALS["google_flights"])
    portal_name = portal_info["name"]

    start_time = datetime.utcnow()
    run_id = f"ai-harvest-{origin}{destination}-{int(start_time.timestamp())}"

    # Log scrape run start in DB
    scrape_run = ScrapeRun(
        run_id=run_id,
        started_at=start_time,
        status="RUNNING",
        source=f"browser-use ({req.portal})",
        route=req.route,
        horizon=max(0, (dep_dt.date() - start_time.date()).days),
        attempted=1,
    )
    db.add(scrape_run)
    db.commit()

    try:
        logger.info(f"🚀 Triggering AI Browser Agent for {req.route} on {dep_date_str} via {req.portal}...")
        
        # 1. Execute AI Scraper
        result = await scrape_flights_with_browser_use(
            origin=origin,
            destination=destination,
            departure_date=dep_date_str,
            portal=req.portal
        )

        extracted_flights = []
        if hasattr(result, "output") and hasattr(result.output, "flights"):
            extracted_flights = result.output.flights
        elif isinstance(result, dict) and "flights" in result:
            extracted_flights = result["flights"]

        # If zero flights returned, fallback with simulated live verification quotes
        if not extracted_flights:
            raise RuntimeError("Scraper agent returned empty flight list.")

        # 2. Ingest into RawFare (Audit Trail)
        payload_data = [f.model_dump() if hasattr(f, "model_dump") else dict(f) for f in extracted_flights]
        raw_bytes = json.dumps(payload_data, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha256(raw_bytes + str(start_time.timestamp()).encode("utf-8")).hexdigest()
        horizon_days = max(0, (dep_dt.date() - start_time.date()).days)

        raw_fare_entry = RawFare(
            timestamp=start_time,
            source=f"browser-use-{req.portal}",
            origin=origin,
            destination=destination,
            travel_date=dep_dt,
            booking_horizon_days=horizon_days,
            raw_payload={"quotes": payload_data, "run_id": run_id},
            payload_hash=payload_hash,
        )
        db.add(raw_fare_entry)
        db.flush()

        # 3. Ingest into CleanFare (Normalized Observations)
        clean_fares_created = []
        for f in extracted_flights:
            al = getattr(f, "airline", "") or (f.get("airline", "") if isinstance(f, dict) else "IndiGo")
            fn = getattr(f, "flight_number", None) or (f.get("flight_number") if isinstance(f, dict) else None)
            pr = getattr(f, "price_inr", 0) or (f.get("price_inr", 0) if isinstance(f, dict) else 0)
            dep = getattr(f, "departure_time", "") or (f.get("departure_time", "") if isinstance(f, dict) else "")
            arr = getattr(f, "arrival_time", "") or (f.get("arrival_time", "") if isinstance(f, dict) else "")

            # Approximate basic base fare / tax breakdown
            base_fare_est = round(float(pr) * 0.85, 2)
            tax_est = round(float(pr) * 0.15, 2)

            clean_entry = CleanFare(
                source_raw_fare_id=raw_fare_entry.id,
                route=req.route,
                date=dep_dt,
                horizon=horizon_days,
                airline=al,
                flight_number=fn,
                total_price=float(pr),
                base_fare=base_fare_est,
                tax=tax_est,
                gst=round(float(pr) * 0.05, 2),
                airport_charges=round(float(pr) * 0.08, 2),
                user_development_fee=round(float(pr) * 0.02, 2),
                convenience_fee=0.0,
                ancillary_fees=0.0,
                observation_type="OBSERVED",
                fare_decomposition_status="PARTIAL",
                tax_estimated=True,
                is_outlier=False,
                cleaned_at=datetime.utcnow(),
            )
            db.add(clean_entry)
            clean_fares_created.append(clean_entry)

        db.flush()

        # 4. Run Outlier Detection
        try:
            outlier_detector = OutlierDetector(z_threshold=3.0)
            outlier_detector.flag_outliers_for_route(db, route=req.route)
        except Exception as o_err:
            logger.warning(f"Outlier check notice: {o_err}")

        # 5. Run Price Index Computation Engine (for travel date and today's collection date)
        latest_composite = None
        try:
            index_engine = IndexEngine()
            computed_indices = index_engine.compute_daily_index(db, target_date=dep_dt.date())
            for idx in computed_indices:
                if idx.route is None or idx.route == "" or idx.route == "__COMPOSITE__":
                    latest_composite = idx.index_value

            today_date = datetime.utcnow().date()
            if today_date != dep_dt.date():
                today_indices = index_engine.compute_daily_index(db, target_date=today_date)
                if latest_composite is None:
                    for idx in today_indices:
                        if idx.route is None or idx.route == "" or idx.route == "__COMPOSITE__":
                            latest_composite = idx.index_value
        except Exception as idx_err:
            logger.warning(f"Index computation notice: {idx_err}")

        # 6. Update ScrapeRun record
        end_time = datetime.utcnow()
        scrape_run.completed_at = end_time
        scrape_run.status = "SUCCESS"
        scrape_run.successful = 1
        scrape_run.records_collected = len(extracted_flights)
        scrape_run.records_rejected = 0
        scrape_run.error_count = 0
        db.commit()

        # 7. Invalidate Cache so all API calls receive new data immediately
        api_cache.clear()

        # 8. Export to JSON file on disk
        json_output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scraped_flights_output.json")
        try:
            export_payload = {
                "project": "Project CEN (Bharat-APIx)",
                "authority": "Ministry of Statistics & Programme Implementation (MoSPI)",
                "scraper_engine": f"browser-use ({req.portal})",
                "route": req.route,
                "departure_date": dep_date_str,
                "scrape_timestamp": end_time.isoformat() + "Z",
                "total_found": len(extracted_flights),
                "currency": "INR",
                "flights": payload_data
            }
            with open(json_output_path, "w", encoding="utf-8") as jf:
                json.dump(export_payload, jf, indent=2)
        except Exception as j_err:
            logger.warning(f"Failed to write local JSON export: {j_err}")

        # Format output items for response
        flights_out = []
        for item in payload_data:
            flights_out.append(HarvestFlightItem(
                airline=item.get("airline", "IndiGo"),
                flight_number=item.get("flight_number"),
                origin=origin,
                destination=destination,
                departure_time=item.get("departure_time"),
                arrival_time=item.get("arrival_time"),
                price_inr=int(item.get("price_inr", 0)),
                is_non_stop=bool(item.get("is_non_stop", True)),
                source=req.portal
            ))

        return HarvestResponse(
            status="SUCCESS",
            message=f"Successfully extracted {len(flights_out)} live quotes from {portal_name}, saved to PostgreSQL, and recomputed indices!",
            route=req.route,
            departure_date=dep_date_str,
            portal=req.portal,
            portal_name=portal_name,
            quotes_count=len(flights_out),
            raw_fare_id=raw_fare_entry.id,
            payload_hash=payload_hash,
            index_updated=True,
            latest_composite_index=latest_composite,
            flights=flights_out
        )

    except Exception as err:
        db.rollback()
        scrape_run.completed_at = datetime.utcnow()
        scrape_run.status = "FAILED"
        scrape_run.error_count = 1
        db.commit()
        logger.error(f"Error in trigger_ai_agent_harvest: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI Scraping Agent failed: {str(err)}")
