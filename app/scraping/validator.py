import re
import datetime
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class IngestionValidator:
    """
    Ingestion gatekeeper validating raw flight quotes before persistence.
    Ensures data consistency and prevents corrupt, non-positive, or sold-out ₹0 records from polluting storage.
    """

    AIRPORT_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")

    @classmethod
    def validate_quote(cls, quote: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates individual flight quote against basic physical & economic requirements.
        Returns (is_valid: bool, reason: str).
        """
        if not isinstance(quote, dict):
            return False, "INVALID_DATA_TYPE"

        # 1. Airport Code Validation
        origin = str(quote.get("origin", "")).strip().upper()
        destination = str(quote.get("destination", "")).strip().upper()

        if not cls.AIRPORT_CODE_PATTERN.match(origin) or not cls.AIRPORT_CODE_PATTERN.match(destination):
            return False, f"INVALID_IATA_CODES_{origin}_{destination}"

        if origin == destination:
            return False, "CIRCULAR_ROUTE_ORIGIN_EQUALS_DESTINATION"

        # 2. Travel Date Validation
        travel_date_str = str(quote.get("travel_date", "")).strip()
        try:
            travel_dt = datetime.datetime.strptime(travel_date_str, "%Y-%m-%d").date()
        except ValueError:
            return False, f"INVALID_DATE_FORMAT_{travel_date_str}"

        # 3. Price Validation (Must be strictly positive)
        price_val = quote.get("total_price")
        if price_val is None:
            return False, "MISSING_TOTAL_PRICE"

        try:
            price = float(price_val)
        except (ValueError, TypeError):
            return False, "NON_NUMERIC_TOTAL_PRICE"

        if price <= 0:
            return False, f"NON_POSITIVE_PRICE_{price}"

        # Maximum plausible domestic economy airfare ceiling (sanity check for bad OCR/parsing)
        if price > 250000.0:
            return False, f"EXCESSIVE_PRICE_SPIKE_{price}"

        # 4. Airline Validation
        airline = str(quote.get("airline", "")).strip()
        if not airline or airline.lower() == "unknown":
            return False, "MISSING_AIRLINE_IDENTITY"

        # 5. Currency Check
        currency = str(quote.get("currency", "INR")).strip().upper()
        if currency != "INR":
            return False, f"UNSUPPORTED_CURRENCY_{currency}"

        # 6. Observation Provenance Validation
        obs_type = quote.get("observation_type", "OBSERVED")
        if obs_type not in {"OBSERVED", "ESTIMATED", "REFERENCE"}:
            return False, f"INVALID_OBSERVATION_TYPE_{obs_type}"

        return True, "VALID_QUOTE"
