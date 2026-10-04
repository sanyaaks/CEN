"use client";

import React, { useEffect, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { getRouteIndexHistory, getRouteAudit } from "@/lib/api";
import { IndexRecord, CleanObservation } from "@/types/api";
import LoadingState from "@/components/ui/LoadingState";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import InteractiveIndexChart from "@/components/charts/InteractiveIndexChart";
import AirlineLogo from "@/components/ui/AirlineLogo";
import RouteSearchSelect from "@/components/ui/RouteSearchSelect";

const CONFIGURED_ROUTES = [
  "DEL-BOM",
  "BLR-DEL",
  "DEL-CCU",
  "BOM-BLR",
  "DEL-MAA",
  "HYD-MAA",
];

const AIRLINE_NAMES: Record<string, string> = {
  "6E": "IndiGo",
  "AI": "Air India",
  "SG": "SpiceJet",
  "QP": "Akasa Air",
  "IX": "Air India Express",
  "UK": "Vistara",
  "EK": "Emirates",
  "TG": "Thai Airways",
  "UL": "SriLankan Airlines",
  "WY": "Oman Air",
};

export default function RouteExplorerPage() {
  const [selectedRoute, setSelectedRoute] = useState<string>("DEL-BOM");
  const [method, setMethod] = useState<string>("Dutot");
  const [history, setHistory] = useState<IndexRecord[]>([]);
  const [quotes, setQuotes] = useState<CleanObservation[]>([]);
  const [expandedCodes, setExpandedCodes] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const toggleCode = (code: string) => {
    setExpandedCodes((prev) => ({ ...prev, [code]: !prev[code] }));
  };

  const fetchRouteData = async (route: string, m: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const [historyRes, auditRes] = await Promise.all([
        getRouteIndexHistory(route, m),
        getRouteAudit(route),
      ]);
      setHistory(historyRes.history || []);
      setQuotes(auditRes.observations || []);
    } catch (err: any) {
      setError(err.message || "Failed to load route data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRouteData(selectedRoute, method);
  }, [selectedRoute, method]);

  // Aggregate prices
  const validPrices = quotes.map((q) => q.total_price);
  const minPrice = validPrices.length ? Math.min(...validPrices) : 0;
  const maxPrice = validPrices.length ? Math.max(...validPrices) : 0;
  const avgPrice = validPrices.length ? validPrices.reduce((a, b) => a + b, 0) / validPrices.length : 0;

  // Chart data
  const chartPoints = history.map((h) => ({
    label: h.date,
    value: h.index_value,
    tooltipDetails: `Observed Sample: ${h.observed_count} quotes`
  }));

  // Airline breakdown counts
  const airlineCounts: Record<string, { count: number; sum: number }> = {};
  quotes.forEach((q) => {
    const code = q.airline || "Unknown";
    if (!airlineCounts[code]) {
      airlineCounts[code] = { count: 0, sum: 0 };
    }
    airlineCounts[code].count += 1;
    airlineCounts[code].sum += q.total_price;
  });

  return (
    <div className="space-y-8 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 py-8 transition-colors duration-200">
      {/* Route Header & Selection */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b app-border">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold tracking-tight app-text-primary">
              Corridor Deep Dive: {selectedRoute}
            </h1>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-md app-badge-teal">
              Active Monitored Corridor
            </span>
          </div>
          <p className="text-xs app-text-secondary mt-1">
            Historical price index series, ticket price yields, and operating carrier market share on this trunk route.
          </p>
        </div>

        {/* Controls: Route Dropdown & Calculation Method */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Corridor Dropdown with Search */}
          <div className="w-64">
            <RouteSearchSelect
              value={selectedRoute}
              onChange={setSelectedRoute}
              compact
            />
          </div>

          {/* Method Selector */}
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
      </div>

      {isLoading ? (
        <LoadingState message={`Fetching statistical metrics for ${selectedRoute}...`} />
      ) : error ? (
        <ErrorState message={error} onRetry={() => fetchRouteData(selectedRoute, method)} />
      ) : (
        <>
          {/* Key Pricing Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="app-card-blue-1 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="text-xs font-semibold text-[#1E2A44] uppercase">Average Observed Fare</div>
              <div className="text-2xl font-bold text-[#1E2A44] font-mono">
                ₹{avgPrice.toFixed(0)}
              </div>
              <p className="text-[11px] text-[#7D8CA3]">Based on {quotes.length} valid quotes</p>
            </div>

            <div className="app-card-blue-2 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="text-xs font-semibold text-[#1E2A44] uppercase">Min Observed Fare</div>
              <div className="text-2xl font-bold text-[#15803D] font-mono">
                ₹{minPrice.toFixed(0)}
              </div>
              <p className="text-[11px] text-[#7D8CA3]">Best available scheduled seat</p>
            </div>

            <div className="app-card-blue-3 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="text-xs font-semibold text-[#1E2A44] uppercase">Max Observed Fare</div>
              <div className="text-2xl font-bold text-[#DC2626] font-mono">
                ₹{maxPrice.toFixed(0)}
              </div>
              <p className="text-[11px] text-[#7D8CA3]">Peak departure / last-minute seat</p>
            </div>

            <div className="app-card-blue-4 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="text-xs font-semibold text-[#1E2A44] uppercase">Air Carriers Active</div>
              <div className="text-2xl font-bold text-[#111827] font-mono">
                {Object.keys(airlineCounts).length}
              </div>
              <p className="text-[11px] text-[#7D8CA3]">Competing on {selectedRoute}</p>
            </div>
          </div>

          {/* Time-Series Index Chart */}
          <div className="space-y-3">
            <h2 className="text-sm sm:text-base font-semibold app-text-primary">
              Corridor Historical Index Trajectory ({selectedRoute} • {method})
            </h2>
            <InteractiveIndexChart
              data={chartPoints}
              title={`Elementary Price Relative: ${selectedRoute}`}
              valueSuffix=" pts"
              height={260}
              baseLineValue={100}
              accentColor="gold"
            />
          </div>

          {/* Airline Distribution on this Corridor */}
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <h2 className="text-base font-semibold app-text-primary">
                Carrier Distribution & Market Quote Shares
              </h2>
              <span className="text-xs app-text-muted">
                {Object.keys(airlineCounts).length} Active Carriers Sampled
              </span>
            </div>

            {/* Desktop Table View (Full Columns, Clean, No Chevrons) */}
            <div className="hidden md:block app-bg-card border app-border rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="app-bg-surface border-b app-border text-[11px] font-semibold app-text-secondary uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3.5">Carrier</th>
                    <th className="px-5 py-3.5">Quotes Sampled</th>
                    <th className="px-5 py-3.5 min-w-[200px]">Market Quote Share</th>
                    <th className="px-5 py-3.5 text-right">Avg Fare</th>
                  </tr>
                </thead>
                <tbody className="divide-y app-border-subtle app-text-primary">
                  {Object.entries(airlineCounts).map(([code, stat]) => {
                    const share = quotes.length ? (stat.count / quotes.length) * 100 : 0;
                    const avg = stat.count ? stat.sum / stat.count : 0;
                    const airlineName = AIRLINE_NAMES[code] || code;
                    return (
                      <tr key={code} className="hover:app-bg-surface/70 transition-colors">
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-3">
                            <AirlineLogo airline={code} size="md" />
                            <div className="flex items-center gap-1.5 min-w-0">
                              <span className="font-bold app-text-primary text-xs truncate">
                                {airlineName}
                              </span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded app-bg-surface border app-border-subtle app-text-muted font-normal flex-shrink-0">
                                {code}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-3.5 font-mono text-xs app-text-secondary">
                          <span className="font-semibold app-text-primary">{stat.count}</span> quotes
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-3">
                            <div className="w-36 bg-slate-200 dark:bg-slate-700/60 rounded-full h-2 overflow-hidden border app-border-subtle flex-shrink-0">
                              <div
                                className="bg-[var(--color-gold)] h-2 rounded-full transition-all duration-300"
                                style={{ width: `${Math.max(share, 2)}%` }}
                              ></div>
                            </div>
                            <span className="text-xs font-mono font-semibold app-text-primary tabular-nums w-12 text-right flex-shrink-0">
                              {share.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-5 py-3.5 text-right font-mono font-semibold text-xs text-[var(--color-gold)]">
                          ₹{avg.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                        </td>
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
                    <th className="px-2 py-3 min-w-[110px]">Share</th>
                    <th className="px-3 py-3 text-right">Avg Fare</th>
                  </tr>
                </thead>
                <tbody className="divide-y app-border-subtle app-text-primary">
                  {Object.entries(airlineCounts).map(([code, stat]) => {
                    const share = quotes.length ? (stat.count / quotes.length) * 100 : 0;
                    const avg = stat.count ? stat.sum / stat.count : 0;
                    const airlineName = AIRLINE_NAMES[code] || code;
                    const isExpanded = !!expandedCodes[code];
                    return (
                      <React.Fragment key={code}>
                        <tr
                          onClick={() => toggleCode(code)}
                          className="hover:app-bg-surface/70 transition-colors cursor-pointer select-none"
                        >
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-1.5">
                              {isExpanded ? (
                                <ChevronDown className="w-3.5 h-3.5 text-[var(--color-gold)] flex-shrink-0" />
                              ) : (
                                <ChevronRight className="w-3.5 h-3.5 app-text-muted flex-shrink-0" />
                              )}
                              <AirlineLogo airline={code} size="sm" />
                              <span className="font-bold app-text-primary text-xs truncate max-w-[85px]">
                                {airlineName}
                              </span>
                            </div>
                          </td>
                          <td className="px-2 py-3">
                            <div className="flex items-center gap-1.5">
                              <div className="w-14 bg-slate-200 dark:bg-slate-700/60 rounded-full h-1.5 overflow-hidden border app-border-subtle flex-shrink-0">
                                <div
                                  className="bg-[var(--color-gold)] h-1.5 rounded-full transition-all duration-300"
                                  style={{ width: `${Math.max(share, 2)}%` }}
                                ></div>
                              </div>
                              <span className="text-[11px] font-mono font-semibold app-text-primary tabular-nums">
                                {share.toFixed(1)}%
                              </span>
                            </div>
                          </td>
                          <td className="px-3 py-3 text-right font-mono font-semibold text-xs text-[var(--color-gold)]">
                            ₹{avg.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                          </td>
                        </tr>

                        {/* Expandable Details Sub-row */}
                        {isExpanded && (
                          <tr className="app-bg-surface/60 border-t border-b app-border-subtle">
                            <td colSpan={3} className="px-3.5 py-3 text-xs">
                              <div className="grid grid-cols-2 gap-2.5 font-mono">
                                <div>
                                  <span className="text-[9px] uppercase font-semibold app-text-muted block">
                                    Corridor Volume
                                  </span>
                                  <span className="text-[11px] font-bold app-text-primary">
                                    {stat.count} quotes ({share.toFixed(1)}%)
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[9px] uppercase font-semibold app-text-muted block">
                                    Carrier Code
                                  </span>
                                  <span className="text-[11px] font-bold app-text-primary">
                                    {code} ({airlineName})
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
        </>
      )}
    </div>
  );
}
