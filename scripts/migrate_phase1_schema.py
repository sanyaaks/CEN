import sys
import os
import logging
from sqlalchemy import text

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate_phase1")


def run_migration():
    logger.info("Executing safe Phase 1 schema migration on Neon PostgreSQL...")

    ddl_statements = [
        # CleanFare modifications
        "ALTER TABLE clean_fares ALTER COLUMN base_fare DROP NOT NULL;",
        "ALTER TABLE clean_fares ALTER COLUMN tax DROP NOT NULL;",
        "ALTER TABLE clean_fares ADD COLUMN IF NOT EXISTS observation_type VARCHAR(20) DEFAULT 'OBSERVED' NOT NULL;",
        "ALTER TABLE clean_fares ADD COLUMN IF NOT EXISTS fare_decomposition_status VARCHAR(20) DEFAULT 'UNAVAILABLE' NOT NULL;",
        "ALTER TABLE clean_fares ADD COLUMN IF NOT EXISTS gst FLOAT NULL;",
        "ALTER TABLE clean_fares ADD COLUMN IF NOT EXISTS airport_charges FLOAT NULL;",
        "ALTER TABLE clean_fares ADD COLUMN IF NOT EXISTS user_development_fee FLOAT NULL;",
        "ALTER TABLE clean_fares ADD COLUMN IF NOT EXISTS convenience_fee FLOAT NULL;",

        # IndexValue modifications
        "ALTER TABLE index_values ADD COLUMN IF NOT EXISTS frequency VARCHAR(20) DEFAULT 'DAILY' NOT NULL;",
        "ALTER TABLE index_values ADD COLUMN IF NOT EXISTS observation_type VARCHAR(20) DEFAULT 'OBSERVED' NOT NULL;",
        "ALTER TABLE index_values ADD COLUMN IF NOT EXISTS coverage_percent FLOAT DEFAULT 100.0 NULL;",
        "ALTER TABLE index_values ADD COLUMN IF NOT EXISTS observed_count INTEGER DEFAULT 0 NULL;",
        "ALTER TABLE index_values ADD COLUMN IF NOT EXISTS estimated_count INTEGER DEFAULT 0 NULL;",
        "ALTER TABLE index_values ADD COLUMN IF NOT EXISTS methodology_version VARCHAR(50) DEFAULT 'v1.0-prototype' NULL;",

        # Indexes for fast filtering
        "CREATE INDEX IF NOT EXISTS ix_clean_fares_observation_type ON clean_fares (observation_type);",
        "CREATE INDEX IF NOT EXISTS ix_clean_fares_fare_decomposition_status ON clean_fares (fare_decomposition_status);",
        "CREATE INDEX IF NOT EXISTS ix_index_values_frequency ON index_values (frequency);",
        "CREATE INDEX IF NOT EXISTS ix_index_values_observation_type ON index_values (observation_type);"
    ]

    with engine.begin() as conn:
        for stmt in ddl_statements:
            logger.info(f"Running: {stmt}")
            conn.execute(text(stmt))

    logger.info("Phase 1 schema migration executed successfully on Neon PostgreSQL!")


if __name__ == "__main__":
    run_migration()
