import uuid
import logging
import datetime
import time
from typing import List, Optional
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.db import SessionLocal
from app.models.db_models import ScrapeRun
from app.scraping.flight_client import FlightClient
from app.scraping.raw_store import RawStore
from app.processing.normalize import FareNormalizer
from app.processing.outliers import OutlierDetector
from app.processing.index_engine import IndexEngine

logger = logging.getLogger(__name__)


class ScrapeScheduler:
    """
    Coordinates matrix scraping across configured routes & booking horizons,
    records comprehensive scrape run execution metadata in Neon PostgreSQL,
    normalizes raw flight quotes, removes statistical outliers, and generates price index values.
    Supports standalone execution and continuous cron scheduling via APScheduler.
    """

    def __init__(
        self,
        routes: Optional[List[str]] = None,
        horizons: Optional[List[int]] = None
    ):
        self.routes = routes or settings.routes_list
        self.horizons = horizons or settings.horizons_list
        self.flight_client = FlightClient()
        self.raw_store = RawStore()
        self.normalizer = FareNormalizer()
        self.outlier_detector = OutlierDetector()
        self.index_engine = IndexEngine()
        self.scheduler: Optional[BackgroundScheduler] = None

    def run_matrix_scrape(
        self,
        db: Optional[Session] = None,
        target_date: Optional[datetime.date] = None
    ) -> dict:
        """
        Executes one full sweep across Route x Horizon matrix:
        Routes: DEL-BOM, BLR-DEL, HYD-MAA, DEL-MAA, BOM-BLR, DEL-CCU
        Horizons: T+1, T+7, T+15, T+30, T+45
        """
        if not settings.ENABLE_GOOGLE_FLIGHTS and not settings.ENABLE_OTA_GATEWAY and not settings.ENABLE_PLAYWRIGHT:
            logger.warning("All scraping sources are disabled. Skipping scrape cycle.")
            return {"status": "SKIPPED", "message": "All scraper sources disabled."}

        close_db_on_exit = False
        if db is None:
            db = SessionLocal()
            close_db_on_exit = True

        today = target_date or datetime.date.today()
        run_uuid = f"run_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        start_time = time.time()
        start_dt = datetime.datetime.utcnow()

        logger.info(f"Starting Scrape Run [{run_uuid}] for base date: {today}")

        # Initialize ScrapeRun record
        scrape_run = ScrapeRun(
            run_id=run_uuid,
            started_at=start_dt,
            status="STARTED",
            attempted=len(self.routes) * len(self.horizons),
            successful=0,
            records_collected=0,
            records_rejected=0,
            error_count=0,
            duration_seconds=0.0
        )
        db.add(scrape_run)
        db.commit()
        db.refresh(scrape_run)

        scraped_raw_records = []
        errors_logged = []

        try:
            for route_str in self.routes:
                parts = route_str.split("-")
                if len(parts) != 2:
                    logger.warning(f"Invalid route format: {route_str}, skipping.")
                    continue
                origin, destination = parts[0].strip().upper(), parts[1].strip().upper()

                for horizon in self.horizons:
                    travel_date = today + datetime.timedelta(days=horizon)
                    try:
                        logger.info(f"Scraping {route_str} @ T+{horizon} days ({travel_date})...")
                        payload = self.flight_client.fetch_flights(
                            origin=origin,
                            destination=destination,
                            departure_date=travel_date
                        )
                        raw_rec = self.raw_store.store_raw_response(
                            db=db,
                            origin=origin,
                            destination=destination,
                            travel_date=travel_date,
                            booking_horizon_days=horizon,
                            raw_payload=payload,
                            source=payload.get("source_used", "google_flights")
                        )
                        scraped_raw_records.append(raw_rec)
                        scrape_run.successful += 1
                        scrape_run.records_collected += payload.get("count", 0)
                        time.sleep(0.2)
                    except Exception as e:
                        err_msg = f"{route_str}_T+{horizon}: {str(e)}"
                        logger.error(f"Error scraping {err_msg}")
                        errors_logged.append(err_msg)
                        scrape_run.error_count += 1

            # 1. Normalize newly scraped records
            clean_count = self.normalizer.process_raw_fares(db, scraped_raw_records)

            # 2. Flag outliers with Z-score > 3 sigma
            outlier_ids = self.outlier_detector.flag_outliers_for_route(db)

            # 3. Compute Dutot, Jevons, and DGCA-weighted indices
            index_records = self.index_engine.compute_indices_for_date(db, target_date=today)

            # Finalize ScrapeRun Record
            end_time = time.time()
            scrape_run.completed_at = datetime.datetime.utcnow()
            scrape_run.duration_seconds = round(end_time - start_time, 2)
            scrape_run.status = "SUCCESS" if scrape_run.error_count == 0 else ("PARTIAL" if scrape_run.successful > 0 else "FAILED")
            scrape_run.error_message = "; ".join(errors_logged[:5]) if errors_logged else None
            scrape_run.metadata_json = {
                "clean_fares_created": clean_count,
                "outliers_flagged": len(outlier_ids),
                "indices_generated": len(index_records),
                "routes": self.routes,
                "horizons": self.horizons
            }
            db.commit()

            summary = {
                "run_id": run_uuid,
                "status": scrape_run.status,
                "base_date": today.isoformat(),
                "duration_seconds": scrape_run.duration_seconds,
                "routes": self.routes,
                "horizons": self.horizons,
                "raw_records_scraped": len(scraped_raw_records),
                "clean_fares_created": clean_count,
                "outliers_flagged": len(outlier_ids),
                "indices_generated": len(index_records)
            }
            logger.info(f"Matrix scrape run [{run_uuid}] completed successfully: {summary}")
            return summary

        except Exception as e:
            db.rollback()
            scrape_run.completed_at = datetime.datetime.utcnow()
            scrape_run.status = "FAILED"
            scrape_run.error_message = str(e)
            scrape_run.duration_seconds = round(time.time() - start_time, 2)
            db.commit()
            raise e

        finally:
            if close_db_on_exit:
                db.close()

    def start_scheduler(self):
        """
        Initializes and starts the APScheduler background cron job with non-overlapping constraints.
        """
        if self.scheduler and self.scheduler.running:
            return

        self.scheduler = BackgroundScheduler()
        cron_parts = settings.SCRAPE_SCHEDULE_CRON.split()
        if len(cron_parts) == 5:
            minute, hour, day, month, day_of_week = cron_parts
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
        else:
            trigger = CronTrigger(hour=2, minute=0)

        self.scheduler.add_job(
            self.run_matrix_scrape,
            trigger=trigger,
            id="daily_airfare_matrix_scrape",
            name="Daily Airfare Index Scrape Pipeline",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300
        )
        self.scheduler.start()
        logger.info(f"Scraper scheduler started with cron schedule: {settings.SCRAPE_SCHEDULE_CRON}")

    def stop_scheduler(self):
        """Stops the APScheduler background worker safely."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scraper scheduler stopped.")
