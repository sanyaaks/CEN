import sys
import os
import logging
from sqlalchemy import text

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate_phase3")


def run_migration():
    logger.info("Executing safe Phase 3 schema migration on Neon PostgreSQL...")

    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS reference_data (
            id SERIAL PRIMARY KEY,
            reference_id VARCHAR(64) UNIQUE NOT NULL,
            source VARCHAR(50) NOT NULL,
            reference_period VARCHAR(20) NOT NULL,
            route VARCHAR(20) NULL,
            value FLOAT NOT NULL,
            unit VARCHAR(20) NOT NULL DEFAULT 'INR',
            is_official BOOLEAN NOT NULL DEFAULT FALSE,
            publication_date TIMESTAMP WITHOUT TIME ZONE NULL,
            retrieved_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
            methodology TEXT NULL,
            notes TEXT NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_reference_data_reference_id ON reference_data (reference_id);",
        "CREATE INDEX IF NOT EXISTS ix_reference_data_reference_period ON reference_data (reference_period);",
        "CREATE INDEX IF NOT EXISTS ix_reference_data_route ON reference_data (route);",
        """
        CREATE TABLE IF NOT EXISTS validation_results (
            id SERIAL PRIMARY KEY,
            validation_id VARCHAR(64) NOT NULL,
            validation_type VARCHAR(50) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reference_source VARCHAR(50) NOT NULL,
            index_method VARCHAR(50) NOT NULL,
            route VARCHAR(20) NULL,
            our_mean_index FLOAT NOT NULL,
            reference_mean_value FLOAT NOT NULL,
            mae FLOAT NULL,
            mape FLOAT NULL,
            rmse FLOAT NULL,
            pearson_corr FLOAT NULL,
            spearman_corr FLOAT NULL,
            mean_pct_deviation FLOAT NULL,
            directional_agreement_pct FLOAT NULL,
            sample_size INTEGER NOT NULL DEFAULT 0,
            observed_count INTEGER NOT NULL DEFAULT 0,
            coverage_percent FLOAT NOT NULL DEFAULT 100.0,
            route_coverage_percent FLOAT NOT NULL DEFAULT 100.0,
            methodology_version VARCHAR(50) NOT NULL DEFAULT 'v1.0-prototype',
            weight_version VARCHAR(50) NOT NULL DEFAULT 'v1.0-prototype',
            metadata_json JSON NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_validation_results_validation_id ON validation_results (validation_id);",
        "CREATE INDEX IF NOT EXISTS ix_validation_results_validation_type ON validation_results (validation_type);",
        "CREATE INDEX IF NOT EXISTS ix_validation_results_created_at ON validation_results (created_at);"
    ]

    with engine.begin() as conn:
        for stmt in ddl_statements:
            logger.info("Executing DDL statement...")
            conn.execute(text(stmt))

    logger.info("Phase 3 schema migration executed successfully on Neon PostgreSQL!")


if __name__ == "__main__":
    run_migration()
