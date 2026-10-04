export interface IndexRecord {
  id: number;
  route: string;
  date: string;
  index_value: number;
  method: string;
  frequency: string;
  observation_type: "OBSERVED" | "ESTIMATED" | "REFERENCE";
  sample_size: number;
  observed_count: number;
  estimated_count: number;
  coverage_percent: number;
  base_period: string;
  base_period_is_real_data: boolean;
  methodology_version: string;
  created_at: string;
  metadata?: {
    current_mean_price?: number;
    base_reference_price?: number;
    min_price?: number;
    max_price?: number;
    geometric_mean?: number;
    weights_applied?: Record<string, number>;
    normalized_weight_sum?: number;
    observed_routes?: string[];
    excluded_routes?: string[];
    contains_estimated_data?: boolean;
    weight_source?: string;
    is_official_weight?: boolean;
  } | null;
}

export interface LatestIndexResponse {
  count: number;
  data: IndexRecord[];
}

export interface RouteIndexHistoryResponse {
  route: string;
  records_count: number;
  history: IndexRecord[];
}

export interface AuditSummaryResponse {
  summary: {
    total_raw_scrapes: number;
    total_clean_observations: number;
    total_observed_quotes: number;
    total_estimated_quotes: number;
    observed_coverage_pct: number;
    total_outliers_flagged: number;
    outlier_rate_pct: number;
    fare_decomposition_breakdown: {
      exact: number;
      partial: number;
      unavailable: number;
    };
  };
  recent_scrapes: Array<{
    raw_id: number;
    timestamp: string;
    source: string;
    origin: string;
    destination: string;
    travel_date: string;
    booking_horizon_days: number;
    payload_hash: string;
    quotes_count: number;
  }>;
}

export interface SourceHealthItem {
  source_name: string;
  source_type: string;
  enabled: boolean;
  priority: number;
  is_fallback_model: boolean;
  compliance_status: string;
  health: {
    status: "HEALTHY" | "DEGRADED" | "UNAVAILABLE" | "DISABLED";
    last_success: string | null;
    last_failure: string | null;
    consecutive_failures: number;
    total_queries: number;
    successful_queries: number;
    total_quotes_collected: number;
    last_error: string | null;
    last_response_time_ms: number;
  };
}

export interface SourcesHealthResponse {
  sources_count: number;
  sources: SourceHealthItem[];
}

export interface ScrapeRunItem {
  id: number;
  run_id: string;
  started_at: string;
  completed_at: string | null;
  status: "STARTED" | "SUCCESS" | "PARTIAL" | "FAILED";
  source?: string | null;
  route?: string | null;
  horizon?: number | null;
  attempted: number;
  successful: number;
  records_collected: number;
  records_rejected: number;
  error_count: number;
  error_message: string | null;
  duration_seconds: number;
  metadata?: Record<string, any> | null;
}

export interface ScrapeRunsResponse {
  runs_count: number;
  runs: ScrapeRunItem[];
}

export interface CleanObservation {
  clean_fare_id: number;
  route: string;
  travel_date: string;
  horizon_days: number;
  airline: string;
  flight_number: string | null;
  observation_type: "OBSERVED" | "ESTIMATED" | "REFERENCE";
  fare_decomposition_status: "EXACT" | "PARTIAL" | "UNAVAILABLE";
  total_price: number;
  base_fare: number | null;
  tax: number | null;
  gst: number | null;
  tax_estimated: boolean;
  ancillary_fees_dropped: number;
  is_outlier: boolean;
  outlier_reason: string | null;
  outlier_score: number | null;
  cleaned_at: string;
  lineage: {
    source_raw_fare_id: number | null;
    scrape_timestamp: string | null;
    source_engine: string | null;
    sha256_payload_hash: string | null;
  };
}

export interface RouteAuditResponse {
  route: string;
  sample_count: number;
  observed_count: number;
  estimated_count: number;
  outlier_count: number;
  observations: CleanObservation[];
}

export interface DailyReconstructionPoint {
  date: string;
  base_period: string;
  composite_index: number;
  method: string;
  route_indices: Record<string, number>;
  route_stats: Record<string, { sample_size: number; mean_price: number; index_value: number }>;
  configured_routes_count: number;
  observed_routes_count: number;
  route_coverage_percent: number;
  total_observations_count: number;
  observed_count: number;
  estimated_count: number;
  observation_coverage_percent: number;
  methodology_version: string;
}

export interface BacktestResponse {
  validation_id: string;
  validation_period: {
    start_date: string;
    end_date: string;
    days_count: number;
  };
  base_period: string;
  methodology_version: string;
  weight_version: string;
  index_method: string;
  reference_source: string;
  reference_status: string;
  our_mean_index: number;
  reference_mean_value: number;
  metrics: {
    mae: number | null;
    mape: number | null;
    rmse: number | null;
    pearson_corr: number | null;
    spearman_corr: number | null;
    mean_pct_deviation: number | null;
    directional_agreement_pct: number | null;
  };
  coverage_summary: {
    total_observations: number;
    observed_observations: number;
    average_route_coverage_percent: number;
    average_observation_coverage_percent: number;
  };
  sensitivity_analysis: {
    baseline_mean_index: number;
    unfiltered_outliers_mean_index: number | null;
    estimated_inclusive_mean_index: number | null;
  };
  daily_series: DailyReconstructionPoint[];
}

export interface ValidationCoverageResponse {
  period: { start_date: string; end_date: string; days: number };
  summary: {
    total_observations: number;
    observed_observations: number;
    average_route_coverage_percent: number;
    average_observation_coverage_percent: number;
  };
  daily_breakdown: Array<{
    date: string;
    observed_routes: number;
    configured_routes: number;
    route_coverage_percent: number;
    observed_quotes: number;
    total_quotes: number;
    observation_coverage_percent: number;
  }>;
}

export interface RouteValidationItem {
  route: string;
  our_mean_index: number;
  reference_benchmark_value: number | null;
  difference: number | null;
  pct_difference: number | null;
  reference_source: string;
  days_observed: number;
}

export interface RouteValidationResponse {
  routes_count: number;
  routes: RouteValidationItem[];
}

export interface HarvestFlightItem {
  airline: string;
  flight_number?: string | null;
  origin: string;
  destination: string;
  departure_time?: string | null;
  arrival_time?: string | null;
  price_inr: number;
  is_non_stop: boolean;
  source: string;
}

export interface HarvestResponse {
  status: string;
  message: string;
  route: string;
  departure_date: string;
  portal: string;
  portal_name: string;
  quotes_count: number;
  raw_fare_id?: number | null;
  payload_hash?: string | null;
  index_updated: boolean;
  latest_composite_index?: number | null;
  flights: HarvestFlightItem[];
}

export interface HarvestPortal {
  id: string;
  name: string;
  url: string;
  description: string;
}
