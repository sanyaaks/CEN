import sys
import os
import argparse
import datetime
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.scraping.flight_client import FlightClient
from app.scraping.registry import registry
from app.scraping.health import health_tracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("live_scraper_test")


def run_live_test(route: str, horizon: int, source: str = None):
    print("=" * 80)
    print(f"      MANUAL LIVE SCRAPER DIAGNOSTIC TOOL")
    print("=" * 80)

    parts = route.split("-")
    if len(parts) != 2:
        print(f"Error: Route must be formatted as ORIGIN-DESTINATION (e.g., DEL-BOM). Received: {route}")
        return False

    origin, destination = parts[0].strip().upper(), parts[1].strip().upper()
    travel_date = datetime.date.today() + datetime.timedelta(days=horizon)

    print(f"• Route Target          : {origin} -> {destination}")
    print(f"• Horizon Target        : T+{horizon} days ({travel_date})")
    print(f"• Source Preference     : {source or 'Automatic Multi-Source Cascade'}")
    print("-" * 80)

    if source:
        meta = registry.get_source_metadata(source)
        if not meta:
            print(f"Error: Source '{source}' is not registered. Available: {[s['source_name'] for s in registry.list_all_sources()]}")
            return False
        scraper = meta.scraper_class()
        quotes = scraper.search(origin, destination, travel_date)
        result = {
            "origin": origin,
            "destination": destination,
            "travel_date": travel_date.strftime("%Y-%m-%d"),
            "source_used": source,
            "observation_type": "ESTIMATED" if meta.is_fallback_model else "OBSERVED",
            "count": len(quotes),
            "flights": quotes
        }
    else:
        client = FlightClient(enable_playwright=True)
        result = client.fetch_flights(origin, destination, travel_date)

    print(f"\n[RESULTS SUMMARY]")
    print(f"• Source Used           : {result.get('source_used')}")
    print(f"• Observation Type      : {result.get('observation_type')}")
    print(f"• Quotes Collected      : {result.get('count')}")

    if result.get("flights"):
        print("\n[SAMPLE QUOTES COLLECTED]")
        for i, q in enumerate(result["flights"][:5], 1):
            print(f"  {i}. {q.get('airline', 'Unknown')} | Flt: {q.get('flight_number', 'N/A')} | ₹{q.get('total_price', 0):,.2f} | Obs: {q.get('observation_type')} | Decomp: {q.get('fare_decomposition_status')}")

    print("\n[SOURCE HEALTH STATE]")
    health = health_tracker.get_all_health()
    for s_name, h in health.items():
        print(f"• {s_name:<25}: Status={h['status']}, Total={h['total_queries']}, Success={h['successful_queries']}, Failures={h['consecutive_failures']}")

    print("=" * 80)
    return result.get("count", 0) > 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live airfare scraper diagnostic tool.")
    parser.add_argument("--route", type=str, default="DEL-BOM", help="Target route e.g. DEL-BOM")
    parser.add_argument("--horizon", type=int, default=7, help="Advance booking days e.g. 7")
    parser.add_argument("--source", type=str, default=None, help="Target specific source e.g. google_flights, ota_gateway, calibrated_market_model")

    args = parser.parse_args()
    run_live_test(route=args.route, horizon=args.horizon, source=args.source)
