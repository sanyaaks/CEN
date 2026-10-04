"use client";

import React, { useEffect, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { getRouteAudit } from "@/lib/api";
import { CleanObservation } from "@/types/api";
import LoadingState from "@/components/ui/LoadingState";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import InteractiveIndexChart from "@/components/charts/InteractiveIndexChart";
import RouteHorizonHeatmap from "@/components/charts/RouteHorizonHeatmap";
import RouteSearchSelect from "@/components/ui/RouteSearchSelect";

const CONFIGURED_ROUTES = [
  "DEL-BOM",
  "BLR-DEL",
  "DEL-CCU",
  "BOM-BLR",
  "DEL-MAA",
  "HYD-MAA",
];

interface HorizonSummary {
  horizon_days: number;
  sample_size: number;
  min_price: number;
  max_price: number;
  avg_price: number;
}

export default function BookingWindowPage() {
  const [selectedRoute, setSelectedRoute] = useState<string>("DEL-BOM");
  const [horizons, setHorizons] = useState<HorizonSummary[]>([]);
  const [expandedHorizons, setExpandedHorizons] = useState<Record<number, boolean>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const toggleHorizon = (day: number) => {
    setExpandedHorizons((prev) => ({ ...prev, [day]: !prev[day] }));
  };

  const fetchCurve = async (route: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await getRouteAudit(route);
      const observations: CleanObservation[] = res.observations || [];

      // Group by horizon_days
      const grouped: Record<number, { sum: number; count: number; min: number; max: number }> = {};
      observations.forEach((obs) => {
        const h = obs.horizon_days;
        if (!grouped[h]) {
          grouped[h] = { sum: 0, count: 0, min: Infinity, max: -Infinity };
        }
        grouped[h].sum += obs.total_price;
        grouped[h].count += 1;
        if (obs.total_price < grouped[h].min) grouped[h].min = obs.total_price;
        if (obs.total_price > grouped[h].max) grouped[h].max = obs.total_price;
      });

      const curve: HorizonSummary[] = Object.entries(grouped)
        .map(([hStr, data]) => ({
          horizon_days: parseInt(hStr, 10),
          sample_size: data.count,
          min_price: data.min,
          max_price: data.max,
          avg_price: data.count > 0 ? data.sum / data.count : 0,
        }))
        .sort((a, b) => a.horizon_days - b.horizon_days);

      setHorizons(curve);
    } catch (err: any) {
      setError(err.message || "Failed to load booking window data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCurve(selectedRoute);
  }, [selectedRoute]);

  // Find min and max fare horizons
  let minHorizon = horizons[0];
  let maxHorizon = horizons[0];
  horizons.forEach((h) => {
    if (h.avg_price < (minHorizon?.avg_price || Infinity)) minHorizon = h;
    if (h.avg_price > (maxHorizon?.avg_price || -Infinity)) maxHorizon = h;
  });

  const chartData = horizons.map((h) => ({
    label: `T+${h.horizon_days}`,
    value: h.avg_price,
    tooltipDetails: `Min: ₹${Math.round(h.min_price)} • Max: ₹${Math.round(h.max_price)} (${h.sample_size} quotes)`
  }));

  return (
    <div className="space-y-8 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 py-8 transition-colors duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b app-border">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold tracking-tight app-text-primary">
              Advance Booking Horizon Yield Curve
            </h1>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-md app-badge-gold">
              T+1 to T+45 Days
            </span>
          </div>
          <p className="text-xs app-text-secondary mt-1">
            Empirical dynamic pricing trajectories across booking lead-time buckets.
          </p>
        </div>

        {/* Route Selector with Search */}
        <div className="w-64">
          <RouteSearchSelect
            value={selectedRoute}
            onChange={setSelectedRoute}
            compact
          />
        </div>
      </div>

      {isLoading ? (
        <LoadingState message={`Constructing empirical advance yield curve for ${selectedRoute}...`} />
      ) : error ? (
        <ErrorState message={error} onRetry={() => fetchCurve(selectedRoute)} />
      ) : horizons.length === 0 ? (
        <EmptyState title="No Horizon Data" description="Insufficient observations collected across lead-times." />
      ) : (
        <>
          {/* Key Horizon Insights */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="app-card-blue-1 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="text-xs font-semibold text-[#1E2A44] uppercase">Cheapest Advance Horizon</div>
              <div className="text-2xl font-bold text-[#15803D] font-mono">
                T+{minHorizon?.horizon_days} Days
              </div>
              <p className="text-[11px] text-[#7D8CA3]">
                Avg price: <strong className="text-[#1E2A44]">₹{minHorizon?.avg_price ? Math.round(minHorizon.avg_price).toLocaleString() : "N/A"}</strong>
              </p>
            </div>

            <div className="app-card-blue-2 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="text-xs font-semibold text-[#1E2A44] uppercase">Peak Dynamic Pricing Horizon</div>
              <div className="text-2xl font-bold text-[#DC2626] font-mono">
                T+{maxHorizon?.horizon_days} Days
              </div>
              <p className="text-[11px] text-[#7D8CA3]">
                Avg price: <strong className="text-[#1E2A44]">₹{maxHorizon?.avg_price ? Math.round(maxHorizon.avg_price).toLocaleString() : "N/A"}</strong>
              </p>
            </div>

            <div className="app-card-blue-3 rounded-xl p-5 shadow-sm space-y-2 transition-transform hover:-translate-y-0.5">
              <div className="text-xs font-semibold text-[#1E2A44] uppercase">Horizon Price Spread</div>
              <div className="text-2xl font-bold text-[#1E2A44] font-mono">
                ₹{minHorizon && maxHorizon ? Math.round(maxHorizon.avg_price - minHorizon.avg_price).toLocaleString() : "0"}
              </div>
              <p className="text-[11px] text-[#7D8CA3]">
                Last-minute premium observed vs advance purchase
              </p>
            </div>
          </div>

          {/* Interactive Yield Curve */}
          <div className="space-y-3">
            <h2 className="text-base font-semibold app-text-primary">
              Empirical Price Relative Curve ({selectedRoute} • ₹ INR)
            </h2>
            <InteractiveIndexChart
              data={chartData}
              title={`Lead-Time Fare Progression (T+1 to T+45)`}
              valuePrefix="₹"
              valueSuffix=""
              height={260}
              accentColor="teal"
            />
          </div>

          {/* Interactive Route x Horizon Heatmap */}
          <RouteHorizonHeatmap />

          {/* Horizon Table Breakdown */}
          <div className="space-y-4">
            <h2 className="text-base font-semibold app-text-primary">
              Lead Time Bucket Data ({selectedRoute})
            </h2>
            {/* Desktop Table View (Full Columns, Clean, No Chevrons) */}
            <div className="hidden md:block app-bg-card border app-border rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="app-bg-surface border-b app-border text-[11px] font-semibold app-text-secondary uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3.5">Horizon</th>
                    <th className="px-5 py-3.5">Sample Volume</th>
                    <th className="px-5 py-3.5 text-right">Min Fare</th>
                    <th className="px-5 py-3.5 text-right">Avg Observed Fare</th>
                    <th className="px-5 py-3.5 text-right">Max Fare</th>
                  </tr>
                </thead>
                <tbody className="divide-y app-border-subtle app-text-primary font-mono">
                  {horizons.map((h) => (
                    <tr key={h.horizon_days} className="hover:app-bg-surface/70 transition-colors">
                      <td className="px-5 py-3.5 font-sans font-bold app-text-primary">
                        T+{h.horizon_days} Days Out
                      </td>
                      <td className="px-5 py-3.5 text-[11px] app-text-secondary">
                        {h.sample_size} quotes
                      </td>
                      <td className="px-5 py-3.5 text-right text-[var(--color-teal)]">
                        ₹{Math.round(h.min_price).toLocaleString()}
                      </td>
                      <td className="px-5 py-3.5 text-right font-bold text-[var(--color-gold)]">
                        ₹{Math.round(h.avg_price).toLocaleString()}
                      </td>
                      <td className="px-5 py-3.5 text-right text-[var(--color-rose)]">
                        ₹{Math.round(h.max_price).toLocaleString()}
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
                    <th className="px-3 py-3">Horizon</th>
                    <th className="px-2 py-3 text-center">Volume</th>
                    <th className="px-3 py-3 text-right">Avg Fare</th>
                  </tr>
                </thead>
                <tbody className="divide-y app-border-subtle app-text-primary font-mono">
                  {horizons.map((h) => {
                    const isExpanded = !!expandedHorizons[h.horizon_days];
                    return (
                      <React.Fragment key={h.horizon_days}>
                        <tr
                          onClick={() => toggleHorizon(h.horizon_days)}
                          className="hover:app-bg-surface/70 transition-colors cursor-pointer select-none"
                        >
                          <td className="px-3 py-3 font-sans font-bold app-text-primary">
                            <div className="flex items-center gap-1.5">
                              {isExpanded ? (
                                <ChevronDown className="w-3.5 h-3.5 text-[var(--color-gold)] flex-shrink-0" />
                              ) : (
                                <ChevronRight className="w-3.5 h-3.5 app-text-muted flex-shrink-0" />
                              )}
                              <span>T+{h.horizon_days}d</span>
                            </div>
                          </td>
                          <td className="px-2 py-3 text-center text-[11px] app-text-secondary">
                            {h.sample_size}
                          </td>
                          <td className="px-3 py-3 text-right font-bold text-[var(--color-gold)]">
                            ₹{Math.round(h.avg_price).toLocaleString()}
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
                                    ₹{Math.round(h.min_price).toLocaleString()}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[9px] uppercase font-semibold app-text-muted block">
                                    Max Fare
                                  </span>
                                  <span className="text-xs font-bold text-[var(--color-rose)]">
                                    ₹{Math.round(h.max_price).toLocaleString()}
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
