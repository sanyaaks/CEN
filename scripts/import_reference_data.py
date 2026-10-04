import sys
import os
import json
import csv
import argparse
import datetime
import logging
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal
from app.models.db_models import ReferenceData

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("import_reference_data")


def import_reference_records(records: List[Dict[str, Any]]) -> Dict[str, int]:
    db = SessionLocal()
    inserted = 0
    skipped = 0

    try:
        for r in records:
            ref_id = r.get("reference_id")
            source = r.get("source")
            period = r.get("reference_period")
            val = r.get("value")

            if not ref_id or not source or not period or val is None:
                logger.warning(f"Skipping malformed reference record: {r}")
                skipped += 1
                continue

            try:
                num_val = float(val)
            except (ValueError, TypeError):
                logger.warning(f"Skipping non-numeric reference value: {val}")
                skipped += 1
                continue

            existing = db.query(ReferenceData).filter(ReferenceData.reference_id == ref_id).first()
            if existing:
                skipped += 1
                continue

            pub_date = None
            if r.get("publication_date"):
                try:
                    pub_date = datetime.datetime.strptime(r["publication_date"], "%Y-%m-%d")
                except ValueError:
                    pub_date = None

            ref_obj = ReferenceData(
                reference_id=ref_id,
                source=source,
                reference_period=period,
                route=r.get("route"),
                value=num_val,
                unit=r.get("unit", "INR"),
                is_official=bool(r.get("is_official", False)),
                publication_date=pub_date,
                methodology=r.get("methodology"),
                notes=r.get("notes")
            )
            db.add(ref_obj)
            inserted += 1

        db.commit()
        logger.info(f"Reference data import complete: {inserted} inserted, {skipped} skipped.")
        return {"inserted": inserted, "skipped": skipped}

    finally:
        db.close()


def load_file_and_import(filepath: str) -> Dict[str, int]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    if filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            records = data if isinstance(data, list) else data.get("records", [])
    elif filepath.endswith(".csv"):
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    else:
        raise ValueError("Unsupported file extension. Only .json and .csv are supported.")

    return import_reference_records(records)


def seed_sample_benchmark_fixtures():
    """Seeds test benchmark records for backtesting validation."""
    sample_records = [
        {
            "reference_id": "SAMPLE_BENCH_2026_08_DEL_BOM",
            "source": "SAMPLE_BENCHMARK",
            "reference_period": "2026-08",
            "route": "DEL-BOM",
            "value": 5200.0,
            "unit": "INR",
            "is_official": False,
            "methodology": "Sample monthly average fare benchmark for automated validation tests.",
            "notes": "Test fixture only — clearly labelled non-official."
        },
        {
            "reference_id": "SAMPLE_BENCH_2026_08_BLR_DEL",
            "source": "SAMPLE_BENCHMARK",
            "reference_period": "2026-08",
            "route": "BLR-DEL",
            "value": 5600.0,
            "unit": "INR",
            "is_official": False,
            "methodology": "Sample monthly average fare benchmark for automated validation tests.",
            "notes": "Test fixture only — clearly labelled non-official."
        },
        {
            "reference_id": "SAMPLE_BENCH_2026_08_ALL_INDIA",
            "source": "SAMPLE_BENCHMARK",
            "reference_period": "2026-08",
            "route": None,
            "value": 5100.0,
            "unit": "INR",
            "is_official": False,
            "methodology": "Sample All-India monthly average fare benchmark.",
            "notes": "Test fixture only — clearly labelled non-official."
        }
    ]
    return import_reference_records(sample_records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import external reference benchmark data for backtesting.")
    parser.add_argument("--file", type=str, help="Path to CSV or JSON reference file")
    parser.add_argument("--seed-sample", action="store_true", help="Seed sample test fixture benchmarks")

    args = parser.parse_args()
    if args.seed_sample:
        res = seed_sample_benchmark_fixtures()
        print(f"Sample benchmarks seeded: {res}")
    elif args.file:
        res = load_file_and_import(args.file)
        print(f"Imported: {res}")
    else:
        parser.print_help()
