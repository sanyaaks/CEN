"""
AI-Powered Flight Scraper Agent using browser-use and Browser Use Cloud/Local SDK.
Autonomous AI agent that searches airline booking portals and direct airline websites
(IndiGo, Air India, Akasa Air, EaseMyTrip, MakeMyTrip, Google Flights)
and extracts structured airfare price quotes for Project CEN (MoSPI Airfare Index).
"""

import asyncio
import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load local environment variables (.env) from root and app directories
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Fallback explicit check from app/.env if os.environ is empty
if not os.getenv("BROWSER_USE_API_KEY"):
    app_env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(app_env_path):
        with open(app_env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("BROWSER_USE_API_KEY="):
                    val = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                    os.environ["BROWSER_USE_API_KEY"] = val
                    break

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BrowserUseFlightAgent")


class FlightQuoteResult(BaseModel):
    airline: str = Field(description="Airline name, e.g. IndiGo, Air India, SpiceJet, Akasa Air")
    flight_number: Optional[str] = Field(None, description="Flight code e.g. 6E-2134, AI-805")
    origin: str = Field(description="3-letter IATA origin airport code e.g. DEL, BOM, BLR")
    destination: str = Field(description="3-letter IATA destination airport code e.g. BOM, BLR, MAA")
    departure_time: Optional[str] = Field(None, description="Departure time e.g. 06:15")
    arrival_time: Optional[str] = Field(None, description="Arrival time e.g. 08:30")
    price_inr: int = Field(description="Total one-way base economy fare in Indian Rupees (INR), e.g. 4850")
    is_non_stop: bool = Field(True, description="True if direct flight without layover")
    source: str = Field("browser-use-agent", description="Scraping source identifier")


class FlightExtractionOutput(BaseModel):
    flights: List[FlightQuoteResult] = Field(default_factory=list, description="List of observed flight quotes")
    total_found: int = Field(0, description="Total flights observed")
    route: str = Field("", description="Route e.g. DEL-BOM")
    departure_date: str = Field("", description="Date in YYYY-MM-DD format")


TARGET_PORTALS = {
    "google_flights": {
        "name": "Google Flights (All Carriers Aggregator)",
        "url": "https://www.google.com/travel/flights",
        "instructions": "Navigate to Google Flights, search one-way flights, and extract up to 10 economy flights across all Indian airlines."
    },
    "indigo": {
        "name": "IndiGo Official Portal (goindigo.in)",
        "url": "https://www.goindigo.in",
        "instructions": "Navigate to IndiGo website (https://www.goindigo.in), select One-Way flight, search for the route on the given date, and extract flight numbers and lowest economy fares."
    },
    "airindia": {
        "name": "Air India Official Portal (airindia.com)",
        "url": "https://www.airindia.com",
        "instructions": "Navigate to Air India website (https://www.airindia.com), search for one-way economy flights for the route on the date, and extract available flight quotes."
    },
    "easemytrip": {
        "name": "EaseMyTrip Portal (easemytrip.com)",
        "url": "https://www.easemytrip.com",
        "instructions": "Navigate to EaseMyTrip (https://www.easemytrip.com), search one-way flight from origin to destination on the departure date, and extract flight details and prices."
    },
    "akasaair": {
        "name": "Akasa Air Official Portal (akasaair.com)",
        "url": "https://www.akasaair.com",
        "instructions": "Navigate to Akasa Air website (https://www.akasaair.com), search for one-way flights on the route and date, and extract the fare options."
    }
}


def check_environment() -> dict:
    """Check and display available browser-use tools and API keys."""
    keys = {
        "BROWSER_USE_API_KEY": bool(os.getenv("BROWSER_USE_API_KEY")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
    }
    return keys


def save_flights_to_database(flights: List[FlightQuoteResult], origin: str, destination: str, dep_date_str: str, portal_source: str = "browser-use-ai"):
    """
    Saves the extracted browser-use quotes into PostgreSQL (Neon DB)
    so they immediately populate /audit, /collection, /routes, and the live Dashboard.
    """
    try:
        from app.db import SessionLocal
        from app.models.db_models import RawFare, CleanFare

        db = SessionLocal()
        travel_dt = datetime.strptime(dep_date_str, "%Y-%m-%d")
        now = datetime.utcnow()
        horizon_days = max(0, (travel_dt.date() - now.date()).days)
        route_str = f"{origin}-{destination}"

        # 1. Save Raw Payload in RawFare table (Audit Trail)
        payload_data = [f.model_dump() if hasattr(f, "model_dump") else dict(f) for f in flights]
        raw_bytes = json.dumps(payload_data, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha256(raw_bytes + str(now.timestamp()).encode("utf-8")).hexdigest()

        raw_fare_entry = RawFare(
            timestamp=now,
            source=portal_source,
            origin=origin,
            destination=destination,
            travel_date=travel_dt,
            booking_horizon_days=horizon_days,
            raw_payload={"quotes": payload_data},
            payload_hash=payload_hash,
        )
        db.add(raw_fare_entry)
        db.flush()

        # 2. Save Normalized Observations into CleanFare table
        saved_count = 0
        for f in flights:
            al = getattr(f, "airline", "") or (f.get("airline", "") if isinstance(f, dict) else "Airline")
            fn = getattr(f, "flight_number", None) or (f.get("flight_number") if isinstance(f, dict) else None)
            pr = getattr(f, "price_inr", 0) or (f.get("price_inr", 0) if isinstance(f, dict) else 0)
            dep = getattr(f, "departure_time", "") or (f.get("departure_time", "") if isinstance(f, dict) else "")
            arr = getattr(f, "arrival_time", "") or (f.get("arrival_time", "") if isinstance(f, dict) else "")

            clean_entry = CleanFare(
                source_raw_fare_id=raw_fare_entry.id,
                route=route_str,
                date=travel_dt,
                horizon=horizon_days,
                airline=al,
                flight_number=fn,
                departure_time=dep,
                arrival_time=arr,
                base_fare=float(pr),
                fuel_surcharge=0.0,
                airport_fee=0.0,
                user_dev_fee=0.0,
                gst=0.0,
                other_taxes=0.0,
                total_fare=float(pr),
                observation_type="OBSERVED",
                fare_decomposition_status="UNAVAILABLE",
                source=portal_source,
            )
            db.add(clean_entry)
            saved_count += 1

        db.commit()
        db.close()
        logger.info(f"💾 Successfully saved {saved_count} live quotes into Neon PostgreSQL database!")
        print(f"\n💾 Database Ingestion: {saved_count} quotes saved to PostgreSQL (Live on Dashboard & /collection)!")
    except Exception as e:
        logger.warning(f"Database ingestion notice (optional): {e}")


async def scrape_flights_with_browser_use(
    origin: str = "DEL",
    destination: str = "BOM",
    departure_date: Optional[str] = None,
    portal: str = "google_flights",
) -> FlightExtractionOutput:
    """
    Launches an autonomous Browser Use AI agent to search live flight prices directly from airline portals.
    Available portals: 'google_flights', 'indigo', 'airindia', 'easemytrip', 'akasaair'
    """
    if not departure_date:
        departure_date = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")

    api_key = os.getenv("BROWSER_USE_API_KEY")

    portal_info = TARGET_PORTALS.get(portal, TARGET_PORTALS["google_flights"])
    portal_name = portal_info["name"]
    portal_instructions = portal_info["instructions"]

    task_prompt = f"""
    You are an automated price intelligence agent for Project CEN (MoSPI, Government of India).
    
    GOAL:
    1. {portal_instructions}
    2. Search ONE-WAY economy flights from {origin} to {destination} on departure date {departure_date}.
    3. Look at the flight search results and extract available flight options.
    4. For each flight, extract:
       - Airline Name (IndiGo, Air India, SpiceJet, Akasa Air, etc.)
       - Flight Number (e.g. 6E 6047, AI 2951)
       - Departure Time (e.g. 11:00 AM)
       - Arrival Time (e.g. 1:15 PM)
       - Price in Indian Rupees (INR) as an integer (e.g. 6425)
       - Non-stop status (true/false)
    5. Return valid structured flight quotes.
    """

    if api_key:
        logger.info(f"🌐 Using Browser Use Cloud SDK on target: {portal_name}...")
        from browser_use_sdk import AsyncBrowserUse

        async with AsyncBrowserUse(api_key=api_key) as client:
            logger.info(f"🚀 Dispatching autonomous task for {origin}->{destination} on {departure_date}...")
            task_run = await client.run(
                task=task_prompt,
                output_schema=FlightExtractionOutput,
            )
            logger.info(f"✅ Cloud Task Finished! Status: {task_run.status if hasattr(task_run, 'status') else 'Completed'}")
            return task_run
    else:
        logger.info(f"🖥️ Using Local Browser Use Agent on target: {portal_name}...")
        from browser_use import Agent

        # Check for local LLM keys
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        llm = None
        if openai_key:
            try:
                import importlib
                ChatOpenAI = importlib.import_module("langchain_openai").ChatOpenAI
                llm = ChatOpenAI(model="gpt-4o", api_key=openai_key)
            except (ImportError, Exception) as e:
                logger.warning(f"Could not initialize langchain_openai: {e}")
        elif gemini_key:
            try:
                import importlib
                ChatGoogleGenerativeAI = importlib.import_module("langchain_google_genai").ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key)
            except (ImportError, Exception) as e:
                logger.warning(f"Could not initialize langchain_google_genai: {e}")
        
        agent = Agent(
            task=task_prompt,
            llm=llm,
        )
        logger.info("🤖 Starting local browser agent...")
        history = await agent.run()
        logger.info("✅ Local Agent execution finished!")
        return history


async def main():
    # Configure your target route, date, and portal
    origin = "DEL"
    destination = "BOM"
    dep_date = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")
    target_portal = "google_flights"  # Options: 'google_flights', 'indigo', 'airindia', 'easemytrip', 'akasaair'

    print("\n" + "="*70)
    print("✈️  PROJECT CEN — AUTONOMOUS AIRLINE WEB SCRAPER AGENT")
    print(f"📍 Route:    {origin} -> {destination}")
    print(f"📅 Date:     {dep_date}")
    print(f"🌐 Target:   {TARGET_PORTALS.get(target_portal, {}).get('name', target_portal)}")
    print("="*70)

    # 1. Diagnostic Environment Check
    print("\n🔍 1. Checking Environment & API Keys:")
    env_status = check_environment()
    for key, present in env_status.items():
        status_icon = "✅ Configured" if present else "❌ Not set"
        print(f"   • {key:<22}: {status_icon}")

    if not any(env_status.values()):
        print("\n⚠️  Notice: No AI API key found in your .env file.")
        print("   To run the autonomous agent, add one of the following to your .env file:")
        print("   1) BROWSER_USE_API_KEY=bu_...   (for Browser Use Cloud)")
        print("   2) OPENAI_API_KEY=sk-...        (for GPT-4o Local Agent)")
        print("   3) GEMINI_API_KEY=AIzaSy...     (for Google Gemini Local Agent)")
        print("\n" + "="*70 + "\n")
        return

    # 2. Run Scraping Agent
    print(f"\n🚀 2. Launching Autonomous Scraper on {TARGET_PORTALS.get(target_portal, {}).get('name', target_portal)}...")
    try:
        result = await scrape_flights_with_browser_use(
            origin=origin,
            destination=destination,
            departure_date=dep_date,
            portal=target_portal,
        )
        print("\n" + "="*70)
        print("🎉 SCRAPING COMPLETE! Extracted Live Airline Price Quotes:")
        print("="*70)
        
        flights = []
        if hasattr(result, "output") and hasattr(result.output, "flights"):
            flights = result.output.flights
        elif isinstance(result, dict) and "flights" in result:
            flights = result["flights"]

        if flights:
            print(f"{'Airline':<18} | {'Flight No':<10} | {'Times':<18} | {'Price (INR)':<12} | {'Non-stop'}")
            print("-" * 70)
            for f in flights:
                al = getattr(f, "airline", "") or (f.get("airline", "") if isinstance(f, dict) else "")
                fn = getattr(f, "flight_number", "N/A") or (f.get("flight_number", "N/A") if isinstance(f, dict) else "N/A")
                dep = getattr(f, "departure_time", "") or (f.get("departure_time", "") if isinstance(f, dict) else "")
                arr = getattr(f, "arrival_time", "") or (f.get("arrival_time", "") if isinstance(f, dict) else "")
                times = f"{dep} -> {arr}"
                pr = getattr(f, "price_inr", 0) or (f.get("price_inr", 0) if isinstance(f, dict) else 0)
                ns = "✅ Direct" if (getattr(f, "is_non_stop", True) if not isinstance(f, dict) else f.get("is_non_stop", True)) else "1-stop"
                print(f"{al:<18} | {fn:<10} | {times:<18} | ₹{pr:<11,} | {ns}")
            print("=" * 70)

            # Save to PostgreSQL Database for website visualization
            save_flights_to_database(flights, origin, destination, dep_date, portal_source=target_portal)

            # Export to structured JSON file
            json_output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scraped_flights_output.json")
            export_payload = {
                "project": "Project CEN (Bharat-APIx)",
                "authority": "Ministry of Statistics & Programme Implementation (MoSPI)",
                "scraper_engine": f"browser-use-ai ({target_portal})",
                "route": f"{origin}-{destination}",
                "departure_date": dep_date,
                "scrape_timestamp": datetime.utcnow().isoformat() + "Z",
                "total_found": len(flights),
                "currency": "INR",
                "flights": [f.model_dump() if hasattr(f, "model_dump") else dict(f) for f in flights]
            }
            with open(json_output_path, "w", encoding="utf-8") as jf:
                json.dump(export_payload, jf, indent=2)
            print(f"📄 JSON File Exported: {json_output_path}")

        else:
            print(result)

    except Exception as err:
        print(f"\n❌ Error running browser agent: {err}")


if __name__ == "__main__":
    asyncio.run(main())