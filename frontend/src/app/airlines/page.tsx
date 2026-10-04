"use client";

import React, { useEffect, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { getRouteAudit } from "@/lib/api";
import { CleanObservation } from "@/types/api";
import LoadingState from "@/components/ui/LoadingState";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import AirlineLogo from "@/components/ui/AirlineLogo";

const CONFIGURED_ROUTES = [
  "DEL-BOM",
  "BLR-DEL",
  "DEL-CCU",
  "BOM-BLR",
  "DEL-MAA",
  "HYD-MAA",
];

export default function AirlinesPage() {
  const [observations, setObservations] = useState<CleanObservation[]>([]);
  const [expandedAirlines, setExpandedAirlines] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const toggleAirline = (airline: string) => {
    setExpandedAirlines((prev) => ({ ...prev, [airline]: !prev[airline] }));
  };

  const fetchAirlineStats = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const results = await Promise.all(
        CONFIGURED_ROUTES.map((r) => getRouteAudit(r).catch(() => ({ observations: [] })))
      );
      const allObs = results.flatMap((res) => res.observations || []);
      setObservations(allObs);
    } catch (err: any) {
      setError(err.message || "Failed to load airline observations.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAirlineStats();
  }, []);

  // Aggregate stats per airline
  const airlineData: Record<
    string,
    {
      totalQuotes: number;
      minPrice: number;
      maxPrice: number;
      avgPrice: number;
      outlierCount: number;
      routes: Set<string>;
    }
  > = {};

  observations.forEach((obs) => {
    const airline = obs.airline || "Unknown Carrier";
    if (!airlineData[airline]) {
      airlineData[airline] = {
        totalQuotes: 0,
        minPrice: Infinity,
        maxPrice: -Infinity,
        avgPrice: 0,
        outlierCount: 0,
        routes: new Set<string>(),
      };
    }
    const d = airlineData[airline];
    d.totalQuotes += 1;
    if (obs.total_price < d.minPrice) d.minPrice = obs.total_price;
    if (obs.total_price > d.maxPrice) d.maxPrice = obs.total_price;
    d.avgPrice += obs.total_price;
    if (obs.is_outlier) d.outlierCount += 1;
    d.routes.add(obs.route);
  });

  // Calculate final average prices
  Object.values(airlineData).forEach((d) => {
    if (d.totalQuotes > 0) {
      d.avgPrice = d.avgPrice / d.totalQuotes;
    }
  });

  const totalQuotesAll = Object.values(airlineData).reduce((sum, a) => sum + a.totalQuotes, 0);

  // Calculate overall weighted average price
  const overallAvgPrice =
    totalQuotesAll > 0
      ? Object.values(airlineData).reduce((sum, a) => sum + a.avgPrice * a.totalQuotes, 0) /
        totalQuotesAll
      : 0;

  // Sort airlines by quote volume descending
  const sortedAirlines = Object.entries(airlineData).sort(
    (a, b) => b[1].totalQuotes - a[1].totalQuotes
  );

  return (
    <div className="space-y-8 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 py-8 transition-colors duration-200">
      {/* Header */}
      <div className="pb-6 border-b app-border">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-extrabold tracking-tight app-text-primary">
            Carrier Fleet & Fare Profile
          </h1>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-md app-badge-teal">
            Sample Distribution
          </span>
        </div>
        <p className="text-xs app-text-secondary mt-1">
          Carrier representation, dynamic price ranges, and quote market shares across monitored corridors.
        </p>
      </div>

      {isLoading ? (
        <LoadingState message="Aggregating airline quote distributions..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchAirlineStats} />
      ) : sortedAirlines.length === 0 ? (
        <EmptyState title="No Carrier Data Found" description="Run collection to aggregate quotes." />
      ) : (
        <div className="space-y-8">
          {/* Metrics Overview */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="app-card-blue-1 rounded-xl p-4 shadow-sm transition-transform hover:-translate-y-0.5">
              <span className="text-[11px] font-semibold text-[#1E2A44] uppercase tracking-wider block">
                Total Sampled Quotes
              </span>
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#111827] mt-1">
                {totalQuotesAll.toLocaleString()}
              </div>
              <span className="text-[10px] text-[#7D8CA3] mt-0.5 block">Across 6 monitored corridors</span>
            </div>

            <div className="app-card-blue-2 rounded-xl p-4 shadow-sm transition-transform hover:-translate-y-0.5">
              <span className="text-[11px] font-semibold text-[#1E2A44] uppercase tracking-wider block">
                Active Carriers
              </span>
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#15803D] mt-1">
                {sortedAirlines.length} Airlines
              </div>
              <span className="text-[10px] text-[#7D8CA3] mt-0.5 block">Domestic & scheduled</span>
            </div>

            <div className="app-card-blue-3 rounded-xl p-4 shadow-sm transition-transform hover:-translate-y-0.5">
              <span className="text-[11px] font-semibold text-[#1E2A44] uppercase tracking-wider block">
                Market Leader Share
              </span>
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#1E2A44] mt-1">
                {sortedAirlines.length > 0
                  ? `${((sortedAirlines[0][1].totalQuotes / totalQuotesAll) * 100).toFixed(1)}%`
                  : "0%"}
              </div>
              <span className="text-[10px] text-[#7D8CA3] mt-0.5 block truncate">
                {sortedAirlines[0]?.[0] || "None"}
              </span>
            </div>

            <div className="app-card-blue-4 rounded-xl p-4 shadow-sm transition-transform hover:-translate-y-0.5">
              <span className="text-[11px] font-semibold text-[#1E2A44] uppercase tracking-wider block">
                Weighted Industry Mean
              </span>
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#111827] mt-1">
                ₹{Math.round(overallAvgPrice).toLocaleString()}
              </div>
              <span className="text-[10px] text-[#7D8CA3] mt-0.5 block">Aggregate baseline fare</span>
            </div>
          </div>

          {/* Full Airline Summary Table with Expandable Rows */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold app-text-primary">
                Consolidated Carrier Market Summary
              </h2>
            </div>

            {/* Desktop Table View (Full Columns, Clean, No Chevrons) */}
            <div className="hidden md:block app-bg-card border app-border rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="app-bg-surface border-b app-border text-[11px] font-semibold app-text-secondary uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3.5">Carrier</th>
                    <th className="px-5 py-3.5">Sample Volume</th>
                    <th className="px-5 py-3.5">Quote Share</th>
                    <th className="px-5 py-3.5 text-right">Min Fare</th>
                    <th className="px-5 py-3.5 text-right">Average Fare</th>
                    <th className="px-5 py-3.5 text-right">Max Fare</th>
                    <th className="px-5 py-3.5 text-right">Outlier Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y app-border-subtle app-text-primary font-mono">
                  {sortedAirlines.map(([airline, stats]) => {
                    const share = totalQuotesAll > 0 ? (stats.totalQuotes / totalQuotesAll) * 100 : 0;
                    const outlierRate = stats.totalQuotes > 0 ? (stats.outlierCount / stats.totalQuotes) * 100 : 0;
                    return (
                      <tr key={airline} className="hover:app-bg-surface/70 transition-colors">
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-2.5">
                            <AirlineLogo airline={airline} size="sm" />
                            <span className="font-sans font-bold app-text-primary">{airline}</span>
                          </div>
                        </td>
                        <td className="px-5 py-3.5">{stats.totalQuotes.toLocaleString()} quotes</td>
                        <td className="px-5 py-3.5 font-bold text-[var(--color-gold)]">{share.toFixed(1)}%</td>
                        <td className="px-5 py-3.5 text-right text-[var(--color-teal)]">₹{Math.round(stats.minPrice).toLocaleString()}</td>
                        <td className="px-5 py-3.5 text-right font-bold">₹{Math.round(stats.avgPrice).toLocaleString()}</td>
                        <td className="px-5 py-3.5 text-right text-[var(--color-rose)]">₹{Math.round(stats.maxPrice).toLocaleString()}</td>
                        <td className="px-5 py-3.5 text-right text-[var(--color-rose)]">{outlierRate.toFixed(1)}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile & Tablet Expandable Table View (Zero-Scroll with Click-to-Expand) */}
            <div className="md:hidden app-bg-card border app-border rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="app-bg-surface border-b app-border text-[11px] font-semibold app-text-secondary uppercase tracking-wider">
                  <tr>
                    <th className="px-3 py-3">Carrier</th>
                    <th className="px-2 py-3 text-center">Share</th>
                    <th className="px-3 py-3 text-right">Avg Fare</th>
                  </tr>
                </thead>
                <tbody className="divide-y app-border-subtle app-text-primary font-mono">
                  {sortedAirlines.map(([airline, stats]) => {
                    const share = totalQuotesAll > 0 ? (stats.totalQuotes / totalQuotesAll) * 100 : 0;
                    const outlierRate = stats.totalQuotes > 0 ? (stats.outlierCount / stats.totalQuotes) * 100 : 0;
                    const isExpanded = !!expandedAirlines[airline];
                    return (
                      <React.Fragment key={airline}>
                        <tr
                          onClick={() => toggleAirline(airline)}
                          className="hover:app-bg-surface/70 transition-colors cursor-pointer select-none"
                        >
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-1.5">
                              {isExpanded ? (
                                <ChevronDown className="w-3.5 h-3.5 text-[var(--color-gold)] flex-shrink-0" />
                              ) : (
                                <ChevronRight className="w-3.5 h-3.5 app-text-muted flex-shrink-0" />
                              )}
                              <AirlineLogo airline={airline} size="sm" />
                              <span className="font-sans font-bold app-text-primary truncate max-w-[95px]">
                                {airline}
                              </span>
                            </div>
                          </td>
                          <td className="px-2 py-3 text-center font-bold text-[var(--color-gold)]">
                            {share.toFixed(1)}%
                          </td>
                          <td className="px-3 py-3 text-right font-bold">
                            ₹{Math.round(stats.avgPrice).toLocaleString()}
                          </td>
                        </tr>

                        {/* Expandable Details Sub-row */}
                        {isExpanded && (
                          <tr className="app-bg-surface/60 border-t border-b app-border-subtle">
                            <td colSpan={3} className="px-3.5 py-3 text-xs">
                              <div className="grid grid-cols-2 gap-2.5 font-mono">
                                <div>
                                  <span className="text-[9px] uppercase font-semibold app-text-muted block">
                                    Min Fare
                                  </span>
                                  <span className="text-xs font-bold text-[var(--color-teal)]">
                                    ₹{Math.round(stats.minPrice).toLocaleString()}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[9px] uppercase font-semibold app-text-muted block">
                                    Max Fare
                                  </span>
                                  <span className="text-xs font-bold text-[var(--color-rose)]">
                                    ₹{Math.round(stats.maxPrice).toLocaleString()}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[9px] uppercase font-semibold app-text-muted block">
                                    Sample Volume
                                  </span>
                                  <span className="text-[11px] app-text-primary">
                                    {stats.totalQuotes.toLocaleString()} quotes ({stats.routes.size} corridors)
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[9px] uppercase font-semibold app-text-muted block">
                                    Outlier Rate
                                  </span>
                                  <span className="text-[11px] app-text-primary">
                                    {stats.outlierCount} outliers ({outlierRate.toFixed(1)}%)
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
        </div>
      )}
    </div>
  );
}
