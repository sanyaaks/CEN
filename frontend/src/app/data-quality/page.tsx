"use client";

import { useEffect, useState } from "react";
import { getAuditSummary, getSourcesHealth } from "@/lib/api";
import { AuditSummaryResponse, SourcesHealthResponse } from "@/types/api";
import LoadingState from "@/components/ui/LoadingState";
import ErrorState from "@/components/ui/ErrorState";

export default function DataQualityPage() {
  const [auditSummary, setAuditSummary] = useState<AuditSummaryResponse | null>(null);
  const [sourcesHealth, setSourcesHealth] = useState<SourcesHealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQualityData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [audit, health] = await Promise.all([
        getAuditSummary(),
        getSourcesHealth()
      ]);
      setAuditSummary(audit);
      setSourcesHealth(health);
    } catch (err: any) {
      setError(err.message || "Failed to load data quality statistics.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQualityData();
  }, []);

  const summary = auditSummary?.summary;
  const sources = sourcesHealth?.sources || [];
  const healthySources = sources.filter((s) => s.health.status === "HEALTHY").length;
  const sourceCoveragePct = sources.length > 0 ? (healthySources / sources.length) * 100 : 0;

  return (
    <div className="space-y-8 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 py-8 transition-colors duration-200">
      {/* Header */}
      <div className="pb-6 border-b app-border">
        <h1 className="text-2xl font-extrabold tracking-tight app-text-primary">
          Data Quality & Governance Audit
        </h1>
        <p className="text-xs app-text-secondary mt-1">
          Provenance transparency, outlier detection rate, fare decomposition status, and multi-tier coverage metrics.
        </p>
      </div>

      {isLoading ? (
        <LoadingState message="Verifying database integrity and quality metrics..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchQualityData} />
      ) : !summary ? (
        <ErrorState message="Quality audit response is empty." />
      ) : (
        <>
          {/* Data Coverage & Quality Overview */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold app-text-secondary uppercase tracking-wider">
              Data Coverage & Quality Overview
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Tier 1 */}
              <div className="app-bg-card border app-border rounded-lg p-5 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold app-text-secondary">
                  <span>Direct Observation Rate</span>
                  <span className="text-[10px] app-badge-teal px-1.5 py-0.5 rounded font-mono font-semibold">Tier 1</span>
                </div>
                <div className="text-3xl font-semibold text-[var(--color-teal)] font-mono tracking-tight">
                  {summary.observed_coverage_pct.toFixed(1)}%
                </div>
                <p className="text-[11px] app-text-muted">
                  {summary.total_observed_quotes} observed prices • {summary.total_estimated_quotes} model estimates
                </p>
              </div>

              {/* Tier 2 */}
              <div className="app-bg-card border app-border rounded-lg p-5 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold app-text-secondary">
                  <span>Route Network Coverage</span>
                  <span className="text-[10px] app-badge-gold px-1.5 py-0.5 rounded font-mono font-semibold">Tier 2</span>
                </div>
                <div className="text-3xl font-semibold app-text-primary font-mono tracking-tight">
                  6 / 6 Corridors
                </div>
                <p className="text-[11px] app-text-muted">
                  100% of major Indian domestic trunk routes actively tracked
                </p>
              </div>

              {/* Tier 3 */}
              <div className="app-bg-card border app-border rounded-lg p-5 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold app-text-secondary">
                  <span>Data Source Availability</span>
                  <span className="text-[10px] app-badge-rose px-1.5 py-0.5 rounded font-mono font-semibold">Tier 3</span>
                </div>
                <div className="text-3xl font-semibold text-[var(--color-teal)] font-mono tracking-tight">
                  {sourceCoveragePct.toFixed(0)}% Online
                </div>
                <p className="text-[11px] app-text-muted">
                  {healthySources} of {sources.length} collection sources operating normally
                </p>
              </div>
            </div>
          </div>

          {/* Outlier & Decomposition Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Outlier Card */}
            <div className="app-card-blue-1 rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-[#1E2A44]">
                  Statistical Outlier Isolation (3-Sigma + IQR)
                </h3>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                <div>
                  <span className="text-[10px] text-[#7D8CA3] block">Outliers Flagged</span>
                  <span className="text-2xl font-bold text-[#DC2626]">
                    {summary.total_outliers_flagged}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-[#7D8CA3] block">Rejection Rate</span>
                  <span className="text-2xl font-bold text-[#111827]">
                    {summary.outlier_rate_pct.toFixed(2)}%
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-[#7D8CA3] pt-2 border-t border-[#CBDCEE] leading-relaxed">
                Prices with Z-score &gt; 3.0 or exceeding interquartile fences are automatically excluded from the Dutot and Jevons index relative aggregation to prevent distortion.
              </p>
            </div>

            {/* Fare Decomposition Card */}
            <div className="app-card-blue-2 rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-[#1E2A44]">
                  Fare Decomposition Transparency
                </h3>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs font-mono pt-1">
                <div>
                  <span className="text-[10px] text-[#7D8CA3] block">Unavailable</span>
                  <span className="text-xl font-bold text-[#1E2A44]">
                    {summary.fare_decomposition_breakdown.unavailable}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-[#7D8CA3] block">Exact</span>
                  <span className="text-xl font-bold text-[#15803D]">
                    {summary.fare_decomposition_breakdown.exact}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-[#7D8CA3] block">Partial</span>
                  <span className="text-xl font-bold text-[#111827]">
                    {summary.fare_decomposition_breakdown.partial}
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-[#7D8CA3] pt-2 border-t border-[#CBDCEE] leading-relaxed">
                Zero arbitrary flat GST assumptions applied. When itemized tax breakdowns are not exposed by aggregators, status is recorded as UNAVAILABLE.
              </p>
            </div>
          </div>

          {/* Database Provenance Counts */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold app-text-secondary uppercase tracking-wider">
              Database Provenance Counts
            </h2>
            <div className="app-bg-surface border app-border rounded-lg p-5 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div>
                <span className="app-text-muted block text-[10px]">Total Scraped Raw Payloads</span>
                <span className="text-xl font-bold app-text-primary">{summary.total_raw_scrapes}</span>
              </div>
              <div>
                <span className="app-text-muted block text-[10px]">Total Normalized Quotes</span>
                <span className="text-xl font-bold app-text-primary">{summary.total_clean_observations}</span>
              </div>
              <div>
                <span className="app-text-muted block text-[10px]">Valid Observed Quotes</span>
                <span className="text-xl font-bold text-[var(--color-teal)]">{summary.total_observed_quotes}</span>
              </div>
              <div>
                <span className="app-text-muted block text-[10px]">Estimated Quotes</span>
                <span className="text-xl font-bold text-[#1E2A44]">{summary.total_estimated_quotes}</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
