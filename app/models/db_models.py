import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Date, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db import Base


class RawFare(Base):
    """
    Audit trail model storing untouched raw scraped responses.
    Ensures complete statistical reproducibility and provenance.
    """
    __tablename__ = "raw_fares"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    source = Column(String(50), default="google_flights", nullable=False)
    origin = Column(String(10), index=True, nullable=False)
    destination = Column(String(10), index=True, nullable=False)
    travel_date = Column(DateTime, nullable=False, index=True)
    booking_horizon_days = Column(Integer, nullable=False, index=True)
    raw_payload = Column(JSON, nullable=False)
    payload_hash = Column(String(64), unique=True, index=True, nullable=False)

    clean_fares = relationship("CleanFare", back_populates="raw_fare", cascade="all, delete-orphan")


class CleanFare(Base):
    """
    Cleaned, normalized airfare observations with explicit data provenance:
    - observation_type: OBSERVED (actual collected price), ESTIMATED (model fallback), REFERENCE (historical benchmark)
    - fare_decomposition_status: EXACT (full itemized breakdown), PARTIAL, UNAVAILABLE (only total fare provided)
    """
    __tablename__ = "clean_fares"

    id = Column(Integer, primary_key=True, index=True)
    source_raw_fare_id = Column(Integer, ForeignKey("raw_fares.id"), nullable=True, index=True)
    route = Column(String(20), index=True, nullable=False)  # e.g., "DEL-BOM"
    date = Column(DateTime, nullable=False, index=True)  # travel_date
    horizon = Column(Integer, nullable=False, index=True)  # booking horizon days
    airline = Column(String(100), nullable=False, index=True)
    flight_number = Column(String(50), nullable=True)

    # Observation provenance
    observation_type = Column(String(20), default="OBSERVED", nullable=False, index=True,
                                comment="OBSERVED, ESTIMATED, or REFERENCE")
    
    # Fare breakdown attributes
    total_price = Column(Float, nullable=False)
    base_fare = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    gst = Column(Float, nullable=True)
    airport_charges = Column(Float, nullable=True)
    user_development_fee = Column(Float, nullable=True)
    convenience_fee = Column(Float, nullable=True)
    ancillary_fees = Column(Float, nullable=False, default=0.0)

    fare_decomposition_status = Column(String(20), default="UNAVAILABLE", nullable=False, index=True,
                                       comment="EXACT, PARTIAL, or UNAVAILABLE")
    tax_estimated = Column(Boolean, default=True, nullable=False,
                           comment="True if base_fare/tax split is estimated and not directly provided by source")

    # Outlier detection
    is_outlier = Column(Boolean, default=False, index=True)
    outlier_reason = Column(String(100), nullable=True)
    outlier_score = Column(Float, nullable=True)

    cleaned_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    raw_fare = relationship("RawFare", back_populates="clean_fares")


class IndexValue(Base):
    """
    Computed airfare price index series with statistical auditability:
    - method: Dutot, Jevons, DGCA_Weighted_Dutot
    - frequency: DAILY, WEEKLY, MONTHLY
    - observation_type: OBSERVED (default official index), ESTIMATED (contains model fallback data)
    """
    __tablename__ = "index_values"

    id = Column(Integer, primary_key=True, index=True)
    route = Column(String(20), index=True, nullable=True)  # Nullable for composite national index
    date = Column(DateTime, nullable=False, index=True)  # Period date / timestamp
    index_value = Column(Float, nullable=False)
    method = Column(String(50), default="Dutot", nullable=False, index=True)  # Dutot, Jevons, DGCA_Weighted_Dutot
    frequency = Column(String(20), default="DAILY", nullable=False, index=True)  # DAILY, WEEKLY, MONTHLY
    observation_type = Column(String(20), default="OBSERVED", nullable=False, index=True)  # OBSERVED, ESTIMATED

    sample_size = Column(Integer, nullable=False, default=0)
    observed_count = Column(Integer, nullable=False, default=0)
    estimated_count = Column(Integer, nullable=False, default=0)
    coverage_percent = Column(Float, nullable=False, default=100.0)

    base_period = Column(String(50), default="2026-08-28")
    base_period_is_real_data = Column(Boolean, default=True, nullable=False,
                                      comment="True if base period and P0 were established from real scraped data")
    methodology_version = Column(String(50), default="v1.0-prototype", nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class ScrapeRun(Base):
    """
    Tracks lifecycle, duration, collection volume, and health status for each collection run.
    """
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="STARTED", nullable=False, index=True)  # STARTED, SUCCESS, PARTIAL, FAILED
    source = Column(String(50), nullable=True)
    route = Column(String(20), nullable=True)
    horizon = Column(Integer, nullable=True)
    attempted = Column(Integer, default=0, nullable=False)
    successful = Column(Integer, default=0, nullable=False)
    records_collected = Column(Integer, default=0, nullable=False)
    records_rejected = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Float, default=0.0, nullable=False)
    metadata_json = Column(JSON, nullable=True)


class ReferenceData(Base):
    """
    Stores external reference benchmarks (e.g. DGCA monthly passenger yield / average fares).
    """
    __tablename__ = "reference_data"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(String(64), unique=True, index=True, nullable=False)
    source = Column(String(50), nullable=False)  # e.g., DGCA_MONTHLY_REPORT, SAMPLE_BENCHMARK
    reference_period = Column(String(20), nullable=False, index=True)  # e.g., '2026-08', '2026-08-30'
    route = Column(String(20), nullable=True, index=True)  # Null for All-India
    value = Column(Float, nullable=False)
    unit = Column(String(20), default="INR", nullable=False)  # INR or INDEX_POINT
    is_official = Column(Boolean, default=False, nullable=False)
    publication_date = Column(DateTime, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    methodology = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class ValidationResult(Base):
    """
    Stores statistical validation metrics comparing reconstructed index series against external benchmarks.
    """
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    validation_id = Column(String(64), index=True, nullable=False)
    validation_type = Column(String(50), index=True, nullable=False)  # HISTORICAL_BACKTEST, SENSITIVITY_OUTLIER, etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reference_source = Column(String(50), nullable=False)
    index_method = Column(String(50), nullable=False)
    route = Column(String(20), nullable=True)

    our_mean_index = Column(Float, nullable=False)
    reference_mean_value = Column(Float, nullable=False)
    mae = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    pearson_corr = Column(Float, nullable=True)
    spearman_corr = Column(Float, nullable=True)
    mean_pct_deviation = Column(Float, nullable=True)
    directional_agreement_pct = Column(Float, nullable=True)

    sample_size = Column(Integer, default=0, nullable=False)
    observed_count = Column(Integer, default=0, nullable=False)
    coverage_percent = Column(Float, default=100.0, nullable=False)
    route_coverage_percent = Column(Float, default=100.0, nullable=False)

    methodology_version = Column(String(50), default="v1.0-prototype", nullable=False)
    weight_version = Column(String(50), default="v1.0-prototype", nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
