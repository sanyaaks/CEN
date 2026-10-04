import logging
from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from app.models.db_models import CleanFare

logger = logging.getLogger(__name__)


class OutlierDetector:
    """
    Flags price anomalies using Z-score statistical bounds (3 standard deviations).
    Keeps all rows intact in DB with `is_outlier = True` for auditability & lineage.
    """

    def __init__(self, z_threshold: float = 3.0):
        self.z_threshold = z_threshold

    def flag_outliers_for_route(
        self,
        db: Session,
        route: Optional[str] = None
    ) -> List[int]:
        """
        Calculates Z-scores per route & horizon grouping.
        Flags fares where |z| > z_threshold (3 standard deviations from mean).
        Returns list of flagged CleanFare IDs.
        """
        query = db.query(CleanFare)
        if route:
            query = query.filter(CleanFare.route == route)
        
        fares: List[CleanFare] = query.all()
        if not fares:
            return []

        df = pd.DataFrame([{
            "id": f.id,
            "route": f.route,
            "horizon": f.horizon,
            "total_price": f.total_price
        } for f in fares])

        flagged_fare_ids: List[int] = []

        # Group by route and horizon for relative pricing bounds
        for (r_name, h_val), group in df.groupby(["route", "horizon"]):
            if len(group) < 4:
                continue  # Skip groups with too few observations to calculate meaningful sigma

            prices = group["total_price"].values
            mean_price = np.mean(prices)
            std_price = np.std(prices)

            if std_price <= 0:
                continue

            z_scores = np.abs((prices - mean_price) / std_price)
            outlier_indices = np.where(z_scores > self.z_threshold)[0]

            for idx in outlier_indices:
                fare_id = int(group.iloc[idx]["id"])
                z_val = float(z_scores[idx])
                
                fare_rec = db.query(CleanFare).filter(CleanFare.id == fare_id).first()
                if fare_rec:
                    fare_rec.is_outlier = True
                    fare_rec.outlier_reason = f"Z-score {z_val:.2f} > {self.z_threshold} std dev (mean: {mean_price:.2f}, std: {std_price:.2f})"
                    fare_rec.outlier_score = round(z_val, 4)
                    flagged_fare_ids.append(fare_id)

        db.commit()
        logger.info(f"Outlier detection completed: flagged {len(flagged_fare_ids)} out of {len(fares)} fares.")
        return flagged_fare_ids
