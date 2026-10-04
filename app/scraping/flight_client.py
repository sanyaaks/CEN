import time
import logging
import datetime
import random
from typing import Dict, Any, List, Optional
import fast_flights

from app.scraping.base import (
    BaseScraper,
    ScraperError,
    ScraperTimeoutError,
    ScraperRateLimitError,
    ScraperBlockedError,
    ScraperNoResultError
)
from app.scraping.playwright_scraper import PlaywrightFlightScraper
from app.scraping.ota_client import OTAPortalScraper
from app.scraping.validator import IngestionValidator
from app.scraping.health import health_tracker
from app.scraping.registry import registry, SourceMetadata
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleFlightsFastScraper(BaseScraper):
    """
    Primary fast aggregator scraper wrapping fast-flights for Google Flights.
    Produces OBSERVED quotes with fare_decomposition_status=UNAVAILABLE.
    """

    def __init__(self, currency: str = "INR"):
        super().__init__(
            name="google_flights",
            source_type="AGGREGATOR",
            min_delay_sec=settings.SCRAPER_MIN_DELAY_SEC,
            max_delay_sec=settings.SCRAPER_MAX_DELAY_SEC,
            timeout_sec=settings.SCRAPER_REQUEST_TIMEOUT,
            max_retries=settings.SCRAPER_MAX_RETRIES
        )
        self.currency = currency

    def search(
        self,
        origin: str,
        destination: str,
        travel_date: datetime.date,
        passengers: int = 1,
        cabin_class: str = "ECONOMY"
    ) -> List[Dict[str, Any]]:
        date_str = travel_date.strftime("%Y-%m-%d")
        quotes: List[Dict[str, Any]] = []

        self.apply_rate_limit()
        query = fast_flights.create_query(
            flights=[
                fast_flights.FlightQuery(
                    date=date_str,
                    from_airport=origin.upper(),
                    to_airport=destination.upper()
                )
            ],
            trip="one-way",
            currency=self.currency
        )
        result = fast_flights.get_flights(query)

        for item in result:
            airlines = getattr(item, "airlines", [])
            airline_name = ", ".join(airlines) if airlines else "Unknown Airline"
            price = getattr(item, "price", None)
            if price is None:
                continue

            sub_flights = getattr(item, "flights", [])
            flight_no = getattr(item, "type", "FLIGHT")
            dep_iso = f"{date_str}T00:00:00"
            arr_iso = None
            plane_type = None

            if sub_flights and len(sub_flights) > 0:
                first_seg = sub_flights[0]
                plane_type = getattr(first_seg, "plane_type", None)
                dep_dt = getattr(first_seg, "departure", None)
                if dep_dt and hasattr(dep_dt, "date") and hasattr(dep_dt, "time"):
                    d_tuple, t_tuple = dep_dt.date, dep_dt.time
                    dep_iso = f"{d_tuple[0]:04d}-{d_tuple[1]:02d}-{d_tuple[2]:02d}T{t_tuple[0]:02d}:{t_tuple[1]:02d}:00"

                arr_dt = getattr(first_seg, "arrival", None)
                if arr_dt and hasattr(arr_dt, "date") and hasattr(arr_dt, "time"):
                    a_d, a_t = arr_dt.date, arr_dt.time
                    arr_iso = f"{a_d[0]:04d}-{a_d[1]:02d}-{a_d[2]:02d}T{a_t[0]:02d}:{a_t[1]:02d}:00"

            quotes.append(
                self.create_standard_quote(
                    origin=origin,
                    destination=destination,
                    travel_date=date_str,
                    airline=airline_name,
                    flight_number=flight_no,
                    plane_type=plane_type,
                    departure_time=dep_iso,
                    arrival_time=arr_iso,
                    fare_class=cabin_class,
                    total_price=float(price),
                    currency=self.currency,
                    observation_type="OBSERVED",
                    fare_decomposition_status="UNAVAILABLE"
                )
            )

        return quotes


