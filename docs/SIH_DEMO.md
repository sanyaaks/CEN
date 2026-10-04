# AirIndex India — Smart India Hackathon (SIH) Live Demo Script

**Recommended Presentation Duration**: 5 to 8 minutes  
**Target Audience**: MoSPI / NSO Evaluators & SIH Jury Panel

---

## Pre-Demo Checklist

1. **Start FastAPI Backend**:
   ```bash
   uvicorn app.main:app --port 8000
   ```
2. **Start Next.js Frontend**:
   ```bash
   cd frontend && npm run dev
   ```
3. **Open in Browser**:
   * Dashboard: `http://localhost:3000`
   * Swagger OpenAPI Docs: `http://localhost:8000/docs`

---

## 8-Step Demonstration Flow

### Step 1: Main Dashboard (`/`) — 1 Minute
* **What to Show**:
  * Point out the **National Composite Airfare Price Index** card (`71.76 pts`).
  * Highlight the **100% Observation Coverage** badge (932 genuine quotes observed, 0 estimated).
  * Toggle between **Dutot (Arithmetic)** and **Jevons (Geometric)** formulas in real-time to demonstrate statistical flexibility.
  * Show the 6 domestic trunk route cards (`DEL-BOM`, `BLR-DEL`, `DEL-CCU`, `BOM-BLR`, `DEL-MAA`, `HYD-MAA`).
* **Key Talking Point**:
  > *"AirIndex India is an automated, high-frequency price index engine aligned with MoSPI CPI item 07.3.3.1. All numbers shown on this screen originate from real scraped quotes in our Neon PostgreSQL database with zero synthetic fabrication."*

---

### Step 2: Route Corridor Explorer (`/routes`) — 1 Minute
* **What to Show**:
  * Select `DEL-BOM` from the dropdown.
  * Point out the **Average Observed Fare** (e.g. ₹5,420), min/max observed range, and historical price relative trend.
  * Scroll down to the **Airline Distribution Table** showing carrier shares (IndiGo, Air India, SpiceJet, Vistara, Akasa Air) and carrier-specific average fares.
* **Key Talking Point**:
  > *"Our system isolates airline market dynamics per corridor, enabling economists to see both macro index movements and carrier-level price distributions."*

---

### Step 3: Advance Purchase Window Analysis (`/booking-window`) — 1 Minute
* **What to Show**:
  * Show the 5 standardized booking horizons: $T+1, T+7, T+15, T+30, T+45$ days.
  * Explain the observed lead-time curve showing how prices evolve as departure day approaches.
* **Key Talking Point**:
  > *"We capture standardized forward travel dates to isolate advance purchase pricing dynamics from last-minute distress fares."*

---

### Step 4: Data Quality & Governance (`/data-quality`) — 1 Minute
* **What to Show**:
  * Show the **Three-Tier Coverage Architecture**: Observation Coverage, Route Coverage, and Source Health Coverage.
  * Show the **Fare Decomposition Breakdown** (`UNAVAILABLE`, `EXACT`, `PARTIAL`).
* **Key Talking Point**:
  > *"Unlike naive scrapers that assume flat 5% or 15% GST splits, AirIndex India explicitly reports when fare breakdowns are unavailable rather than guessing."*

---

### Step 5: Collection & Source Health Monitor (`/collection`) — 45 Seconds
* **What to Show**:
  * Show the 3 scraper adapters: `Google Flights`, `OTA Gateway`, and `Playwright Scraper`.
  * Show the live query counts, latencies (ms), and chronological **ScrapeRun Execution Logs**.
* **Key Talking Point**:
  > *"Our scraping layer is resilient, circuit-broken, rate-limited, and records every single scrape execution run with start/end timestamps and error metrics."*

---

### Step 6: Cryptographic Data Lineage (`/audit`) — 1 Minute
* **What to Show**:
  * Walk through the **5-Stage Pipeline** (Raw Scrape $\to$ Normalization $\to$ Ingestion Check $\to$ Outlier Rejection $\to$ Index Aggregation).
  * Click on an observation in the table to display its **SHA-256 cryptographic payload hash** and outlier score.
* **Key Talking Point**:
  > *"Every single price quote that contributes to the index has an immutable raw JSON audit record in PostgreSQL with a SHA-256 fingerprint, guaranteeing complete reproducibility."*

---

### Step 7: Historical Backtesting & Validation (`/validation`) — 1 Minute
* **What to Show**:
  * Point out the **Deterministic Historical Reconstruction** across the 45-day dataset.
  * Show the **Sensitivity Analysis** comparing Baseline Clean vs Unfiltered Outliers.
  * Point out the prominent **DGCA Reference Status Banner** stating that official DGCA comparison remains pending certified ingestion.
* **Key Talking Point**:
  > *"We built an end-to-end backtesting pipeline with sensitivity bounds. We maintain complete scientific honesty by clearly marking external reference comparisons as pending official dataset ingestion."*

---

### Step 8: NSO CPI Export & API Documentation (`/export` & `/docs`) — 45 Seconds
* **What to Show**:
  * Click **Export CSV** and **Export JSON** to show the MoSPI COICOP `07.3.3.1` standardized output.
  * Open `/docs` to show all 15 FastAPI REST endpoints with interactive Swagger testing.
* **Key Talking Point**:
  > *"The system is fully decoupled and ready to integrate directly with MoSPI CPI data aggregation pipelines via standard REST and scheduled bulk exports."*
