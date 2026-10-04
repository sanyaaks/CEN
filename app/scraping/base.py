import time
import random
import logging
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)


# -------------------------------------------------------------
# Scraper Specific Exceptions for Controlled Failure Recovery
# -------------------------------------------------------------
class ScraperError(Exception):
    """Base exception for scraping operations."""
    pass


class ScraperTimeoutError(ScraperError):
    """Raised when a remote source times out."""
    pass


class ScraperRateLimitError(ScraperError):
    """Raised when remote endpoint returns HTTP 429 or excessive request rejection."""
    pass


class ScraperBlockedError(ScraperError):
    """Raised when remote endpoint returns HTTP 403 or access restriction."""
    pass


class ScraperNoResultError(ScraperError):
    """Raised when no flights exist for given route/date (sold out or unavailable)."""
    pass


class BaseScraper(ABC):
    """
    Common Scraper Contract (Phase 2 Standard Interface).
    Enforces standardized output schemas, ethical rate-limiting, bounded retries,
    polite User-Agent handling, and non-evasion graceful failure.
    """

    def __init__(
        self,
        name: str,
        source_type: str = "AGGREGATOR",
        min_delay_sec: Optional[float] = None,
        max_delay_sec: Optional[float] = None,
        timeout_sec: Optional[int] = None,
        max_retries: Optional[int] = None
    ):
        self.name = name
        self.source_type = source_type
        self.min_delay_sec = min_delay_sec if min_delay_sec is not None else settings.SCRAPER_MIN_DELAY_SEC
        self.max_delay_sec = max_delay_sec if max_delay_sec is not None else settings.SCRAPER_MAX_DELAY_SEC
        self.timeout_sec = timeout_sec if timeout_sec is not None else settings.SCRAPER_REQUEST_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else settings.SCRAPER_MAX_RETRIES

    def get_headers(self) -> Dict[str, str]:
        """
        Returns polite, standard HTTP headers.
        Uses identifiable bot User-Agent by default.
        """
        return {
            "User-Agent": settings.SCRAPER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive"
        }

    def get_random_headers(self) -> Dict[str, str]:
        """Backwards compatibility alias for browser emulation."""
        return self.get_headers()

    def apply_rate_limit(self):
        """Applies a polite random delay between scraper queries to prevent server load."""
        if self.min_delay_sec > 0:
            delay = random.uniform(self.min_delay_sec, self.max_delay_sec)
            time.sleep(delay)

    def create_standard_quote(
        self,
        origin: str,
        destination: str,
        travel_date: str,
        airline: str,
        total_price: float,
        flight_number: Optional[str] = None,
        plane_type: Optional[str] = None,
        departure_time: Optional[str] = None,
        arrival_time: Optional[str] = None,
        fare_class: str = "ECONOMY",
        base_fare: Optional[float] = None,
        tax: Optional[float] = None,
        gst: Optional[float] = None,
        airport_charges: Optional[float] = None,
        user_development_fee: Optional[float] = None,
        convenience_fee: Optional[float] = None,
        ancillary_fees: float = 0.0,
        currency: str = "INR",
        observation_type: str = "OBSERVED",
        fare_decomposition_status: str = "UNAVAILABLE"
    ) -> Dict[str, Any]:
        """
        Constructs a quote adhering to the standard schema contract.
        """
        return {
            "source": self.name,
            "source_type": self.source_type,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "travel_date": travel_date,
            "airline": airline,
            "flight_number": flight_number,
            "plane_type": plane_type,
            "departure_time": departure_time or f"{travel_date}T00:00:00",
            "arrival_time": arrival_time,
            "fare_class": fare_class,
            "base_fare": base_fare,
            "tax": tax,
            "gst": gst,
            "airport_charges": airport_charges,
            "user_development_fee": user_development_fee,
            "convenience_fee": convenience_fee,
            "ancillary_fees": ancillary_fees,
            "total_price": float(total_price),
            "currency": currency,
            "observation_type": observation_type,
            "fare_decomposition_status": fare_decomposition_status
        }

    @abstractmethod
    def search(
        self,
        origin: str,
        destination: str,
        travel_date: datetime.date,
        passengers: int = 1,
        cabin_class: str = "ECONOMY"
    ) -> List[Dict[str, Any]]:
        """
        Common search method returning standard quote dictionaries.
        """
        pass

    def fetch_quotes(
        self,
        origin: str,
        destination: str,
        departure_date: datetime.date
    ) -> List[Dict[str, Any]]:
        """
        Standard alias wrapping search(...) for backward compatibility.
        """
        return self.search(origin, destination, departure_date)
