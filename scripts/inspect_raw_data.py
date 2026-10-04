#!/usr/bin/env python3
"""
Inspects the raw scraped data stored in the RawFare table.
Outputs id, route, travel_date, horizon, source, timestamp, and a sample of
parsed flight quotes to verify real Google Flights ingestion.
"""

import sys
import os
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import init_db, SessionLocal
from app.models.db_models import RawFare


def inspect_raw_fares(limit: int = 100, preview_flights_count: int = 5):
    init_db()
    db = SessionLocal()
    try:
        raw_records = db.query(RawFare).order_by(RawFare.id.asc()).all()
        total_count = len(raw_records)
        
        print("=" * 80)
        print(f"  RAW FARE AUDIT INSPECTION (Total Batches: {total_count})")
        print("=" * 80)

        if not raw_records:
            print("No raw scrape records found in database.")
            return

        for r in raw_records[:limit]:
            route_str = f"{r.origin}-{r.destination}"
            travel_str = r.travel_date.strftime("%Y-%m-%d") if r.travel_date else "N/A"
            ts_str = r.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if r.timestamp else "N/A"
            payload = r.raw_payload or {}
            flights = payload.get("flights", [])
            total_flights = payload.get("count", len(flights))

            print(f"\n[RawFare ID: {r.id}]")
            print(f"  - Route               : {route_str} ({r.origin} -> {r.destination})")
            print(f"  - Travel Date         : {travel_str}")
            print(f"  - Booking Horizon     : T+{r.booking_horizon_days} days")
            print(f"  - Source Provider     : {r.source}")
            print(f"  - Ingested Timestamp  : {ts_str}")
            print(f"  - Payload SHA256 Hash : {r.payload_hash}")
            print(f"  - Total Quotes Found  : {total_flights}")
            print(f"  - Sample Raw Quotes (showing first {min(preview_flights_count, len(flights))} of {len(flights)}):")

            for idx, fl in enumerate(flights[:preview_flights_count], 1):
                airline = fl.get("airline", "Unknown")
                fno = fl.get("flight_number") or "N/A"
                plane = fl.get("plane_type") or "N/A"
                dep = fl.get("departure_time", "N/A")
                arr = fl.get("arrival_time", "N/A")
                price = fl.get("total_price", fl.get("price", 0.0))
                base_f = fl.get("base_fare", 0.0)
                tax = fl.get("tax", 0.0)
                
                print(f"    [{idx}] {airline:<16} | Flt: {fno:<6} | Plane: {plane:<16} | Dep: {dep:<19} | Arr: {arr:<19} | Price: INR {price:,.2f} (Base: {base_f:,.2f} + Tax: {tax:,.2f})")

        print("\n" + "=" * 80)
        print(f"Audit Summary: {total_count} raw scrape batches verified.")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    inspect_raw_fares()
