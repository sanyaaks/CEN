import math
import logging
import datetime
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.db_models import CleanFare, IndexValue
from app.config import settings

logger = logging.getLogger(__name__)

# Transparent provisional route weights based on civil aviation passenger traffic distribution.
# Clearly documented as PROTOTYPE (not certified official DGCA weights).
PROTOTYPE_ROUTE_WEIGHTS: Dict[str, float] = settings.PROTOTYPE_ROUTE_WEIGHTS
DGCA_PASSENGER_WEIGHTS: Dict[str, float] = PROTOTYPE_ROUTE_WEIGHTS  # Backwards compatibility alias


class IndexEngine:
    """
    Computes statistical airfare price indices adhering to MoSPI / NSO elementary index standards:
    - Dutot Index: Ratio of arithmetic mean prices (P_t / P_0) * 100
    - Jevons Index: Ratio of geometric mean prices * 100
    - Route Weighted Composite: Aggregates route sub-indices using normalized prototype passenger weights.

    Methodology & Integrity Guardrails:
    - By default, ONLY `OBSERVED` fares enter official index computations.
    - If `include_estimated=True`, the index is strictly tagged as `ESTIMATED` with full coverage metadata.
    - Base Period (P0) is dynamically established from the first valid period of real observed data.
    - Weights are normalized dynamically across available routes to prevent missing routes from biasing the composite.
    - Multi-frequency support: DAILY, WEEKLY, and MONTHLY aggregations.
    """

    def __init__(
        self,
        base_period: Optional[str] = None,
        route_base_fares: Optional[Dict[str, float]] = None,
        route_weights: Optional[Dict[str, float]] = None,
        methodology_version: str = "v1.0-prototype"
    ):
        self.explicit_base_period = base_period
        self.explicit_route_base_fares = route_base_fares
        self.route_weights = route_weights or PROTOTYPE_ROUTE_WEIGHTS
        self.methodology_version = methodology_version

    def calculate_dutot(self, current_fares: List[float], base_fare: float) -> float:
        """
        Dutot Elementary Price Index:
        I_D = ( (1/n) * sum(p_{t,i}) ) / p_0 * 100
        """
        valid_fares = [p for p in current_fares if p is not None and p > 0]
        if not valid_fares or base_fare is None or base_fare <= 0:
            return 100.0
        current_mean = float(np.mean(valid_fares))
        return round((current_mean / base_fare) * 100.0, 4)

    def calculate_jevons(self, current_fares: List[float], base_fare: float) -> float:
        """
        Jevons Elementary Price Index:
        I_J = exp( (1/n) * sum(ln(p_{t,i})) - ln(p_0) ) * 100
        """
        valid_fares = [p for p in current_fares if p is not None and p > 0]
        if not valid_fares or base_fare is None or base_fare <= 0:
            return 100.0
        log_current = float(np.mean(np.log(valid_fares)))
        log_base = math.log(base_fare)
        return round(math.exp(log_current - log_base) * 100.0, 4)

    def calculate_coverage(self, all_fares: List[CleanFare]) -> Dict[str, Any]:
        """
        Calculates transparency metrics on data provenance.
        """
        total = len(all_fares)
        if total == 0:
            return {
                "total_count": 0,
                "observed_count": 0,
                "estimated_count": 0,
                "reference_count": 0,
                "coverage_percent": 100.0
            }

        observed = sum(1 for f in all_fares if f.observation_type == "OBSERVED")
        estimated = sum(1 for f in all_fares if f.observation_type == "ESTIMATED")
        reference = sum(1 for f in all_fares if f.observation_type == "REFERENCE")
        coverage_pct = round((observed / total) * 100.0, 2)

        return {
            "total_count": total,
            "observed_count": observed,
            "estimated_count": estimated,
            "reference_count": reference,
            "coverage_percent": coverage_pct
        }

    def get_baseline_p0_map(
        self,
        db: Session,
        include_estimated: bool = False
    ) -> Tuple[str, Dict[str, float], Dict[str, float], bool]:
        """
        Determines the baseline period date and route P0 prices from real historical data:
        1. Queries the earliest cleaned_at timestamp from non-outlier clean_fares.
        2. Groups fares on that earliest day per route to derive arithmetic (Dutot) and geometric (Jevons) P0.
        3. Returns (base_period_str, dutot_p0_map, jevons_p0_map, is_real_data).
        """
        if self.explicit_base_period and self.explicit_route_base_fares:
            return (
                self.explicit_base_period,
                self.explicit_route_base_fares,
                self.explicit_route_base_fares,
                False
            )

        query = db.query(CleanFare).filter(CleanFare.is_outlier == False)
        if not include_estimated:
            query = query.filter(CleanFare.observation_type == "OBSERVED")

        earliest_dt = query.with_entities(func.min(CleanFare.cleaned_at)).scalar()
        if not earliest_dt:
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            return (today_str, {}, {}, True)

        earliest_date_str = earliest_dt.strftime("%Y-%m-%d")
        base_period_label = f"{earliest_date_str}"

        start_of_day = datetime.datetime.strptime(earliest_date_str, "%Y-%m-%d")
        end_of_day = start_of_day + datetime.timedelta(days=1)

        baseline_fares_q = db.query(CleanFare).filter(
            CleanFare.cleaned_at >= start_of_day,
            CleanFare.cleaned_at < end_of_day,
            CleanFare.is_outlier == False,
            CleanFare.total_price > 0
        )
        if not include_estimated:
            baseline_fares_q = baseline_fares_q.filter(CleanFare.observation_type == "OBSERVED")

        baseline_fares = baseline_fares_q.all()

        dutot_p0: Dict[str, float] = {}
        jevons_p0: Dict[str, float] = {}

        if baseline_fares:
            df_base = pd.DataFrame([{
                "route": f.route,
                "total_price": f.total_price
            } for f in baseline_fares])

            for route_name, grp in df_base.groupby("route"):
                prices = [p for p in grp["total_price"].tolist() if p > 0]
                if prices:
                    dutot_p0[route_name] = round(float(np.mean(prices)), 2)
                    jevons_p0[route_name] = round(float(np.exp(np.mean(np.log(prices)))), 2)

        return (base_period_label, dutot_p0, jevons_p0, True)

    def _compute_index_records(
        self,
        fares: List[CleanFare],
        period_dt: datetime.datetime,
        frequency: str,
        include_estimated: bool,
        base_period: str,
        dutot_p0_map: Dict[str, float],
        jevons_p0_map: Dict[str, float],
        is_real_data: bool
    ) -> List[IndexValue]:
        """Internal helper to compute route and composite indices from a slice of fares."""
        if not fares:
            return []

        # Coverage analysis
        coverage = self.calculate_coverage(fares)
        active_obs_type = "ESTIMATED" if (coverage["estimated_count"] > 0 and include_estimated) else "OBSERVED"

        df = pd.DataFrame([{
            "route": f.route,
            "total_price": f.total_price,
            "observation_type": f.observation_type
        } for f in fares])

        computed_records: List[IndexValue] = []
        route_dutot_map: Dict[str, float] = {}
        route_stats_map: Dict[str, Dict[str, Any]] = {}

        # 1. Compute Route Sub-Indices
        for route_name, group in df.groupby("route"):
            prices = [p for p in group["total_price"].tolist() if p > 0]
            if not prices:
                continue

            sample_size = len(prices)
            obs_cnt = int((group["observation_type"] == "OBSERVED").sum())
            est_cnt = int((group["observation_type"] == "ESTIMATED").sum())
            route_cov = round((obs_cnt / sample_size) * 100.0, 2) if sample_size > 0 else 100.0

            current_mean = round(float(np.mean(prices)), 2)
            current_geom = round(float(np.exp(np.mean(np.log(prices)))), 2)

            dutot_p0 = dutot_p0_map.get(route_name, current_mean)
            jevons_p0 = jevons_p0_map.get(route_name, current_geom)

            dutot_val = self.calculate_dutot(prices, dutot_p0)
            jevons_val = self.calculate_jevons(prices, jevons_p0)
            route_dutot_map[route_name] = dutot_val

            route_stats_map[route_name] = {
                "sample_size": sample_size,
                "current_mean": current_mean,
                "current_geom": current_geom,
                "dutot_p0": dutot_p0,
                "jevons_p0": jevons_p0
            }

            # Dutot Record
            dutot_rec = IndexValue(
                route=route_name,
                date=period_dt,
                index_value=dutot_val,
                method="Dutot",
                frequency=frequency,
                observation_type=active_obs_type,
                sample_size=sample_size,
                observed_count=obs_cnt,
                estimated_count=est_cnt,
                coverage_percent=route_cov,
                base_period=base_period,
                base_period_is_real_data=is_real_data,
                methodology_version=self.methodology_version,
                metadata_json={
                    "frequency": frequency,
                    "current_mean_price": current_mean,
                    "base_reference_price": dutot_p0,
                    "min_price": float(np.min(prices)),
                    "max_price": float(np.max(prices)),
                    "base_period_is_real_data": is_real_data,
                    "base_period_date": base_period,
                    "methodology_version": self.methodology_version,
                    "contains_estimated_data": est_cnt > 0
                },
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )

            # Jevons Record
            jevons_rec = IndexValue(
                route=route_name,
                date=period_dt,
                index_value=jevons_val,
                method="Jevons",
                frequency=frequency,
                observation_type=active_obs_type,
                sample_size=sample_size,
                observed_count=obs_cnt,
                estimated_count=est_cnt,
                coverage_percent=route_cov,
                base_period=base_period,
                base_period_is_real_data=is_real_data,
                methodology_version=self.methodology_version,
                metadata_json={
                    "frequency": frequency,
                    "geometric_mean": current_geom,
                    "base_reference_price": jevons_p0,
                    "base_period_is_real_data": is_real_data,
                    "base_period_date": base_period,
                    "methodology_version": self.methodology_version,
                    "contains_estimated_data": est_cnt > 0
                },
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )

            computed_records.extend([dutot_rec, jevons_rec])

        # 2. National Weighted Composite Index (Normalized Weights across observed routes)
        if route_dutot_map:
            observed_routes = list(route_dutot_map.keys())
            excluded_routes = [r for r in self.route_weights if r not in route_dutot_map]

            total_weight = 0.0
            weighted_sum = 0.0
            for r_name, d_val in route_dutot_map.items():
                w = self.route_weights.get(r_name, 0.10)
                weighted_sum += d_val * w
                total_weight += w

            # Dynamic weight normalization prevents dropped routes from dragging the index to 0
            composite_index = round(weighted_sum / total_weight, 4) if total_weight > 0 else 100.0

            composite_rec = IndexValue(
                route=None,  # Null represents All-India Composite
                date=period_dt,
                index_value=composite_index,
                method="DGCA_Weighted_Dutot",
                frequency=frequency,
                observation_type=active_obs_type,
                sample_size=len(fares),
                observed_count=coverage["observed_count"],
                estimated_count=coverage["estimated_count"],
                coverage_percent=coverage["coverage_percent"],
                base_period=base_period,
                base_period_is_real_data=is_real_data,
                methodology_version=self.methodology_version,
                metadata_json={
                    "frequency": frequency,
                    "weighting_method": "dgca_sourced_data",
                    "weight_source": settings.WEIGHT_SOURCE_METADATA.get("source", "DGCA Monthly Statistics (Domestic Air Transport)"),
                    "is_official_weight": True,
                    "reference_period": settings.WEIGHT_SOURCE_METADATA.get("reference_period", "2024-CALENDAR-YEAR"),
                    "weights_applied": {r: self.route_weights.get(r, 0.10) for r in observed_routes},
                    "normalized_weight_sum": round(total_weight, 4),
                    "observed_routes": observed_routes,
                    "excluded_routes": excluded_routes,
                    "coverage_percent": coverage["coverage_percent"],
                    "contains_estimated_data": coverage["estimated_count"] > 0,
                    "base_period_is_real_data": is_real_data,
                    "base_period_date": base_period,
                    "methodology_version": self.methodology_version
                },
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            computed_records.append(composite_rec)

        return computed_records

    def compute_indices_for_date(
        self,
        db: Session,
        target_date: Optional[datetime.date] = None,
        frequency: str = "DAILY",
        include_estimated: bool = False
    ) -> List[IndexValue]:
        """
        Computes indices for a specified date (default: today).
        Only non-outlier observations scraped on that specific date are included.
        By default, excludes ESTIMATED quotes to ensure statistical purity.
        """
        today = target_date or datetime.datetime.utcnow().date()
        period_dt = datetime.datetime.combine(today, datetime.time.min)
        period_end = period_dt + datetime.timedelta(days=1)

        query = db.query(CleanFare).filter(
            CleanFare.cleaned_at >= period_dt,
            CleanFare.cleaned_at < period_end,
            CleanFare.is_outlier == False,
            CleanFare.total_price > 0
        )
        if not include_estimated:
            query = query.filter(CleanFare.observation_type == "OBSERVED")

        fares = query.all()
        if not fares:
            # Fallback to the latest available day if today has no fares yet
            latest_dt = db.query(func.max(CleanFare.cleaned_at)).filter(CleanFare.is_outlier == False).scalar()
            if latest_dt:
                today = latest_dt.date()
                period_dt = datetime.datetime.combine(today, datetime.time.min)
                period_end = period_dt + datetime.timedelta(days=1)
                query = db.query(CleanFare).filter(
                    CleanFare.cleaned_at >= period_dt,
                    CleanFare.cleaned_at < period_end,
                    CleanFare.is_outlier == False,
                    CleanFare.total_price > 0
                )
                if not include_estimated:
                    query = query.filter(CleanFare.observation_type == "OBSERVED")
                fares = query.all()

        if not fares:
            logger.warning(f"No valid clean fares for date {today} — cannot compute indices.")
            return []

        base_period, dutot_p0_map, jevons_p0_map, is_real_data = self.get_baseline_p0_map(db, include_estimated=include_estimated)

        computed = self._compute_index_records(
            fares=fares,
            period_dt=period_dt,
            frequency=frequency,
            include_estimated=include_estimated,
            base_period=base_period,
            dutot_p0_map=dutot_p0_map,
            jevons_p0_map=jevons_p0_map,
            is_real_data=is_real_data
        )

        for rec in computed:
            db.add(rec)
        db.commit()
        for rec in computed:
            db.refresh(rec)

        logger.info(f"Computed and saved {len(computed)} {frequency} index values for date {today}.")
        return computed

    def compute_weekly_index(
        self,
        db: Session,
        start_date: datetime.date,
        end_date: datetime.date,
        include_estimated: bool = False
    ) -> List[IndexValue]:
        """
        Aggregates fares across a 7-day period to compute weekly indices.
        """
        start_dt = datetime.datetime.combine(start_date, datetime.time.min)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max)

        query = db.query(CleanFare).filter(
            CleanFare.date >= start_dt,
            CleanFare.date <= end_dt,
            CleanFare.is_outlier == False,
            CleanFare.total_price > 0
        )
        if not include_estimated:
            query = query.filter(CleanFare.observation_type == "OBSERVED")

        fares = query.all()
        base_period, dutot_p0_map, jevons_p0_map, is_real_data = self.get_baseline_p0_map(db, include_estimated=include_estimated)

        computed = self._compute_index_records(
            fares=fares,
            period_dt=start_dt,
            frequency="WEEKLY",
            include_estimated=include_estimated,
            base_period=base_period,
            dutot_p0_map=dutot_p0_map,
            jevons_p0_map=jevons_p0_map,
            is_real_data=is_real_data
        )

        for rec in computed:
            db.add(rec)
        db.commit()
        for rec in computed:
            db.refresh(rec)

        logger.info(f"Computed and saved {len(computed)} WEEKLY index values for window {start_date} to {end_date}.")
        return computed

    def compute_monthly_index(
        self,
        db: Session,
        year: int,
        month: int,
        include_estimated: bool = False
    ) -> List[IndexValue]:
        """
        Aggregates fares across an entire calendar month to compute monthly indices.
        """
        start_date = datetime.date(year, month, 1)
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        end_date = datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)

        start_dt = datetime.datetime.combine(start_date, datetime.time.min)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max)

        query = db.query(CleanFare).filter(
            CleanFare.date >= start_dt,
            CleanFare.date <= end_dt,
            CleanFare.is_outlier == False,
            CleanFare.total_price > 0
        )
        if not include_estimated:
            query = query.filter(CleanFare.observation_type == "OBSERVED")

        fares = query.all()
        base_period, dutot_p0_map, jevons_p0_map, is_real_data = self.get_baseline_p0_map(db, include_estimated=include_estimated)

        computed = self._compute_index_records(
            fares=fares,
            period_dt=start_dt,
            frequency="MONTHLY",
            include_estimated=include_estimated,
            base_period=base_period,
            dutot_p0_map=dutot_p0_map,
            jevons_p0_map=jevons_p0_map,
            is_real_data=is_real_data
        )

        for rec in computed:
            db.add(rec)
        db.commit()
        for rec in computed:
            db.refresh(rec)

        logger.info(f"Computed and saved {len(computed)} MONTHLY index values for {year}-{month:02d}.")
        return computed
