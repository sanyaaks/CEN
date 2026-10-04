# MoSPI Airfare Index System — AirIndex India

An automated high-frequency data collection, cleaning, outlier filtering, statistical elementary index computation engine (Dutot / Jevons / Prototype Weighted Indices), historical backtesting validation pipeline, and Next.js modern statistical dashboard designed for tracking domestic airfare inflation under Ministry of Statistics and Programme Implementation (MoSPI) / National Statistical Office (NSO) Consumer Price Index (CPI) methodology (COICOP 07.3.3.1).

> [!NOTE]
> This system is an **NSO/MoSPI-oriented prototype** developed for the Smart India Hackathon (SIH) airfare index problem statement.
> **Data Attribution**: Route weighting data sourced from DGCA (Directorate General of Civil Aviation) via the `india-aviation-traffic` open dataset (ODbL license), aggregated from official Monthly Statistics (Domestic Air Transport) reports.

---

## 1. System Architecture (Phases 1, 2, 3, & 4)

```
[ NEXT.JS 16 APP ROUTER DASHBOARD (AIRINDEX INDIA) ]
Dashboard (/) • Routes (/routes) • Advance Window (/booking-window) • Airlines (/airlines)
Data Quality (/data-quality) • Validation (/validation) • Audit (/audit) • Collection (/collection)
                                  |
                                  v  REST API
[ FASTAPI HIGH-FREQUENCY BACKEND ENGINE ]
/index • /audit • /validation • /export (COICOP 07.3.3.1 CSV/JSON)
                                  |
                                  v
[ MULTI-SOURCE SCRAPING & INGESTION LAYER ]
Google Flights | OTA Gateway | Playwright Headless Browser | Ingestion Validator
                                  |
                                  v
[ STATISTICAL NORMALIZATION & OUTLIER FILTERING ]
3-Sigma Z-Score + IQR Filter • OBSERVED vs ESTIMATED • EXACT vs UNAVAILABLE
                                  |
                                  v
[ NEON CLOUD POSTGRESQL DATABASE ]
raw_fares • clean_fares • index_values • scrape_runs • reference_data • validation_results
```

---

## 2. Frontend Application (Next.js)

### Available Pages:
* `/` — **Main Dashboard**: Real-time National Composite Index KPI, Dutot/Jevons method toggle, interactive trend charts, route cards, NSO export triggers.
* `/routes` — **Route Explorer**: Corridor selector (DEL-BOM, BLR-DEL, etc.), historical index trajectory, observed fare ranges, and airline carrier shares.
* `/booking-window` — **Advance Purchase Analysis**: Standardized lead-time curves across $T+1, T+7, T+15, T+30, T+45$ days.
* `/airlines` — **Airline Analysis**: Carrier quote density, average fares, fare ranges, and network corridor coverage.
* `/data-quality` — **Data Quality & Governance**: Three-tier coverage metrics (Observation vs Route vs Source Coverage), outlier rejection rates, fare decomposition status.
* `/validation` — **Historical Backtest & Validation**: Deterministic 45-day index series reconstruction, sensitivity bounds, and pending DGCA benchmark status.
* `/audit` — **Cryptographic Data Lineage**: 5-stage pipeline visualization, SHA-256 payload inspection, and outlier score audits.
* `/collection` — **Collection & Health Monitor**: Live status of scraper adapters, response latencies, and execution run logs.

### Running the Frontend Locally:
```bash
cd frontend
npm install
npm run dev
# Dashboard accessible at http://localhost:3000
```

### Frontend Tests & Build:
```bash
cd frontend
npm test          # Runs Vitest unit & API mock tests (5/5 passing)
npm run build     # Compiles optimized static production bundle (11/11 pages)
```

---

## 3. Backend & CLI Verification

```bash
# 1. Run Complete Automated Test Suite (41/41 passing)
pytest

# 2. Run Comprehensive Deep System Audit (100% PASS on Neon DB)
python scripts/deep_system_audit.py

# 3. Run Historical Backtest CLI
python scripts/run_backtest.py --start-date 2026-08-30 --end-date 2026-10-13

# 4. Import External Reference Benchmarks
python scripts/import_reference_data.py --seed-sample

# 5. Start FastAPI Backend Locally
uvicorn app.main:app --reload --port 8000
```
