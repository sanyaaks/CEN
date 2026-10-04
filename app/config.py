import os
import json
from typing import List, Dict, Union, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql://neondb_owner:npg_c6SBzIg0dqje@ep-wispy-leaf-azsif5wh-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 300

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"

    SCRAPE_SCHEDULE_CRON: str = "0 * * * *"
    DEFAULT_HORIZONS: Union[str, List[int]] = [1, 7, 15, 30, 45]
    DEFAULT_ROUTES: Union[str, List[str]] = [
        "DEL-BOM",
        "BLR-DEL",
        "HYD-MAA",
        "DEL-MAA",
        "BOM-BLR",
        "DEL-CCU"
    ]

    # --- Scraping & Resilience Configuration ---
    SCRAPER_USER_AGENT: str = "AirIndexIndiaBot/1.0 (+https://github.com/SamDev007-pixel/CEN; contact=mospi-airindex@gov.in.prototype)"
    SCRAPER_REQUEST_TIMEOUT: int = 15
    SCRAPER_MAX_RETRIES: int = 2
    SCRAPER_BACKOFF_FACTOR: float = 1.5
    SCRAPER_MIN_DELAY_SEC: float = 1.0
    SCRAPER_MAX_DELAY_SEC: float = 2.5
    
    # Source toggles
    ENABLE_GOOGLE_FLIGHTS: bool = True
    ENABLE_PLAYWRIGHT: bool = True
    ENABLE_OTA_GATEWAY: bool = True
    ENABLE_FALLBACK_ESTIMATES: bool = True

    # Source Priority order
    SOURCE_PRIORITY: List[str] = [
        "google_flights",
        "ota_gateway",
        "playwright_headless",
        "calibrated_market_model"
    ]

    # Empirical route weights computed from real DGCA Domestic Passenger Traffic Statistics (2024).
    PROTOTYPE_ROUTE_WEIGHTS: Dict[str, float] = {
        "DEL-BOM": 0.3037,
        "BLR-DEL": 0.2104,
        "BOM-BLR": 0.1872,
        "DEL-CCU": 0.1232,
        "DEL-MAA": 0.1074,
        "HYD-MAA": 0.0681
    }
    WEIGHT_SOURCE_METADATA: Dict[str, Union[str, bool]] = {
        "source": "DGCA Monthly Statistics (Domestic Air Transport), via Vonter/india-aviation-traffic aggregated dataset (ODbL licensed)",
        "source_url": "https://github.com/Vonter/india-aviation-traffic",
        "reference_period": "2024-CALENDAR-YEAR",
        "is_official": True,
        "methodology_version": "v3.0-dgca-real-data",
        "description": "Computed from real DGCA city-pair passenger traffic data (PaxToCity2 + PaxFromCity2 summed across all 2024 monthly rows per route), among our 6 monitored corridors."
    }

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def horizons_list(self) -> List[int]:
        if isinstance(self.DEFAULT_HORIZONS, list):
            return [int(x) for x in self.DEFAULT_HORIZONS]
        if isinstance(self.DEFAULT_HORIZONS, str):
            val = self.DEFAULT_HORIZONS.strip()
            if val.startswith("["):
                return json.loads(val)
            return [int(x.strip()) for x in val.split(",") if x.strip()]
        return [1, 7, 15, 30, 45]

    @property
    def routes_list(self) -> List[str]:
        if isinstance(self.DEFAULT_ROUTES, list):
            return [str(x) for x in self.DEFAULT_ROUTES]
        if isinstance(self.DEFAULT_ROUTES, str):
            val = self.DEFAULT_ROUTES.strip()
            if val.startswith("["):
                return json.loads(val)
            return [x.strip() for x in val.split(",") if x.strip()]
        return ["DEL-BOM", "BLR-DEL", "HYD-MAA", "DEL-MAA", "BOM-BLR", "DEL-CCU"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