class CalibratedFallbackScraper(BaseScraper):
    """
    High-fidelity realistic market pricing generator used when all live network
    sources are rate-limited or in offline environments.
    Strictly classified as ESTIMATED with explicit calibration provenance.
    """

    def __init__(self, estimated_reason: str = "SOURCE_UNAVAILABLE"):
        super().__init__(
            name="calibrated_market_model",
            source_type="MODEL",
            min_delay_sec=0.0,
            max_delay_sec=0.0
        )
        self.estimated_reason = estimated_reason
        self.model_version = "v1.0-market-elasticity"

    def search(
        self,
        origin: str,
        destination: str,
        travel_date: datetime.date,
        passengers: int = 1,
        cabin_class: str = "ECONOMY"
    ) -> List[Dict[str, Any]]:
        date_str = travel_date.strftime("%Y-%m-%d")
        quotes: List[Dict[str, Any]] = []

        route_key = f"{origin.upper()}-{destination.upper()}"
        base_route_fares = {
            "DEL-BOM": 4800.0,
            "BLR-DEL": 5200.0,
            "HYD-MAA": 3600.0,
            "DEL-CCU": 4900.0,
            "DEL-MAA": 5400.0,
            "BOM-BLR": 3800.0
        }
        ref_fare = base_route_fares.get(route_key, 4500.0)

        # Booking advance horizon elasticity
        days_ahead = (travel_date - datetime.date.today()).days
        if days_ahead <= 1:
            horizon_multiplier = 1.35  # T+1 price surge
        elif days_ahead <= 7:
            horizon_multiplier = 1.15  # T+7
        elif days_ahead <= 15:
            horizon_multiplier = 1.00  # T+15
        elif days_ahead <= 30:
            horizon_multiplier = 0.90  # T+30
        else:
            horizon_multiplier = 0.82  # T+45

        # Day of week variation (weekends slightly higher)
        dow_multiplier = 1.08 if travel_date.weekday() in (4, 5, 6) else 0.98

        carriers = [
            ("IndiGo", "6E-", 0.96),
            ("Air India", "AI-", 1.05),
            ("Vistara", "UK-", 1.10),
            ("Akasa Air", "QP-", 0.92),
            ("SpiceJet", "SG-", 0.90),
            ("Air India Express", "IX-", 0.93)
        ]

        for carrier, prefix, carrier_mult in carriers:
            f_no = f"{prefix}{random.randint(101, 999)}"
            price = round(ref_fare * horizon_multiplier * dow_multiplier * carrier_mult, 2)
            quotes.append(
                self.create_standard_quote(
                    origin=origin,
                    destination=destination,
                    travel_date=date_str,
                    airline=carrier,
                    flight_number=f_no,
                    plane_type="Airbus A320neo / Boeing 737 MAX",
                    departure_time=f"{date_str}T{random.randint(6, 21):02d}:{random.choice([0, 15, 30, 45]):02d}:00",
                    arrival_time=f"{date_str}T{random.randint(8, 23):02d}:00:00",
                    fare_class=cabin_class,
                    total_price=price,
                    observation_type="ESTIMATED",
                    fare_decomposition_status="UNAVAILABLE"
                )
            )

        return quotes


# -------------------------------------------------------------
# Register All Scraper Adapters in Global Registry
# -------------------------------------------------------------
registry.register(SourceMetadata(
    source_name="google_flights",
    source_type="AGGREGATOR",
    scraper_class=GoogleFlightsFastScraper,
    enabled=settings.ENABLE_GOOGLE_FLIGHTS,
    priority=1,
    description="Fast aggregator interface querying public Google Flights schedules."
))

registry.register(SourceMetadata(
    source_name="ota_gateway",
    source_type="OTA",
    scraper_class=OTAPortalScraper,
    enabled=settings.ENABLE_OTA_GATEWAY,
    priority=2,
    description="Direct HTTP gateway collector targeting domestic OTA flight list feeds."
))

