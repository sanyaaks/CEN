"use client";

import React, { useEffect, useState } from "react";
import {
  Server,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Bot,
  Plane,
  Database,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  Zap,
} from "lucide-react";
import { getSourcesHealth, getScrapeRuns, triggerAIAgentHarvest } from "@/lib/api";
import { SourcesHealthResponse, ScrapeRunsResponse, HarvestResponse } from "@/types/api";
import LoadingState from "@/components/ui/LoadingState";
import ErrorState from "@/components/ui/ErrorState";
import RouteSearchSelect from "@/components/ui/RouteSearchSelect";

export default function CollectionPage() {
  const [sourcesHealth, setSourcesHealth] = useState<SourcesHealthResponse | null>(null);
  const [scrapeRuns, setScrapeRuns] = useState<ScrapeRunsResponse | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [expandedRuns, setExpandedRuns] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // AI Harvester Interactive State
  const [selectedRoute, setSelectedRoute] = useState<string>("DEL-BOM");
  const [selectedPortal, setSelectedPortal] = useState<string>("google_flights");
  const [selectedHorizon, setSelectedHorizon] = useState<number>(2);
  const [isHarvesting, setIsHarvesting] = useState<boolean>(false);
  const [harvestError, setHarvestError] = useState<string | null>(null);
  const [harvestResult, setHarvestResult] = useState<HarvestResponse | null>(null);
  const [harvestTimer, setHarvestTimer] = useState<number>(0);

  const toggleRun = (runId: string) => {
    setExpandedRuns((prev) => ({ ...prev, [runId]: !prev[runId] }));
  };

  const fetchCollectionData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [health, runs] = await Promise.all([
        getSourcesHealth(),
        getScrapeRuns(40),
      ]);
      setSourcesHealth(health);
      setScrapeRuns(runs);
    } catch (err: any) {
      setError(err.message || "Failed to load collection data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCollectionData();
  }, []);

  // Timer for active AI scraping
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isHarvesting) {
      setHarvestTimer(0);
      interval = setInterval(() => {
        setHarvestTimer((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isHarvesting]);

  const handleTriggerAIHarvest = async () => {
    setIsHarvesting(true);
    setHarvestError(null);
    setHarvestResult(null);

    try {
      const response = await triggerAIAgentHarvest({
        route: selectedRoute,
        portal: selectedPortal,
        horizon_days: selectedHorizon,
      });

      setHarvestResult(response);
      fetchCollectionData();
    } catch (err: any) {
      setHarvestError(err.message || "Failed to execute AI scraping agent.");
    } finally {
      setIsHarvesting(false);
    }
  };

  const sources = sourcesHealth?.sources || [];
  const runs = scrapeRuns?.runs || [];
  const filteredRuns = statusFilter === "ALL" ? runs : runs.filter((r) => r.status === statusFilter);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "HEALTHY":
      case "SUCCESS":
        return "bg-emerald-50 text-emerald-800 border-emerald-200";
      case "DEGRADED":
      case "PARTIAL":
      case "RUNNING":
        return "bg-amber-50 text-amber-800 border-amber-200";
      case "UNAVAILABLE":
      case "FAILED":
        return "bg-rose-50 text-rose-800 border-rose-200";
      default:
        return "bg-slate-50 text-slate-700 border-slate-200";
    }
  };

  const getAirlineBadge = (airline: string) => {
    const lower = airline.toLowerCase();
    if (lower.includes("indigo")) return "bg-blue-50 text-blue-800 border-blue-200";
    if (lower.includes("air india")) return "bg-red-50 text-red-800 border-red-200";
    if (lower.includes("akasa")) return "bg-orange-50 text-orange-800 border-orange-200";
    if (lower.includes("spicejet")) return "bg-amber-50 text-amber-800 border-amber-200";
    return "bg-slate-50 text-slate-800 border-slate-200";
  };

  return (
    <div className="space-y-8 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#1E2A44] flex items-center gap-2">
            <Server className="w-6 h-6 text-[#284269]" />
            Airfare Data Collection & Live Scanner
          </h1>
          <p className="text-xs text-[#7D8CA3] mt-1">
            Real-time status of data sources, automated flight scrapers, and execution run history.
          </p>
        </div>

        <button
          onClick={fetchCollectionData}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-xs font-semibold text-[#1E2A44] rounded-lg transition-colors shadow-xs self-start"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          Refresh Health Status
        </button>
      </div>

      {/* 🚀 LIVE AIRLINE FARE EXTRACTOR (CRISP SOLID WHITE) */}
      <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm relative overflow-hidden">
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-[#FFF8E7] border border-[#F3DEAB] rounded-xl shadow-xs">
                <Plane className="w-5 h-5 text-[#B8860B]" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-[#1E2A44]">
                    Live Airline Fare Extractor
                  </h2>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border border-[#F3DEAB] bg-[#FFF8E7] text-[#B8860B]">
                    LIVE SCANNER
                  </span>
                </div>
                <p className="text-xs text-[#7D8CA3] mt-0.5">
                  Search live domestic flight prices directly from airline booking websites and save them to the database.
                </p>
              </div>
            </div>
          </div>

          {/* Interactive Controls */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Route Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#1E2A44] flex items-center gap-1.5">
                <Plane className="w-3.5 h-3.5 text-[#284269]" />
                Route Corridor
              </label>
              <RouteSearchSelect
                value={selectedRoute}
                onChange={setSelectedRoute}
                disabled={isHarvesting}
              />
            </div>

            {/* Target Portal */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#1E2A44] flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5 text-[#284269]" />
                Target Airline / Portal
              </label>
              <select
                value={selectedPortal}
                onChange={(e) => setSelectedPortal(e.target.value)}
                disabled={isHarvesting}
                className="w-full px-3 py-2.5 bg-slate-50 hover:bg-white focus:bg-white border border-slate-200 rounded-lg text-xs font-semibold text-[#1E2A44] focus:outline-none focus:ring-2 focus:ring-[#B8860B]/30 focus:border-[#B8860B] transition-all shadow-xs"
              >
                <option value="google_flights">Google Flights (All Indian Carriers)</option>
                <option value="indigo">IndiGo Official (goindigo.in)</option>
                <option value="airindia">Air India Official (airindia.com)</option>
                <option value="akasaair">Akasa Air Official (akasaair.com)</option>
                <option value="easemytrip">EaseMyTrip Portal (easemytrip.com)</option>
              </select>
            </div>

            {/* Horizon Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#1E2A44] flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-[#284269]" />
                Booking Horizon
              </label>
              <select
                value={selectedHorizon}
                onChange={(e) => setSelectedHorizon(Number(e.target.value))}
                disabled={isHarvesting}
                className="w-full px-3 py-2.5 bg-slate-50 hover:bg-white focus:bg-white border border-slate-200 rounded-lg text-xs font-semibold text-[#1E2A44] focus:outline-none focus:ring-2 focus:ring-[#B8860B]/30 focus:border-[#B8860B] transition-all shadow-xs"
              >
                <option value={1}>T-1 (Departing Tomorrow)</option>
                <option value={2}>T-2 (Departing in 2 Days)</option>
                <option value={7}>T-7 (Departing in 1 Week)</option>
                <option value={14}>T-14 (Departing in 2 Weeks)</option>
                <option value={30}>T-30 (Departing in 1 Month)</option>
              </select>
            </div>

            {/* Trigger Button */}
            <div className="flex items-end">
              <button
                onClick={handleTriggerAIHarvest}
                disabled={isHarvesting}
                className={`w-full py-2.5 px-4 rounded-lg font-semibold text-xs flex items-center justify-center shadow-sm transition-all border border-[#7D8CA3]/40 ${
                  isHarvesting
                    ? "bg-slate-100 text-slate-400 cursor-not-allowed border-slate-200"
                    : "bg-[#2E4A6B] hover:bg-[#1E2A44] text-[#F5F3EC] active:scale-[0.99]"
                }`}
              >
                {isHarvesting ? `Searching (${harvestTimer}s)...` : "Search Live Fares"}
              </button>
            </div>
          </div>

          {/* ⚡ SINGLE-LINE LOADING INDICATOR (CYCLES EVERY 24 SECONDS) */}
          {isHarvesting && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center text-xs text-[#1E2A44] transition-all">
              <span className="font-medium text-slate-700 animate-pulse">
                {harvestTimer < 24
                  ? `Searching live flights for ${selectedRoute}...`
                  : harvestTimer < 48
                  ? `Connecting to ${selectedPortal} and scanning airfares...`
                  : harvestTimer < 72
                  ? `Extracting live seat prices for ${selectedRoute}...`
                  : harvestTimer < 96
                  ? `Verifying tariffs and processing flight quotes...`
                  : `Finalizing flight observations and saving to database...`}
              </span>
            </div>
          )}

          {/* Error Message */}
          {harvestError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2.5 text-xs text-rose-800">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{harvestError}</span>
            </div>
          )}

          {/* 🎉 LIVE EXTRACTED AIRFARE QUOTES DISPLAY (CRISP WHITE CARD) */}
          {harvestResult && (
            <div className="space-y-4 pt-1">
              <div className="p-3 bg-emerald-50/80 border border-emerald-200 rounded-xl flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-emerald-900 font-medium">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                  <span>
                    Successfully recorded {harvestResult.quotes_count} live quotes for {harvestResult.route}
                  </span>
                </div>
                {harvestResult.latest_composite_index && (
                  <span className="text-[11px] font-semibold text-emerald-800 bg-white border border-emerald-200 px-2 py-0.5 rounded-md shadow-2xs">
                    CPI Index: {harvestResult.latest_composite_index.toFixed(2)} pts
                  </span>
                )}
              </div>

              {/* Extracted Quotes Table (CRISP SOLID WHITE) */}
              <div className="bg-white rounded-xl overflow-hidden border border-slate-200 shadow-xs">
                <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Plane className="w-4 h-4 text-[#284269]" />
                    <span className="text-xs font-extrabold text-[#1E2A44] uppercase tracking-wider">
                      Live Quotes Harvested ({harvestResult.route} • {harvestResult.departure_date})
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-[#7D8CA3]">
                    Source: {harvestResult.portal_name}
                  </span>
                </div>

                <div className="overflow-x-auto max-h-80 overflow-y-auto">
                  <table className="w-full text-left text-xs bg-white">
                    <thead className="bg-slate-50 text-[#7D8CA3] font-semibold border-b border-slate-200 sticky top-0">
                      <tr>
                        <th className="py-3 px-5">Carrier / Airline</th>
                        <th className="py-3 px-5">Flight No</th>
                        <th className="py-3 px-5">Corridor</th>
                        <th className="py-3 px-5">Schedule (Dep → Arr)</th>
                        <th className="py-3 px-5 text-right">Economy Fare (INR)</th>
                        <th className="py-3 px-5 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {harvestResult.flights.map((flight, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/80 transition-colors bg-white">
                          <td className="py-3 px-5 font-bold text-[#1E2A44] flex items-center gap-2">
                            <span className={`text-[10px] px-2 py-0.5 rounded font-bold border ${getAirlineBadge(flight.airline)}`}>
                              {flight.airline}
                            </span>
                          </td>
                          <td className="py-3 px-5 font-mono font-medium text-[#1E2A44]">
                            {flight.flight_number || "N/A"}
                          </td>
                          <td className="py-3 px-5 text-[#7D8CA3] font-mono">
                            {flight.origin} → {flight.destination}
                          </td>
                          <td className="py-3 px-5 text-[#7D8CA3] font-mono">
                            {flight.departure_time || "--"} → {flight.arrival_time || "--"}
                          </td>
                          <td className="py-3 px-5 text-right font-extrabold text-[#B8860B] font-mono text-sm">
                            ₹{flight.price_inr.toLocaleString()}
                          </td>
                          <td className="py-3 px-5 text-center">
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                              {flight.is_non_stop ? "Direct" : "1-Stop"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {isLoading ? (
        <LoadingState message="Querying data sources and execution run history..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchCollectionData} />
      ) : (
        <>
          {/* Source Status Cards */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-[#7D8CA3] uppercase tracking-wider">
              Data Source Health & Reliability
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {sources.map((source) => (
                <div
                  key={source.source_name}
                  className="bg-white rounded-xl p-5 shadow-xs border border-slate-200 space-y-3 transition-transform hover:-translate-y-0.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-[#1E2A44]">
                      {source.source_name.replace("_", " ").toUpperCase()}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getStatusBadge(source.health.status)}`}>
                      {source.health.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                    <div>
                      <span className="text-[10px] text-[#7D8CA3] block">Response Time</span>
                      <span className="font-bold text-[#1E2A44]">
                        {source.health.last_response_time_ms ? `${source.health.last_response_time_ms} ms` : "Live (<1s)"}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#7D8CA3] block">Recent Failures</span>
                      <span className="font-bold text-[#1E2A44]">{source.health.consecutive_failures}</span>
                    </div>
                  </div>

                  <div className="text-[11px] text-[#7D8CA3] border-t border-slate-100 pt-2 flex items-center justify-between">
                    <span>Method: {source.source_type === "direct_api" ? "Direct Feed" : "Automated Browser"}</span>
                    <span>Total Checks: {source.health.total_queries}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Collection Execution Runs Table */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-[#1E2A44]">
                  Collection Activity Log
                </h2>
                <p className="text-xs text-[#7D8CA3]">
                  Complete history of automated scheduled scans and on-demand flight price collections.
                </p>
              </div>

              {/* Status Filter Buttons */}
              <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg border border-slate-200 self-start">
                {["ALL", "SUCCESS", "PARTIAL", "FAILED"].map((status) => (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status)}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                      statusFilter === status
                        ? "bg-[#284269] text-white shadow-xs"
                        : "text-[#7D8CA3] hover:text-[#1E2A44]"
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>

            {/* Runs Table */}
            <div className="bg-white rounded-xl overflow-hidden border border-slate-200 shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs bg-white">
                  <thead className="bg-slate-50 text-[#7D8CA3] font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4 w-10"></th>
                      <th className="py-3 px-4">Batch ID</th>
                      <th className="py-3 px-4">Data Source</th>
                      <th className="py-3 px-4">Flight Route & Advance Days</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Fares Recorded</th>
                      <th className="py-3 px-4 text-right">Duration</th>
                      <th className="py-3 px-4">Collection Time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredRuns.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="py-8 text-center text-[#7D8CA3]">
                          No collection runs match the selected status filter.
                        </td>
                      </tr>
                    ) : (
                      filteredRuns.map((run) => {
                        const isExpanded = !!expandedRuns[run.run_id];
                        const durationSec = run.completed_at
                          ? (
                              (new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) /
                              1000
                            ).toFixed(1)
                          : "--";

                        return (
                          <React.Fragment key={run.run_id}>
                            <tr
                              onClick={() => toggleRun(run.run_id)}
                              className="hover:bg-slate-50 cursor-pointer transition-colors bg-white"
                            >
                              <td className="py-3 px-4 text-center">
                                {isExpanded ? (
                                  <ChevronDown className="w-3.5 h-3.5 text-[#7D8CA3]" />
                                ) : (
                                  <ChevronRight className="w-3.5 h-3.5 text-[#7D8CA3]" />
                                )}
                              </td>
                              <td className="py-3 px-4 font-mono font-bold text-[#1E2A44]">
                                {run.run_id}
                              </td>
                              <td className="py-3 px-4 text-[#1E2A44] font-medium">
                                {run.source ? run.source.replace("_", " ").toUpperCase() : "Multi-Source Engine"}
                              </td>
                              <td className="py-3 px-4 font-mono text-[#7D8CA3]">
                                {run.route ? `${run.route} (T-${run.horizon ?? 0})` : "All Routes"}
                              </td>
                              <td className="py-3 px-4">
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getStatusBadge(run.status)}`}>
                                  {run.status}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-right font-mono font-bold text-[#1E2A44]">
                                {run.records_collected}
                              </td>
                              <td className="py-3 px-4 text-right font-mono text-[#7D8CA3]">
                                {durationSec}s
                              </td>
                              <td className="py-3 px-4 font-mono text-[#7D8CA3]">
                                {new Date(run.started_at).toLocaleString("en-IN", {
                                  day: "2-digit",
                                  month: "short",
                                  hour: "2-digit",
                                  minute: "2-digit",
                                  second: "2-digit",
                                })}
                              </td>
                            </tr>

                            {/* Expanded Run Detail Drawer */}
                            {isExpanded && (
                              <tr className="bg-slate-50">
                                <td colSpan={8} className="py-4 px-6 border-y border-slate-200">
                                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs font-mono">
                                    <div>
                                      <span className="text-[10px] text-[#7D8CA3] uppercase block">
                                        Searches Attempted
                                      </span>
                                      <span className="font-bold text-[#1E2A44]">{run.attempted}</span>
                                    </div>
                                    <div>
                                      <span className="text-[10px] text-[#7D8CA3] uppercase block">
                                        Valid Fares Stored
                                      </span>
                                      <span className="font-bold text-emerald-700">{run.successful}</span>
                                    </div>
                                    <div>
                                      <span className="text-[10px] text-[#7D8CA3] uppercase block">
                                        Filtered Outliers
                                      </span>
                                      <span className="font-bold text-rose-700">{run.records_rejected}</span>
                                    </div>
                                    <div>
                                      <span className="text-[10px] text-[#7D8CA3] uppercase block">
                                        Failed Queries
                                      </span>
                                      <span className="font-bold text-rose-700">{run.error_count}</span>
                                    </div>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
