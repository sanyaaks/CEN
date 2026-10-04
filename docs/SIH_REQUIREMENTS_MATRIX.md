# MoSPI Airfare Index System — SIH Problem Statement Traceability Matrix

This document maps all core requirements from the MoSPI / SIH Airfare Price Index problem statement to the actual implementation modules, codebase evidence, and verification status.

---

## Traceability Table

| # | Requirement Area | Problem Statement Specification | Implementation Module | Verification Evidence | Status |
|---|---|---|---|---|---|
| **1** | **Automated Data Collection** | High-frequency scraping of domestic airfare quotes across multiple sources with polite rate limiting. | `app/scraping/flight_client.py`, `app/scraping/scheduler.py` | Multi-source scraper with Google Flights, OTA, Playwright, User-Agent `AirIndexIndiaBot/1.0`, jittered delays. | **COMPLETE** |
| **2** | **Corridor Basket Selection** | Monitoring high-density domestic trunk routes across India. | `app/config.py` (`DEFAULT_ROUTES`) | 6 major routes configured: `DEL-BOM`, `BLR-DEL`, `HYD-MAA`, `DEL-MAA`, `BOM-BLR`, `DEL-CCU`. | **COMPLETE** |
| **3** | **Advance Booking Windows** | Tracking price dynamics across standardized lead-time horizons ($T+1$ to $T+45$ days). | `app/config.py` (`DEFAULT_HORIZONS`), `app/scraping/scheduler.py` | 5 standardized horizons: $T+1, T+7, T+15, T+30, T+45$ days systematically scraped. | **COMPLETE** |
| **4** | **Data Cleaning & Normalization** | Removing invalid quotes ($₹0$, circular routes) and standardizing currency. | `app/scraping/validator.py`, `app/processing/normalize.py` | `IngestionValidator` drops invalid records; `FareNormalizer` standardizes observations into `clean_fares`. | **COMPLETE** |
| **5** | **Data Provenance Separation** | Explicit separation of directly observed, model estimated, and external reference data. | `app/models/db_models.py`, `app/processing/normalize.py` | `observation_type` column (`OBSERVED`, `ESTIMATED`, `REFERENCE`) enforced across all database tables. | **COMPLETE** |
| **6** | **Fare Decomposition Transparency** | Itemization of Base Fare vs Taxes without blind flat GST assumptions. | `app/models/db_models.py`, `app/processing/normalize.py` | `fare_decomposition_status` (`EXACT`, `PARTIAL`, `UNAVAILABLE`) tracks true breakdown availability. | **COMPLETE** |
| **7** | **Outlier Rejection Filter** | Isolating extreme pricing anomalies and scraping artifacts. | `app/processing/outliers.py` | Combined 3-Sigma standard deviation and Interquartile Range (IQR) bounds with `is_outlier` audit tags. | **COMPLETE** |
| **8** | **Elementary Price Index Formulas** | Implementation of standard statistical index number formulas (Dutot & Jevons). | `app/processing/index_engine.py` | Dutot arithmetic ratio and Jevons geometric ratio with divide-by-zero safeguards. | **COMPLETE** |
| **9** | **National Composite Index** | Aggregating elementary route indices into a national index using weighted averages. | `app/processing/index_engine.py` | Dynamically normalized weights across observed routes with transparent prototype traffic shares. | **COMPLETE** |
| **10** | **Cryptographic Audit Trail** | Immutable audit records from raw scrape JSON to index contribution. | `app/models/db_models.py`, `app/scraping/raw_store.py` | SHA-256 payload fingerprinting stored in `raw_fares`, linked via foreign key to `clean_fares`. | **COMPLETE** |
| **11** | **Historical Backtesting** | Reconstructing index series over historical datasets and evaluating stability. | `app/processing/backtest_engine.py`, `scripts/run_backtest.py` | Deterministic 45-day historical reconstruction with sensitivity analysis (Baseline vs Unfiltered). | **COMPLETE** |
| **12** | **Statistical Comparison Metrics** | Computing MAE, RMSE, MAPE, Pearson correlation, and directional agreement. | `app/processing/backtest_engine.py` | Standardized mathematical formulas implemented in `BacktestEngine.calculate_metrics`. | **COMPLETE** |
| **13** | **Interactive Web Dashboard** | Modern, responsive dashboard visualizing index trends, route matrices, and data quality. | `frontend/` (Next.js 16 App Router) | 8 comprehensive views: Dashboard, Routes, Booking Window, Airlines, Quality, Validation, Audit, Collection. | **COMPLETE** |
| **14** | **MoSPI / NSO CPI Export** | Exporting index series formatted for official CPI item code `07.3.3.1`. | `app/api/routes_export.py` | Standardized CSV and JSON endpoints formatted for National Statistical Office ingestion. | **COMPLETE** |
| **15** | **System Observability & Monitoring** | Tracking scraper adapter health, latencies, and execution logs. | `app/scraping/health.py`, `app/api/routes_audit.py` | `SourceHealthTracker` and `ScrapeRun` logs stored in Neon PostgreSQL and monitored live. | **COMPLETE** |
| **16** | **Official DGCA Reference Validation** | Comparison of index against certified DGCA monthly passenger yield benchmarks. | `app/models/db_models.py` (`ReferenceData`), `scripts/import_reference_data.py` | Reference data ingestion pipeline ready. Official comparison labeled **PENDING** until certified data imported. | **PENDING (Dataset Ingestion)** |

---

## Summary
* **Completed & Verified Requirements**: **15 / 16 (93.75%)**
* **Pending Requirements**: **1 / 16 (6.25%)** — Official DGCA reference data ingestion (pipeline built and tested with test benchmarks).
