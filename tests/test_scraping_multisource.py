import datetime
import pytest
from app.scraping.base import BaseScraper
from app.scraping.flight_client import (
    FlightClient,
    GoogleFlightsFastScraper,
    CalibratedFallbackScraper
)
from app.scraping.ota_client import OTAPortalScraper
from app.scraping.raw_store import RawStore


def test_base_scraper_random_headers():
    scraper = CalibratedFallbackScraper()
    headers = scraper.get_random_headers()
    assert "User-Agent" in headers
    assert "Accept-Language" in headers
    assert "AirIndexIndiaBot" in headers["User-Agent"]


def test_calibrated_fallback_scraper_quotes():
    scraper = CalibratedFallbackScraper()
    today = datetime.date.today()
    travel_date = today + datetime.timedelta(days=7)
    quotes = scraper.fetch_quotes("DEL", "BOM", travel_date)

    assert len(quotes) >= 4
    carriers = [q["airline"] for q in quotes]
    assert "IndiGo" in carriers
    assert "Air India" in carriers
    for q in quotes:
        assert q["total_price"] > 1000.0
        assert q["source"] == "calibrated_market_model"


def test_multi_source_flight_client_cascade():
    client = FlightClient(enable_playwright=False)
    today = datetime.date.today()
    travel_date = today + datetime.timedelta(days=15)
    
    result = client.fetch_flights("BLR", "DEL", travel_date)
    assert result["origin"] == "BLR"
    assert result["destination"] == "DEL"
    assert result["route"] == "BLR-DEL"
    assert result["count"] > 0
    assert len(result["flights"]) > 0
    assert result["source_used"] in ["google_flights", "ota_gateway", "calibrated_market_model"]


def test_raw_store_deterministic_hash():
    payload1 = {"origin": "DEL", "destination": "BOM", "count": 2, "flights": [{"airline": "IndiGo", "price": 4500}]}
    payload2 = {"count": 2, "destination": "BOM", "flights": [{"airline": "IndiGo", "price": 4500}], "origin": "DEL"}

    hash1 = RawStore.calculate_hash(payload1)
    hash2 = RawStore.calculate_hash(payload2)
    assert hash1 == hash2
