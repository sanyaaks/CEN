# MoSPI Airfare Index System — Transparent Limitations & Constraints

In alignment with Ministry of Statistics and Programme Implementation (MoSPI) and National Statistical Office (NSO) standards of statistical governance, this document explicitly discloses the known boundaries, assumptions, and pending components of the AirIndex India prototype.

---

## 1. Official DGCA Reference Data Pending
* **Status**: **PENDING INGESTION**
* **Description**: While the ingestion pipeline (`scripts/import_reference_data.py`) and validation metric engine (`BacktestEngine`) are fully implemented and verified against unit test fixtures (`SAMPLE_BENCHMARK`), official comparisons against DGCA monthly passenger yield reports remain pending the ingestion of certified DGCA datasets.
* **Governance Guardrail**: The system strictly displays *"Official DGCA reference validation pending"* across all dashboard and validation outputs to prevent misleading claims.

---

## 2. Dynamic Airline Pricing & Horizon Coverage
* **Description**: Airline fares fluctuate continuously based on revenue management systems and seat inventory depletion.
* **Boundary**: AirIndex India collects prices across 5 standardized booking horizons ($T+1, T+7, T+15, T+30, T+45$ days). Very long-range bookings ($T+90, T+180$) or last-hour departure gate distress sales are not included in the primary index basket.

---

## 3. Public Aggregator & Scraper Availability
* **Description**: High-frequency web data collection relies on third-party aggregators and web portals that may occasionally alter DOM structures, experience temporary rate-limiting, or trigger anti-automation challenges.
* **Mitigation**: Multi-source architecture with automatic priority failover (`Google Flights` $\to$ `OTA Gateway` $\to$ `Playwright Headless Browser`) and ScrapeRun execution logging.

---

## 4. Itemized Fare Decomposition Availability
* **Description**: Many online aggregators return only the final passenger-facing total quote without exposing an itemized breakdown of base fare, airport charges, User Development Fees (UDF), and GST.
* **Boundary**: Rather than applying blind fixed assumptions (e.g. assuming flat 5% or 15% GST splits), the system records `fare_decomposition_status = "UNAVAILABLE"` and computes index relatives directly on total observed quotes.

---

## 5. Prototype Route Weighting Scheme
* **Description**: National composite index aggregation currently uses prototype weights derived from 2024-Q1 civil aviation passenger traffic distributions across the 6 major domestic corridors (`DEL-BOM`: 35%, `BLR-DEL`: 25%, `HYD-MAA`: 15%, `DEL-CCU`: 15%, `DEL-MAA`: 5%, `BOM-BLR`: 5%).
* **Boundary**: Official NSO CPI deployment will replace these provisional weights with certified Directorate General of Civil Aviation (DGCA) passenger-kilometer (RPK) annual matrices.