registry.register(SourceMetadata(
    source_name="playwright_headless",
    source_type="BROWSER",
    scraper_class=PlaywrightFlightScraper,
    enabled=settings.ENABLE_PLAYWRIGHT,
    priority=3,
    description="Headless Chromium browser collector for JavaScript-rendered price matrixes."
))

registry.register(SourceMetadata(
    source_name="calibrated_market_model",
    source_type="MODEL",
    scraper_class=CalibratedFallbackScraper,
    enabled=settings.ENABLE_FALLBACK_ESTIMATES,
    priority=4,
    is_fallback_model=True,
    description="Statistical fallback generator for pipeline continuity when network is unreachable."
))


class FlightClient:
    """
    Unified Multi-Source Flight Client (Phase 2).
    Orchestrates the scraper cascade across the Source Registry with explicit
    observation_type tagging, ingestion validation, and real-time health monitoring.
    """

    def __init__(self, currency: str = "INR", enable_playwright: bool = True):
        self.currency = currency
        self.enable_playwright = enable_playwright

    def fetch_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime.date
    ) -> Dict[str, Any]:
        date_str = departure_date.strftime("%Y-%m-%d")
        logger.info(f"Initiating multi-source scrape for {origin}->{destination} on {date_str}...")

        flights_list: List[Dict[str, Any]] = []
        active_source = "none"
        active_obs_type = "OBSERVED"
        failure_log: List[Dict[str, str]] = []

        sources = registry.get_enabled_sources_by_priority()

        for source_meta in sources:
            # Respect enable_playwright override if passed
            if source_meta.source_name == "playwright_headless" and not self.enable_playwright:
                continue

            t_start = time.time()
            try:
                scraper = source_meta.scraper_class()
                raw_quotes = scraper.search(origin, destination, departure_date)
                t_elapsed_ms = (time.time() - t_start) * 1000.0

                if raw_quotes:
                    # Ingestion validation
                    valid_quotes = []
                    for q in raw_quotes:
                        is_valid, reason = IngestionValidator.validate_quote(q)
                        if is_valid:
                            valid_quotes.append(q)
                        else:
                            logger.debug(f"Ingestion rejected invalid quote: {reason}")

                    if valid_quotes:
                        flights_list = valid_quotes
                        active_source = source_meta.source_name
                        active_obs_type = "ESTIMATED" if source_meta.is_fallback_model else "OBSERVED"
                        health_tracker.record_success(active_source, len(valid_quotes), t_elapsed_ms)
                        logger.info(f"Source [{active_source}] successfully returned {len(valid_quotes)} quotes in {t_elapsed_ms:.1f}ms.")
                        break
                    else:
                        health_tracker.record_failure(source_meta.source_name, "ALL_QUOTES_REJECTED_BY_VALIDATOR", t_elapsed_ms)
                else:
                    health_tracker.record_failure(source_meta.source_name, "NO_QUOTES_RETURNED", t_elapsed_ms)
                    failure_log.append({"source": source_meta.source_name, "reason": "NO_QUOTES_RETURNED"})

            except Exception as e:
                t_elapsed_ms = (time.time() - t_start) * 1000.0
                err_msg = str(e)
                health_tracker.record_failure(source_meta.source_name, err_msg, t_elapsed_ms)
                failure_log.append({"source": source_meta.source_name, "reason": err_msg})
                logger.warning(f"Source [{source_meta.source_name}] query failed: {err_msg}")

        # If all sources failed and fallback was disabled, return empty
        return {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "route": f"{origin.upper()}-{destination.upper()}",
            "travel_date": date_str,
            "currency": self.currency,
            "source_used": active_source,
            "observation_type": active_obs_type,
            "count": len(flights_list),
            "flights": flights_list,
            "failures": failure_log
        }
