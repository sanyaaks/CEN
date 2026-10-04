import logging
import datetime
from typing import Dict, Any, List, Optional
import requests
from app.scraping.base import BaseScraper, ScraperTimeoutError, ScraperBlockedError, ScraperRateLimitError
from app.config import settings

logger = logging.getLogger(__name__)


class OTAPortalScraper(BaseScraper):
    """
    Direct HTTP Scraper targeting domestic OTA public search gateways
    with standard headers, respectful delay, and session timeouts.
    """

    def __init__(self, timeout_sec: Optional[int] = None):
        super().__init__(
            name="ota_gateway",
            source_type="OTA",
            min_delay_sec=settings.SCRAPER_MIN_DELAY_SEC,
            max_delay_sec=settings.SCRAPER_MAX_DELAY_SEC,
            timeout_sec=timeout_sec or settings.SCRAPER_REQUEST_TIMEOUT,
            max_retries=settings.SCRAPER_MAX_RETRIES
        )

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
        headers = self.get_headers()
        headers.update({
            "Origin": "https://www.easemytrip.com",
            "Referer": "https://www.easemytrip.com/flights.html",
            "Accept": "application/json, text/plain, */*"
        })

        session = requests.Session()
        session.headers.update(headers)

        probe_url = f"https://flight.easemytrip.com/FlightApi/GetFlightList?org={origin.upper()}&dest={destination.upper()}&date={date_str}"
        logger.info(f"[OTA Gateway] Querying flight availability for {origin}->{destination} on {date_str}...")

        try:
            resp = session.get(probe_url, timeout=self.timeout_sec)
            if resp.status_code == 429:
                raise ScraperRateLimitError("OTA Gateway returned HTTP 429 Too Many Requests")
            if resp.status_code in (401, 403):
                raise ScraperBlockedError(f"OTA Gateway access restricted with HTTP {resp.status_code}")

            if resp.status_code == 200 and resp.text.startswith("{"):
                data = resp.json()
                flights_raw = data.get("FlightList", [])
                for fl in flights_raw:
                    airline = fl.get("AirlineName", "IndiGo")
                    f_no = fl.get("FlightNo", "")
                    price = fl.get("Fare", {}).get("GrossAmount") or fl.get("TotalFare")
                    base_p = fl.get("Fare", {}).get("BaseFare")
                    tax_p = fl.get("Fare", {}).get("Tax")

                    if price and float(price) > 0:
                        has_breakdown = base_p is not None and tax_p is not None
                        quotes.append(
                            self.create_standard_quote(
                                origin=origin,
                                destination=destination,
                                travel_date=date_str,
                                airline=airline,
                                flight_number=f_no,
                                plane_type="A320 / B737",
                                departure_time=f"{date_str}T09:00:00",
                                arrival_time=f"{date_str}T11:15:00",
                                fare_class=cabin_class,
                                base_fare=float(base_p) if has_breakdown else None,
                                tax=float(tax_p) if has_breakdown else None,
                                total_price=float(price),
                                observation_type="OBSERVED",
                                fare_decomposition_status="EXACT" if has_breakdown else "UNAVAILABLE"
                            )
                        )
        except (requests.Timeout, requests.exceptions.ReadTimeout):
            logger.warning(f"[OTA Gateway] Request timed out after {self.timeout_sec}s")
        except ScraperError as se:
            logger.warning(f"[OTA Gateway] {se}")
        except Exception as e:
            logger.warning(f"[OTA Gateway] Unreachable or returned unexpected response: {e}")
        finally:
            session.close()

        return quotes
