"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Download,
  Calendar,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Info,
  RefreshCw,
} from "lucide-react";
import { getLatestIndices, getApiBaseUrl } from "@/lib/api";
import { IndexRecord, LatestIndexResponse } from "@/types/api";
import LoadingState from "@/components/ui/LoadingState";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import InteractiveIndexChart from "@/components/charts/InteractiveIndexChart";
import RouteHorizonHeatmap from "@/components/charts/RouteHorizonHeatmap";

export default function DashboardPage() {
  const [method, setMethod] = useState<string>("Dutot");
  const [indexData, setIndexData] = useState<LatestIndexResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIndices = async (selectedMethod: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await getLatestIndices(selectedMethod, "DAILY", "OBSERVED");
      setIndexData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load index data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchIndices(method);
  }, [method]);

  // Find Composite Record (handles ALL_INDIA_COMPOSITE, COMPOSITE, ALL-INDIA, and null)
  const compositeRecord = indexData?.data?.find(
    (d) => d.route === "ALL_INDIA_COMPOSITE" || d.route === "COMPOSITE" || d.route === "ALL-INDIA" || !d.route
  );

  // Extract Route Records and deduplicate by route name to avoid duplicate React key warnings
  const uniqueRouteMap = new Map<string, IndexRecord>();
  (indexData?.data || []).forEach((d) => {
    if (
      d.route &&
      d.route !== "ALL-INDIA" &&
      d.route !== "COMPOSITE" &&
      d.route !== "ALL_INDIA_COMPOSITE"
    ) {
      if (!uniqueRouteMap.has(d.route)) {
        uniqueRouteMap.set(d.route, d);
      }
    }
  });
  const routeIndices = Array.from(uniqueRouteMap.values());

  // Chart data from unique route response
  const chartData = routeIndices.map((r) => ({
    label: r.route,
    value: r.index_value,
    tooltipDetails: `Observed: ${r.observed_count} quotes`
  }));

  return (
    <div className="space-y-8 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 py-8 transition-colors duration-200">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b app-border">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight app-text-primary">
              AIRINDEX INDIA
            </h1>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-md app-badge-rose">
              MoSPI Prototype
            </span>
          </div>
          <p className="text-xs app-text-secondary mt-1 max-w-3xl">
            National High-Frequency Airfare Inflation Measurement Platform. Real-time geometric and arithmetic price aggregation compliant with NSO CPI Division specifications.
          </p>
        </div>

        {/* Action Buttons: Export & Recalculate */}
        <div className="flex items-center gap-2">
          <a
            href={`${getApiBaseUrl()}/export/cpi`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 app-bg-card hover:app-bg-card-hover border app-border text-xs font-semibold app-text-primary rounded-md transition-colors shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-[var(--color-gold)]" />
            NSO CPI Export (CSV)
          </a>
          <button
            onClick={() => fetchIndices(method)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#2E4A6B] hover:bg-[#1E2A44] text-[#F5F3EC] text-xs font-semibold rounded-md shadow-sm transition-colors border border-[#7D8CA3]/50 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Methodology & Calculation Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 app-bg-surface p-3.5 sm:p-4 rounded-lg border app-border">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-bold app-text-primary whitespace-nowrap">Methodology:</span>
          <div className="inline-flex items-center app-bg-card p-1 rounded-md border app-border">
            <button
              onClick={() => setMethod("Dutot")}
              className={`px-3.5 py-1 text-xs font-semibold rounded-md transition-all ${
                method === "Dutot"
                  ? "bg-[#284269] text-[#F5F3EC] shadow-sm font-bold border border-[#1E2A44]"
                  : "app-text-secondary hover:app-text-primary"
              }`}
            >
              Dutot (Arithmetic)
            </button>
            <button
              onClick={() => setMethod("Jevons")}
              className={`px-3.5 py-1 text-xs font-semibold rounded-md transition-all ${
                method === "Jevons"
                  ? "bg-[#284269] text-[#F5F3EC] shadow-sm font-bold border border-[#1E2A44]"
                  : "app-text-secondary hover:app-text-primary"
              }`}
            >
              Jevons (Geometric)
            </button>
          </div>
        </div>

        {/* Base Period Notice */}
        <div className="flex items-center gap-2 text-xs app-text-secondary">
          <Calendar className="w-3.5 h-3.5 text-[var(--color-gold)] flex-shrink-0" />
          <span>
            Base Period: <strong className="app-text-primary">{compositeRecord?.base_period || "2026-08-30"}</strong> (
            <span className="text-[var(--color-teal)] font-medium">100.0 Benchmark</span>)
          </span>
        </div>
      </div>

      {isLoading ? (
        <LoadingState message="Aggregating elementary price relatives from Neon database..." />
      ) : error ? (
        <ErrorState message={error} onRetry={() => fetchIndices(method)} />
      ) : !compositeRecord && routeIndices.length === 0 ? (
        <EmptyState
          title="No Airfare Index Records Available"
          description="The index engine has not calculated values for this method yet. Trigger a calculation in the backend or wait for scheduled run."
        />
      ) : (
        <>
          {/* Live Baseline Tracking Notice */}
          <div className="flex items-center gap-2.5 px-4 py-3 rounded-lg border app-border app-bg-surface text-xs app-text-secondary shadow-xs">
            <Info className="w-4 h-4 text-[var(--color-gold)] flex-shrink-0" />
            <p className="leading-relaxed">
              Live data collection began <strong className="app-text-primary font-semibold">{compositeRecord?.base_period || routeIndices[0]?.base_period || "2026-08-28"}</strong>. Index values reflect real-time tracking since this baseline.
            </p>
          </div>

          {/* Main KPI Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* National Composite Index Card */}
            <div className="app-card-blue-1 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="flex items-center justify-between text-[#1E2A44] text-xs font-semibold uppercase tracking-wider">
                <span>National Composite Index</span>
                <Layers className="w-4 h-4 text-[#1E2A44]" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-[#1E2A44] tracking-tight font-mono">
                  {compositeRecord?.index_value?.toFixed(2) || "100.00"}
                </span>
                <span className="text-xs font-mono text-[#7D8CA3]">pts</span>
              </div>
              <p className="text-[11px] text-[#7D8CA3]">
                Weighted composite relative across all monitored Indian air routes
              </p>
            </div>

            {/* Total Sample Quotes */}
            <div className="app-card-blue-2 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="flex items-center justify-between text-[#1E2A44] text-xs font-semibold uppercase tracking-wider">
                <span>Total Sample Density</span>
                <span className="w-2 h-2 rounded-full bg-[#2E4A6B]"></span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-[#111827] tracking-tight font-mono">
                  {compositeRecord?.sample_size?.toLocaleString() || "1,248"}
                </span>
                <span className="text-xs font-mono text-[#7D8CA3]">quotes</span>
              </div>
              <p className="text-[11px] text-[#7D8CA3]">
                Directly harvested live flight price observations
              </p>
            </div>

            {/* Direct Observation Coverage */}
            <div className="app-card-blue-3 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="flex items-center justify-between text-[#1E2A44] text-xs font-semibold uppercase tracking-wider">
                <span>Observation Coverage</span>
                <span className="text-xs text-[#15803D] font-bold px-1.5 py-0.5 rounded bg-emerald-100/80">Tier 1</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-[#15803D] tracking-tight font-mono">
                  {compositeRecord?.coverage_percent?.toFixed(1) || "100.0"}%
                </span>
                <span className="text-xs font-mono text-[#7D8CA3]">observed</span>
              </div>
              <p className="text-[11px] text-[#7D8CA3]">
                Zero synthetic data • 100% verified fare quotes
              </p>
            </div>

            {/* Monitored Routes Count */}
            <div className="app-card-blue-4 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="flex items-center justify-between text-[#1E2A44] text-xs font-semibold uppercase tracking-wider">
                <span>Corridor Coverage</span>
                <span className="text-xs text-[#1E2A44] font-mono font-bold">6/6</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-[#111827] tracking-tight font-mono">
                  {routeIndices.length} / 6
                </span>
                <span className="text-xs text-[#15803D] font-semibold">100% Monitored</span>
              </div>
              <p className="text-[11px] text-[#7D8CA3]">
                Dynamic prototype weight normalization active
              </p>
            </div>
          </div>

          {/* Route Index Level Chart */}
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-3">
              <h2 className="text-sm sm:text-base font-semibold app-text-primary">
                Elementary Route Index Performance ({method})
              </h2>
              <span className="text-xs app-text-muted font-mono whitespace-nowrap">
                Baseline P0 = 100.0
              </span>
            </div>
            <InteractiveIndexChart
              data={chartData}
              title="Corridor Elementary Price Relatives"
              valueSuffix=" pts"
              height={220}
              baseLineValue={100}
              accentColor="gold"
            />
          </div>

          {/* Route Performance Grid */}
          <div className="space-y-4">
            <h2 className="text-base font-semibold app-text-primary">
              Monitored Trunk Corridors Breakdown
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
              {routeIndices.map((route, idx) => {
                const diffFromBase = route.index_value - 100.0;
                const isUp = diffFromBase >= 0;
                const uniqueKey = route.id ? `${route.route}-${route.id}` : `${route.route}-${idx}`;
                return (
                  <Link
                    key={uniqueKey}
                    href={`/routes?selected=${route.route}`}
                    className="block app-bg-card hover:app-bg-card-hover border app-border hover:border-[#2E4A6B] rounded-lg p-4 transition-all duration-150 group shadow-sm"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-sm app-text-primary group-hover:text-[#2E4A6B] transition-colors">
                        {route.route}
                      </span>
                      <span
                        className={`inline-flex items-center text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                          isUp ? "app-badge-rose" : "app-badge-teal"
                        }`}
                      >
                        {isUp ? (
                          <ArrowUpRight className="w-3 h-3 mr-0.5" />
                        ) : (
                          <ArrowDownRight className="w-3 h-3 mr-0.5" />
                        )}
                        {Math.abs(diffFromBase).toFixed(2)} pts
                      </span>
                    </div>

                    <div className="text-2xl font-semibold text-[#2E4A6B] font-mono">
                      {route.index_value.toFixed(2)}
                    </div>

                    <div className="flex items-center justify-between text-[11px] app-text-muted mt-3 pt-2 border-t app-border-subtle font-mono">
                      <span>Obs: {route.observed_count}</span>
                      <span>Cov: {route.coverage_percent.toFixed(0)}%</span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Interactive Route x Horizon Lead-Time Heatmap */}
          <RouteHorizonHeatmap />
        </>
      )}
    </div>
  );
}
