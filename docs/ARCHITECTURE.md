# MoSPI Airfare Index System (AirIndex India) — System Architecture

## 1. System Overview

AirIndex India is an automated, high-frequency civil aviation airfare data collection, statistical normalization, outlier filtering, elementary price index computation, and historical backtesting system designed for monitoring domestic passenger airfare inflation under the Ministry of Statistics and Programme Implementation (MoSPI) / National Statistical Office (NSO) Consumer Price Index (CPI) methodology (COICOP item `07.3.3.1`).

---

## 2. End-to-End Architecture Diagram

```mermaid
graph TD
    subgraph ClientLayer ["Client / Evaluation Layer"]
        User["SIH Judges / Policy Economists"]
        NextJS["Next.js 16 Dashboard (Port 3000)<br/>App Router • TypeScript • Tailwind CSS"]
    end

    subgraph APILayer ["FastAPI Application Layer (Port 8000)"]
        FastAPI["FastAPI REST Application"]
        IndexRouter["/index & /index/{route}"]
        AuditRouter["/audit, /sources/health, /runs"]
        ValRouter["/validation/backtest, /metrics, /coverage"]
        ExportRouter["/export (COICOP 07.3.3.1)"]
        HealthRouter["/health (Liveness) & /health/ready (Readiness)"]
    end

    subgraph DataCollection ["Multi-Source Ingestion & Scheduling"]
        Scheduler["APScheduler Background Worker<br/>(Cron: 0 * * * *)"]
        FlightClient["FlightClient Multi-Source Orchestrator"]
        Registry["SourceRegistry & Priority Manager"]
        HealthTracker["SourceHealthTracker (Circuit Breaker)"]
        Validator["IngestionValidator (Non-Circular, Positive)"]
        GFScraper["Google Flights Aggregator"]
        OTAScraper["OTA Gateway Client"]
        PWScraper["Playwright Headless Scraper"]
    end

    subgraph StatisticalEngine ["Statistical Processing Pipeline"]
        Normalizer["FareNormalizer<br/>(OBSERVED / ESTIMATED Provenance)"]
        OutlierDetector["OutlierDetector<br/>(3-Sigma Z-Score + IQR Bounds)"]
        IndexEngine["IndexEngine<br/>(Dutot, Jevons, Normalized Prototype Weights)"]
        BacktestEngine["BacktestEngine<br/>(Deterministic Reconstruction & Validation)"]
    end

    subgraph StorageLayer ["Neon Cloud PostgreSQL"]
        RawDB[("raw_fares<br/>(SHA-256 Payload Hash)")]
        CleanDB[("clean_fares<br/>(Itemized & Provenanced)")]
        IndexDB[("index_values<br/>(Frequency & Coverage)")]
        RunsDB[("scrape_runs<br/>(Execution Telemetry)")]
        RefDB[("reference_data<br/>(External Benchmarks)")]
        ValDB[("validation_results<br/>(Historical Metrics)")]
    end

    User --> NextJS
    NextJS -- HTTPS / REST --> FastAPI
    FastAPI --> IndexRouter
    FastAPI --> AuditRouter
    FastAPI --> ValRouter
    FastAPI --> ExportRouter
    FastAPI --> HealthRouter

    Scheduler --> FlightClient
    FlightClient --> Registry
    Registry --> HealthTracker
    FlightClient --> GFScraper
    FlightClient --> OTAScraper
    FlightClient --> PWScraper
    GFScraper --> Validator
    OTAScraper --> Validator
    PWScraper --> Validator
    Validator --> RawDB

    RawDB --> Normalizer
    Normalizer --> CleanDB
    CleanDB --> OutlierDetector
    OutlierDetector --> IndexEngine
    IndexEngine --> IndexDB
    CleanDB --> BacktestEngine
    RefDB --> BacktestEngine
    BacktestEngine --> ValDB
```

---

## 3. Core Component Breakdown

### 1. Multi-Source Ingestion Layer (`app/scraping/`)
* **`BaseScraper` Contract**: Standardized interface enforcing `search(...)` and `create_standard_quote(...)`.
* **`SourceRegistry`**: Dynamic priority ranking (`google_flights` $\to$ `ota_gateway` $\to$ `playwright_headless`).
* **`SourceHealthTracker`**: Circuit breaker tracking consecutive failures, query count, and latency.
* **`IngestionValidator`**: Drops $₹0$ quotes, circular routes (DEL-DEL), and malformed payloads before database storage.
* **Ethical Safeguards**: Bounded timeouts (15s), jittered backoff, respectful `AirIndexIndiaBot/1.0` User-Agent.

### 2. Statistical Processing Engine (`app/processing/`)
* **`FareNormalizer`**: Categorizes observation provenance into `OBSERVED`, `ESTIMATED`, and `REFERENCE`. Eliminates arbitrary GST/tax assumptions by tracking `fare_decomposition_status` (`EXACT`, `PARTIAL`, `UNAVAILABLE`).
* **`OutlierDetector`**: Flags extreme non-market anomalies using combined 3-Sigma standard deviation and Interquartile Range (IQR) fences.
* **`IndexEngine`**:
  * **Dutot Arithmetic Ratio**: $I_{0,t}^D = \left(\frac{\sum p_{i,t}}{\sum p_{i,0}}\right) \times 100$
  * **Jevons Geometric Ratio**: $I_{0,t}^J = \exp\left(\frac{1}{n} \sum \ln(p_{i,t}) - \frac{1}{n} \sum \ln(p_{i,0})\right) \times 100$
  * **Composite Aggregation**: Dynamic weight normalization across active routes:
    $$I_t = \frac{\sum_{r \in \mathcal{R}_t} w_r I_{r,t}}{\sum_{r \in \mathcal{R}_t} w_r}$$

### 3. Historical Backtesting Engine (`app/processing/backtest_engine.py`)
* Reconstructs historical index series deterministically from verified `OBSERVED` quotes.
* Computes standard statistical validation metrics: Mean Absolute Error (MAE), Root Mean Square Error (RMSE), Mean Absolute Percentage Error (MAPE), Pearson correlation, and Directional Agreement.
* Reconstructs 3 sensitivity scenarios: Baseline Clean, Unfiltered Outliers, and Estimated Inclusive.

### 4. Database Layer (Neon Cloud PostgreSQL)
* 6 dedicated relational tables with explicit indexes: `raw_fares`, `clean_fares`, `index_values`, `scrape_runs`, `reference_data`, and `validation_results`.

### 5. Next.js Dashboard (`frontend/`)
* 8 responsive dashboard views built with Next.js App Router, TypeScript, and Tailwind CSS.
* Zero hardcoded production data; all views consume the live FastAPI backend with error/loading boundaries.
