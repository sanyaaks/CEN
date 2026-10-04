import sys
import os
import logging
from sqlalchemy import text

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate_phase2")


def run_migration():
    logger.info("Executing safe Phase 2 schema migration on Neon PostgreSQL...")

    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS scrape_runs (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(64) NOT NULL,
            started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
            completed_at TIMESTAMP WITHOUT TIME ZONE NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'STARTED',
            source VARCHAR(50) NULL,
            route VARCHAR(20) NULL,
            horizon INTEGER NULL,
            attempted INTEGER NOT NULL DEFAULT 0,
            successful INTEGER NOT NULL DEFAULT 0,
            records_collected INTEGER NOT NULL DEFAULT 0,
            records_rejected INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            error_message TEXT NULL,
            duration_seconds FLOAT NOT NULL DEFAULT 0.0,
            metadata_json JSON NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_scrape_runs_run_id ON scrape_runs (run_id);",
        "CREATE INDEX IF NOT EXISTS ix_scrape_runs_status ON scrape_runs (status);",
        "CREATE INDEX IF NOT EXISTS ix_scrape_runs_started_at ON scrape_runs (started_at);"
    ]

    with engine.begin() as conn:
        for stmt in ddl_statements:
            logger.info(f"Running DDL statement...")
            conn.execute(text(stmt))

    logger.info("Phase 2 schema migration executed successfully on Neon PostgreSQL!")


if __name__ == "__main__":
    run_migration()
