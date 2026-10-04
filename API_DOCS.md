# MoSPI Airfare Index System — API Documentation

Interactive OpenAPI / Swagger documentation is available locally at:
`http://localhost:8000/docs`

---

## 1. Index Endpoints

### `GET /index/`
Returns the latest calculated elementary and composite price indices across domestic corridors.

#### Query Parameters:
* `method` *(optional, string)*: `Dutot`, `Jevons`, or `DGCA_Weighted_Dutot`.
* `frequency` *(optional, string)*: `DAILY`, `WEEKLY`, `MONTHLY`. Default: `DAILY`.
* `observation_type` *(optional, string)*: `OBSERVED` or `ESTIMATED`. Default: `OBSERVED`.

---

### `GET /index/{route}`
Returns chronological historical index time series for a specific route (e.g., `DEL-BOM`).

---

## 2. Audit & Data Lineage Endpoints

### `GET /audit/`
Summary statistics on total raw scrapes, clean fares, outlier rejection rates, and fare decomposition status.

### `GET /audit/sources/health`
Real-time health, response latency, and failure metrics for all registered scrapers.

### `GET /audit/runs`
Execution run history tracking attempted queries, duration, and error diagnostics.

### `GET /audit/{route}`
Lineage of individual observations with SHA-256 payload hashes and outlier scores.

---

## 3. Historical Backtesting & Validation Endpoints

### `GET /validation/backtest`
Executes deterministic historical index reconstruction across a date window with sensitivity scenarios.

#### Query Parameters:
* `start_date` *(string, YYYY-MM-DD)*: e.g. `2026-08-30`
* `end_date` *(string, YYYY-MM-DD)*: e.g. `2026-10-13`
* `method` *(string)*: `Dutot` or `Jevons`
* `reference_source` *(string)*: e.g. `SAMPLE_BENCHMARK`, `DGCA_MONTHLY_REPORT`

#### Response Example:
```json
{
  "validation_id": "val_20260828_193943_4dbd7e",
  "validation_period": {
    "start_date": "2026-08-30",
    "end_date": "2026-10-13",
    "days_count": 5
  },
  "base_period": "2026-08-30",
  "methodology_version": "v1.0-prototype",
  "our_mean_index": 71.7648,
  "reference_mean_value": 5100.0,
  "reference_status": "VALIDATED",
  "metrics": {
    "mae": 5000.0,
    "mape": 98.04,
    "rmse": 5000.0,
    "pearson_corr": null,
    "directional_agreement_pct": null
  },
  "coverage_summary": {
    "total_observations": 932,
    "observed_observations": 932,
    "average_route_coverage_percent": 100.0,
    "average_observation_coverage_percent": 100.0
  },
  "sensitivity_analysis": {
    "baseline_mean_index": 71.7648,
    "unfiltered_outliers_mean_index": 71.7918,
    "estimated_inclusive_mean_index": 71.7648
  }
}
```

---

### `GET /validation/metrics`
Returns MAE, MAPE, RMSE, and Pearson correlation vs. reference benchmark.

---

### `GET /validation/coverage`
Returns separate metrics for Route Coverage and Observation Coverage.

---

### `GET /validation/routes`
Returns route-by-route index levels compared to external route-level reference benchmarks.

---

### `GET /validation/runs`
Returns historical validation results saved in Neon PostgreSQL.

---

## 4. MoSPI / NSO Export Endpoints

### `GET /export?format=json|csv`
Dumps the price index series formatted for official National Statistical Office (NSO) Consumer Price Index (CPI) item code `07.3.3.1` (Passenger Transport by Air).
