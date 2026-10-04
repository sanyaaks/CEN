"use client";

import React, { useEffect, useState } from "react";
import { Sliders, ChevronDown, ChevronRight } from "lucide-react";
import { getBacktest, getValidationCoverage, getRouteValidation } from "@/lib/api";
import { BacktestResponse, ValidationCoverageResponse, RouteValidationResponse } from "@/types/api";
import LoadingState from "@/components/ui/LoadingState";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import InteractiveIndexChart from "@/components/charts/InteractiveIndexChart";

export default function ValidationPage() {
  const [method, setMethod] = useState<string>("Dutot");
  const [backtestData, setBacktestData] = useState<BacktestResponse | null>(null);
  const [coverageData, setCoverageData] = useState<ValidationCoverageResponse | null>(null);
  const [routeValidation, setRouteValidation] = useState<RouteValidationResponse | null>(null);
  const [expandedRoutes, setExpandedRoutes] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const toggleRoute = (route: string) => {
    setExpandedRoutes((prev) => ({ ...prev, [route]: !prev[route] }));
  };

  const fetchValidation = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [bt, cov, rt] = await Promise.all([
        getBacktest("2026-08-30", "2026-10-13", method, "SAMPLE_BENCHMARK"),
        getValidationCoverage("2026-08-30", "2026-10-13"),
        getRouteValidation("2026-08-30", "2026-10-13", "SAMPLE_BENCHMARK")
      ]);
      setBacktestData(bt);
      setCoverageData(cov);
      setRouteValidation(rt);
    } catch (err: any) {
      setError(err.message || "Failed to load validation and backtest data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchValidation();
  }, [method]);

  const dailySeries = backtestData?.daily_series || [];
  const chartData = dailySeries.map((d) => ({
    label: d.date,
    value: d.composite_index,
    tooltipDetails: `Observed: ${d.observed_count} quotes`
  }));

  const m = backtestData?.metrics;
  const sens = backtestData?.sensitivity_analysis;

  return (
    <div className="space-y-8 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 py-8 transition-colors duration-200">
      {/* Pending DGCA Benchmark Notice Banner */}
      <div className="app-badge-gold rounded-lg p-4 flex items-start gap-3 shadow-sm">
        <div className="space-y-1 text-xs">
          <p className="font-bold text-[var(--color-gold)]">
            Official DGCA Reference Validation Pending
          </p>
          <p className="app-text-secondary leading-relaxed">
            Validation pipeline is fully operational. Metrics shown below compare reconstructed index series against unit-test sample benchmark fixtures (`SAMPLE_BENCHMARK`). Official Directorate General of Civil Aviation validation will activate upon certified monthly yield data ingestion.
          </p>
        </div>
      </div>

      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b app-border">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold tracking-tight app-text-primary">
              Historical Backtesting & Validation Suite
            </h1>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-md app-badge-teal">
              45-Day Dataset
            </span>
          </div>
          <p className="text-xs app-text-secondary mt-1">
            Reconstructing deterministic index series from verified observed quotes and testing against reference datasets.
          </p>
        </div>

        {/* Method Toggle */}
        <div className="flex items-center app-bg-surface p-1 rounded-md border app-border text-xs">
          <button
            onClick={() => setMethod("Dutot")}
            className={`px-3 py-1 rounded-md font-medium transition-all ${
              method === "Dutot"
                ? "bg-[#284269] text-[#F5F3EC] shadow-sm font-bold border border-[#1E2A44]"
                : "app-text-secondary hover:app-text-primary"
            }`}
          >
            Dutot (Arithmetic)
          </button>
          <button
            onClick={() => setMethod("Jevons")}
            className={`px-3 py-1 rounded-md font-medium transition-all ${
              method === "Jevons"
                ? "bg-[#284269] text-[#F5F3EC] shadow-sm font-bold border border-[#1E2A44]"
                : "app-text-secondary hover:app-text-primary"
            }`}
          >
            Jevons (Geometric)
          </button>
        </div>
      </div>

      {isLoading ? (
        <LoadingState message="Reconstructing 45-day historical index series and running validation models..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchValidation} />
      ) : !backtestData ? (
        <EmptyState title="No Backtest Results" description="Generate reference points to run validation." />
      ) : (
        <>
          {/* Statistical Validation KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div className="app-card-blue-1 rounded-xl p-4 shadow-sm space-y-1 transition-transform hover:-translate-y-0.5">
              <span className="text-[10px] uppercase font-semibold text-[#1E2A44]">Mean Abs Error (MAE)</span>
              <div className="text-xl font-bold text-[#1E2A44] font-mono">{m?.mae?.toFixed(3) ?? "N/A"} pts</div>
              <p className="text-[10px] text-[#7D8CA3]">Target: &lt; 5.0 pts</p>
            </div>

            <div className="app-card-blue-2 rounded-xl p-4 shadow-sm space-y-1 transition-transform hover:-translate-y-0.5">
              <span className="text-[10px] uppercase font-semibold text-[#1E2A44]">Root Mean Sq Err (RMSE)</span>
              <div className="text-xl font-bold text-[#DC2626] font-mono">{m?.rmse?.toFixed(3) ?? "N/A"} pts</div>
              <p className="text-[10px] text-[#7D8CA3]">Variance penalty</p>
            </div>

            <div className="app-card-blue-3 rounded-xl p-4 shadow-sm space-y-1 transition-transform hover:-translate-y-0.5">
              <span className="text-[10px] uppercase font-semibold text-[#1E2A44]">Mean Abs % Err (MAPE)</span>
              <div className="text-xl font-bold text-[#15803D] font-mono">{m?.mape?.toFixed(2) ?? "N/A"}%</div>
              <p className="text-[10px] text-[#7D8CA3]">Relative error</p>
            </div>

            <div className="app-card-blue-4 rounded-xl p-4 shadow-sm space-y-1 transition-transform hover:-translate-y-0.5">
              <span className="text-[10px] uppercase font-semibold text-[#1E2A44]">Pearson Correlation (r)</span>
              <div className="text-xl font-bold text-[#15803D] font-mono">{m?.pearson_corr?.toFixed(3) ?? "N/A"}</div>
              <p className="text-[10px] text-[#7D8CA3]">Trend alignment</p>
            </div>

            <div className="app-card-blue-1 rounded-xl p-4 shadow-sm space-y-1 transition-transform hover:-translate-y-0.5">
              <span className="text-[10px] uppercase font-semibold text-[#1E2A44]">Directional Agreement</span>
              <div className="text-xl font-bold text-[#1E2A44] font-mono">{m?.directional_agreement_pct?.toFixed(1) ?? "N/A"}%</div>
              <p className="text-[10px] text-[#7D8CA3]">Sign concordance</p>
            </div>
          </div>

          {/* Reconstructed Historical Series Chart */}
          <div className="space-y-3">
            <h2 className="text-base font-semibold app-text-primary">
              Reconstructed 45-Day Composite Series ({method} • Base {backtestData.base_period} = 100.0)
            </h2>
            <InteractiveIndexChart
              data={chartData}
              title={`Historical Backtest Trajectory (${dailySeries.length} Daily Points)`}
              valueSuffix=" pts"
              height={260}
              baseLineValue={100}
              accentColor="gold"
            />
          </div>

          {/* Sensitivity Analysis Scenario Comparison */}
          {sens && (
            <div className="space-y-4">
              <h2 className="text-base font-semibold app-text-primary flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[var(--color-rose)]" />
                Sensitivity Scenarios (Robustness Testing)
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="app-bg-card border border-[var(--color-teal)] rounded-lg p-4 shadow-sm space-y-2">
                  <div className="flex items-center justify-between text-xs font-bold app-text-primary">
                    <span>Baseline (Clean Fares)</span>
                    <span className="app-badge-teal text-[10px] px-1.5 py-0.5 rounded">Production</span>
                  </div>
                  <div className="text-2xl font-extrabold text-[var(--color-teal)] font-mono">
                    {sens.baseline_mean_index?.toFixed(2)} pts
                  </div>
                  <p className="text-[11px] app-text-muted">
                    Deterministic reconstruction with 3-Sigma & IQR outlier rejection active.
                  </p>
                </div>

                <div className="app-bg-card border border-[var(--color-rose)] rounded-lg p-4 shadow-sm space-y-2">
                  <div className="flex items-center justify-between text-xs font-bold app-text-primary">
                    <span>Unfiltered (With Outliers)</span>
                    <span className="app-badge-rose text-[10px] px-1.5 py-0.5 rounded">Stress Test</span>
                  </div>
                  <div className="text-2xl font-extrabold text-[var(--color-rose)] font-mono">
                    {sens.unfiltered_outliers_mean_index ? `${sens.unfiltered_outliers_mean_index.toFixed(2)} pts` : "N/A"}
                  </div>
                  <p className="text-[11px] app-text-muted">
                    Raw unfiltered dataset including extreme non-market deviations.
                  </p>
                </div>

                <div className="app-bg-card border border-[var(--color-gold)] rounded-lg p-4 shadow-sm space-y-2">
                  <div className="flex items-center justify-between text-xs font-bold app-text-primary">
                    <span>Estimated Inclusive</span>
                    <span className="app-badge-gold text-[10px] px-1.5 py-0.5 rounded">Fallback Test</span>
                  </div>
                  <div className="text-2xl font-extrabold text-[var(--color-gold)] font-mono">
                    {sens.estimated_inclusive_mean_index ? `${sens.estimated_inclusive_mean_index.toFixed(2)} pts` : "N/A"}
                  </div>
                  <p className="text-[11px] app-text-muted">
                    Dataset incorporating fallback model estimates.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Route-Level Validation Metrics */}
          {routeValidation && (
            <div className="space-y-4">
              <h2 className="text-base font-semibold app-text-primary">
                Corridor Level Benchmark Validation
              </h2>

              {/* Desktop Table View (Full Columns, Clean, No Chevrons) */}
              <div className="hidden md:block app-bg-card border app-border rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="app-bg-surface border-b app-border text-[11px] font-semibold app-text-secondary uppercase tracking-wider">
                    <tr>
                      <th className="px-5 py-3.5">Corridor</th>
                      <th className="px-5 py-3.5">Days Monitored</th>
                      <th className="px-5 py-3.5 text-right">Our Mean Index</th>
                      <th className="px-5 py-3.5 text-right">Ref Benchmark</th>
                      <th className="px-5 py-3.5 text-right">Difference</th>
                      <th className="px-5 py-3.5 text-right">% Difference</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y app-border-subtle app-text-primary font-mono">
                    {routeValidation.routes.map((r) => (
                      <tr key={r.route} className="hover:app-bg-surface/70 transition-colors">
                        <td className="px-5 py-3.5 font-sans font-bold app-text-primary">{r.route}</td>
                        <td className="px-5 py-3.5">{r.days_observed} days</td>
                        <td className="px-5 py-3.5 text-right font-bold text-[var(--color-gold)]">
                          {r.our_mean_index.toFixed(2)} pts
                        </td>
                        <td className="px-5 py-3.5 text-right app-text-secondary">
                          {r.reference_benchmark_value ? `${r.reference_benchmark_value.toFixed(2)} pts` : "N/A"}
                        </td>
                        <td className="px-5 py-3.5 text-right text-[var(--color-rose)] font-bold">
                          {r.difference !== null ? `${r.difference.toFixed(2)} pts` : "N/A"}
                        </td>
                        <td className="px-5 py-3.5 text-right text-[var(--color-teal)] font-bold">
                          {r.pct_difference !== null ? `${r.pct_difference.toFixed(2)}%` : "N/A"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile & Tablet Expandable Table View (Zero-Scroll with Click-to-Expand) */}
              <div className="md:hidden app-bg-card border app-border rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="app-bg-surface border-b app-border text-[11px] font-semibold app-text-secondary uppercase tracking-wider">
                    <tr>
                      <th className="px-3 py-3">Corridor</th>
                      <th className="px-2 py-3 text-center">Mean</th>
                      <th className="px-3 py-3 text-right">% Diff</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y app-border-subtle app-text-primary font-mono">
                    {routeValidation.routes.map((r) => {
                      const isExpanded = !!expandedRoutes[r.route];
                      return (
                        <React.Fragment key={r.route}>
                          <tr
                            onClick={() => toggleRoute(r.route)}
                            className="hover:app-bg-surface/70 transition-colors cursor-pointer select-none"
                          >
                            <td className="px-3 py-3 font-sans font-bold app-text-primary">
                              <div className="flex items-center gap-1.5">
                                {isExpanded ? (
                                  <ChevronDown className="w-3.5 h-3.5 text-[var(--color-gold)] flex-shrink-0" />
                                ) : (
                                  <ChevronRight className="w-3.5 h-3.5 app-text-muted flex-shrink-0" />
                                )}
                                <span>{r.route}</span>
                              </div>
                            </td>
                            <td className="px-2 py-3 text-center font-bold text-[var(--color-gold)]">
                              {r.our_mean_index.toFixed(1)}
                            </td>
                            <td className="px-3 py-3 text-right font-bold text-[var(--color-teal)]">
                              {r.pct_difference !== null ? `${r.pct_difference.toFixed(1)}%` : "N/A"}
                            </td>
                          </tr>

                          {/* Expandable Details Sub-row */}
                          {isExpanded && (
                            <tr className="app-bg-surface/60 border-t border-b app-border-subtle">
                              <td colSpan={3} className="px-3.5 py-3 text-xs">
                                <div className="grid grid-cols-2 gap-2.5 font-mono">
                                  <div>
                                    <span className="text-[9px] uppercase font-semibold app-text-muted block">
                                      Benchmark
                                    </span>
                                    <span className="text-[11px] app-text-primary">
                                      {r.reference_benchmark_value ? `${r.reference_benchmark_value.toFixed(2)} pts` : "N/A"}
                                    </span>
                                  </div>
                                  <div>
                                    <span className="text-[9px] uppercase font-semibold app-text-muted block">
                                      Difference
                                    </span>
                                    <span className="text-[11px] font-bold text-[var(--color-rose)]">
                                      {r.difference !== null ? `${r.difference.toFixed(2)} pts` : "N/A"}
                                    </span>
                                  </div>
                                  <div className="col-span-2">
                                    <span className="text-[9px] uppercase font-semibold app-text-muted block">
                                      Observation Span
                                    </span>
                                    <span className="text-[11px] app-text-primary">
                                      {r.days_observed} monitored calendar days
                                    </span>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
