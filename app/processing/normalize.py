import logging
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.db_models import RawFare, CleanFare

logger = logging.getLogger(__name__)


class FareNormalizer:
    """
    Normalizes raw fare structures adhering to rigorous statistical standards:
    - Preserves total_price as the canonical, factual transaction quote.
    - Does NOT fabricate an unobserved 5% GST or tax split when the source only provides total price.
    - Explicitly sets `fare_decomposition_status`:
        * EXACT: Source provides verified itemized base fare & taxes.
        * PARTIAL: Some fare components are known.
        * UNAVAILABLE: Source provides total price only (base_fare & tax set to NULL).
    - Preserves `observation_type` (OBSERVED, ESTIMATED, or REFERENCE).
    """

    def normalize_single_flight(self, raw_fare: RawFare, flight_dict: Dict[str, Any]) -> CleanFare:
        total_price = float(flight_dict.get("total_price") or flight_dict.get("price") or 0.0)

        # 1. Observation Provenance (OBSERVED vs ESTIMATED vs REFERENCE)
        raw_payload = raw_fare.raw_payload or {}
        obs_type = (
            flight_dict.get("observation_type")
            or raw_payload.get("observation_type")
            or ("ESTIMATED" if raw_fare.source == "calibrated_market_model" else "OBSERVED")
        )

        # 2. Fare Decomposition Verification
        has_base_fare = flight_dict.get("base_fare") is not None
        has_tax = flight_dict.get("tax") is not None
        has_gst = flight_dict.get("gst") is not None
        has_airport = flight_dict.get("airport_charges") is not None

        if has_base_fare and has_tax:
            base_fare = float(flight_dict["base_fare"])
            tax = float(flight_dict["tax"])
            gst = float(flight_dict["gst"]) if has_gst else None
            airport_charges = float(flight_dict["airport_charges"]) if has_airport else None
            udf = float(flight_dict.get("user_development_fee")) if flight_dict.get("user_development_fee") is not None else None
            conv = float(flight_dict.get("convenience_fee")) if flight_dict.get("convenience_fee") is not None else None
            decomposition_status = "EXACT"
            tax_estimated = False
        elif has_base_fare or has_tax or has_gst:
            base_fare = float(flight_dict["base_fare"]) if has_base_fare else None
            tax = float(flight_dict["tax"]) if has_tax else None
            gst = float(flight_dict["gst"]) if has_gst else None
            airport_charges = float(flight_dict["airport_charges"]) if has_airport else None
            udf = float(flight_dict.get("user_development_fee")) if flight_dict.get("user_development_fee") is not None else None
            conv = float(flight_dict.get("convenience_fee")) if flight_dict.get("convenience_fee") is not None else None
            decomposition_status = "PARTIAL"
            tax_estimated = False
        else:
            # Source (e.g. Google Flights aggregator) only provides total quote.
            # Do NOT fabricate an artificial base/tax split as observed data.
            base_fare = None
            tax = None
            gst = None
            airport_charges = None
            udf = None
            conv = None
            decomposition_status = "UNAVAILABLE"
            tax_estimated = True

        # Ancillary fees (baggage, meals, seat selection) — separate from core inflation fare
        ancillary_fees = float(flight_dict.get("ancillary_fees", 0.0))

        route = f"{raw_fare.origin}-{raw_fare.destination}"

        return CleanFare(
            source_raw_fare_id=raw_fare.id,
            route=route,
            date=raw_fare.travel_date,
            horizon=raw_fare.booking_horizon_days,
            airline=flight_dict.get("airline", "Unknown"),
            flight_number=flight_dict.get("flight_number"),
            observation_type=obs_type,
            base_fare=base_fare,
            tax=tax,
            gst=gst,
            airport_charges=airport_charges,
            user_development_fee=udf,
            convenience_fee=conv,
            total_price=total_price,
            ancillary_fees=ancillary_fees,
            fare_decomposition_status=decomposition_status,
            tax_estimated=tax_estimated,
            is_outlier=False,
            outlier_reason=None,
            outlier_score=None,
            cleaned_at=datetime.datetime.utcnow()
        )

    def process_raw_fares(self, db: Session, raw_records: Optional[List[RawFare]] = None) -> int:
        """
        Processes unnormalized raw fares and writes CleanFare rows into DB.
        """
        if raw_records is None:
            # Query raw fares that haven't been cleaned yet
            cleaned_raw_ids = {r[0] for r in db.query(CleanFare.source_raw_fare_id).distinct().all() if r[0]}
            raw_records = db.query(RawFare).filter(~RawFare.id.in_(cleaned_raw_ids)).all() if cleaned_raw_ids else db.query(RawFare).all()

        total_cleaned = 0
        for raw in raw_records:
            payload = raw.raw_payload or {}
            flights = payload.get("flights", [])
            for flight_data in flights:
                clean_fare = self.normalize_single_flight(raw, flight_data)
                db.add(clean_fare)
                total_cleaned += 1

        db.commit()
        logger.info(f"Successfully normalized {total_cleaned} clean fares from {len(raw_records)} raw records.")
        return total_cleaned
