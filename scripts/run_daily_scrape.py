#!/usr/bin/env python3
"""
Manual trigger & cron execution script for running airfare matrix scraping.
Accepts optional CLI arguments:
  --route BLR-DEL
  --horizon 7
Defaults to running all configured routes across all horizons (1, 7, 15, 30, 45 days).
"""

import sys
import os
import argparse
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.db import init_db, SessionLocal
from app.scraping.scheduler import ScrapeScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("manual_scraper")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Trigger airfare scrape across routes and booking horizons.")
    parser.add_argument(
        "--route",
        type=str,
        default=None,
        help="Specific flight route to scrape (e.g., DEL-BOM, BLR-DEL). Defaults to all configured routes."
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=None,
        help="Specific booking horizon in days (e.g., 1, 7, 15, 30, 45). Defaults to all horizons."
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    # Determine routes
    if args.route:
        routes = [args.route.strip().upper()]
    else:
        routes = settings.routes_list

    # Determine horizons
    if args.horizon:
        horizons = [int(args.horizon)]
    else:
        horizons = settings.horizons_list

    logger.info("Initializing database schema...")
    init_db()

    db = SessionLocal()
    try:
        logger.info(f"Target Routes    : {routes}")
        logger.info(f"Target Horizons  : T+{horizons} days")
        
        scheduler = ScrapeScheduler(routes=routes, horizons=horizons)
        result = scheduler.run_matrix_scrape(db)
        
        print("\n" + "=" * 50)
        print("         SCRAPE EXECUTION SUMMARY")
        print("=" * 50)
        print(f"  • Base Reference Date : {result.get('base_date')}")
        print(f"  • Routes Monitored    : {', '.join(result.get('routes', []))}")
        print(f"  • Horizons (Days)     : {result.get('horizons')}")
        print(f"  • Raw Scrapes Created : {result.get('raw_records_scraped')}")
        print(f"  • Clean Observations  : {result.get('clean_fares_created')}")
        print(f"  • Outliers Flagged    : {result.get('outliers_flagged')}")
        print(f"  • Indices Computed    : {result.get('indices_generated')}")
        print("=" * 50 + "\n")
        logger.info("Scrape execution completed successfully.")
    except Exception as e:
        logger.exception(f"Fatal error during scrape execution: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
