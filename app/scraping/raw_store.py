import hashlib
import json
import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.db_models import RawFare


class RawStore:
    """
    Saves raw flight scrape responses directly to DB with metadata,
    timestamp, source, travel date, horizon, and SHA-256 hash for audit trails.
    """

    @staticmethod
    def calculate_hash(payload: Dict[str, Any]) -> str:
        """Calculates deterministic SHA-256 hash of JSON payload."""
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    def store_raw_response(
        self,
        db: Session,
        origin: str,
        destination: str,
        travel_date: datetime.date,
        booking_horizon_days: int,
        raw_payload: Dict[str, Any],
        source: str = "google_flights"
    ) -> RawFare:
        """
        Stores untouched raw payload into RawFare table.
        """
        payload_hash = self.calculate_hash(raw_payload)
        
        # Check if record with same payload hash already exists
        existing = db.query(RawFare).filter(RawFare.payload_hash == payload_hash).first()
        if existing:
            return existing

        travel_dt = datetime.datetime.combine(travel_date, datetime.time.min)
        raw_record = RawFare(
            timestamp=datetime.datetime.utcnow(),
            source=source,
            origin=origin.upper(),
            destination=destination.upper(),
            travel_date=travel_dt,
            booking_horizon_days=booking_horizon_days,
            raw_payload=raw_payload,
            payload_hash=payload_hash
        )
        db.add(raw_record)
        db.commit()
        db.refresh(raw_record)
        return raw_record
