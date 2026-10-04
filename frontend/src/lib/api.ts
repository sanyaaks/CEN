import {
  LatestIndexResponse,
  RouteIndexHistoryResponse,
  AuditSummaryResponse,
  SourcesHealthResponse,
  ScrapeRunsResponse,
  RouteAuditResponse,
  BacktestResponse,
  ValidationCoverageResponse,
  RouteValidationResponse,
  HarvestResponse,
  HarvestPortal
} from "../types/api";
import { User, LoginCredentials, AuthResponse, DemoPersona } from "../types/auth";

export function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

  // 1. If explicit cloud backend URL is provided (e.g. Render URL on Vercel), always use it
  if (envUrl && envUrl !== "/" && !envUrl.includes("localhost") && !envUrl.includes("127.0.0.1")) {
    return envUrl.replace(/\/+$/, "");
  }

  // 2. In browser:
  if (typeof window !== "undefined") {
    const { hostname } = window.location;
    const isLocal = hostname === "localhost" || hostname === "127.0.0.1";
    if (isLocal) {
      // In local dev, use relative paths so Next.js proxy rewrites route cleanly without CORS issues
      return "";
    }
    // Deployed cloud frontend: if environment variable was provided, use it
    if (envUrl && envUrl !== "/") {
      return envUrl.replace(/\/+$/, "");
    }
    // Fallback to relative path for same-domain deployments (e.g. Docker / monolithic host)
    return "";
  }

  return envUrl || process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";
}

// Client-side In-Memory Cache for sub-millisecond tab switching
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const clientApiCache = new Map<string, CacheEntry<any>>();
const CACHE_TTL_MS = 60000; // 60 seconds cache

export function invalidateApiCache(): void {
  clientApiCache.clear();
}

export function getStoredAuthToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("mospi_auth_token");
  }
  return null;
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const isGet = !options?.method || options.method.toUpperCase() === "GET";
  const cacheKey = `${endpoint}`;

  // Instant SWR pattern: If cached data exists, return immediately and revalidate in background if > 15s old
  if (isGet && clientApiCache.has(cacheKey)) {
    const entry = clientApiCache.get(cacheKey)!;
    const age = Date.now() - entry.timestamp;
    if (age < CACHE_TTL_MS) {
      // If slightly stale (age > 15s), trigger silent background revalidation without blocking UI
      if (age > 15000) {
        setTimeout(() => {
          performFetch<T>(endpoint, options, cacheKey).catch(() => {});
        }, 10);
      }
      return entry.data as T;
    }
  }

  return performFetch<T>(endpoint, options, cacheKey);
}

async function performFetch<T>(endpoint: string, options?: RequestInit, cacheKey?: string): Promise<T> {
  const url = `${getApiBaseUrl()}${endpoint}`;
  const token = getStoredAuthToken();

  const headers: Record<string, string> = {
    "Accept": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorDetail = res.statusText;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) errorDetail = errorJson.detail;
        else if (errorJson.message) errorDetail = errorJson.message;
        else if (errorJson.error) errorDetail = errorJson.error;
      } catch {
        // fallback to statusText
      }
      if (!errorDetail && res.status === 404) {
        errorDetail = "Backend endpoint not found. Please verify NEXT_PUBLIC_API_BASE_URL.";
      } else if (!errorDetail && (res.status === 502 || res.status === 504)) {
        errorDetail = "Backend server is warming up from cold start. Please wait a moment and try again.";
      }
      throw new Error(`API Error [${res.status}]: ${errorDetail || "Unknown server error"}`);
    }

    const data = await res.json();
    if (cacheKey) {
      clientApiCache.set(cacheKey, { data, timestamp: Date.now() });
    }
    return data;
  } catch (err: any) {
    if (cacheKey && clientApiCache.has(cacheKey)) {
      return clientApiCache.get(cacheKey)!.data as T;
    }
    console.error(`Failed to fetch ${url}:`, err);
    if (err.name === "TypeError" && err.message?.toLowerCase().includes("fetch")) {
      throw new Error(`Cannot reach backend at '${url || window.location.origin}'. Check if your Render service is live and NEXT_PUBLIC_API_BASE_URL is set in Vercel.`);
    }
    throw err;
  }
}

// -------------------------------------------------------------
// 1. Index APIs
// -------------------------------------------------------------
export async function getLatestIndices(
  method: string = "Dutot",
  frequency: string = "DAILY",
  observation_type: string = "OBSERVED"
): Promise<LatestIndexResponse> {
  return fetchAPI<LatestIndexResponse>(
    `/index/?method=${encodeURIComponent(method)}&frequency=${encodeURIComponent(frequency)}&observation_type=${encodeURIComponent(observation_type)}`
  );
}

export async function getRouteIndexHistory(
  route: string,
  method: string = "Dutot"
): Promise<RouteIndexHistoryResponse> {
  return fetchAPI<RouteIndexHistoryResponse>(
    `/index/${encodeURIComponent(route)}?method=${encodeURIComponent(method)}`
  );
}

// -------------------------------------------------------------
// 2. Audit & Data Lineage APIs
// -------------------------------------------------------------
export async function getAuditSummary(): Promise<AuditSummaryResponse> {
  return fetchAPI<AuditSummaryResponse>("/audit/");
}

export async function getRouteAudit(route: string): Promise<RouteAuditResponse> {
  return fetchAPI<RouteAuditResponse>(`/audit/${encodeURIComponent(route)}`);
}

export async function getSourcesHealth(): Promise<SourcesHealthResponse> {
  return fetchAPI<SourcesHealthResponse>("/audit/sources/health");
}

export async function getScrapeRuns(limit: number = 30): Promise<ScrapeRunsResponse> {
  return fetchAPI<ScrapeRunsResponse>(`/audit/runs?limit=${limit}`);
}

// -------------------------------------------------------------
// 3. Validation & Historical Backtesting APIs
// -------------------------------------------------------------
export async function getBacktest(
  startDate: string = "2026-08-30",
  endDate: string = "2026-10-13",
  method: string = "Dutot",
  referenceSource: string = "SAMPLE_BENCHMARK"
): Promise<BacktestResponse> {
  return fetchAPI<BacktestResponse>(
    `/validation/backtest?start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}&method=${encodeURIComponent(method)}&reference_source=${encodeURIComponent(referenceSource)}`
  );
}

export async function getValidationCoverage(
  startDate: string = "2026-08-30",
  endDate: string = "2026-10-13"
): Promise<ValidationCoverageResponse> {
  return fetchAPI<ValidationCoverageResponse>(
    `/validation/coverage?start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`
  );
}

export async function getRouteValidation(
  startDate: string = "2026-08-30",
  endDate: string = "2026-10-13",
  referenceSource: string = "SAMPLE_BENCHMARK"
): Promise<RouteValidationResponse> {
  return fetchAPI<RouteValidationResponse>(
    `/validation/routes?start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}&reference_source=${encodeURIComponent(referenceSource)}`
  );
}

// -------------------------------------------------------------
// 4. Export URL Generator
// -------------------------------------------------------------
export function getExportUrl(format: "csv" | "json" = "csv"): string {
  return `${getApiBaseUrl()}/export?format=${format}`;
}

// -------------------------------------------------------------
// 5. Official Authentication APIs
// -------------------------------------------------------------
export async function loginOfficial(credentials: LoginCredentials): Promise<AuthResponse> {
  return fetchAPI<AuthResponse>("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(credentials),
  });
}

export async function getCurrentUserProfile(): Promise<User> {
  return fetchAPI<User>("/auth/me");
}

export async function logoutOfficial(): Promise<{ status: string; message: string }> {
  return fetchAPI<{ status: string; message: string }>("/auth/logout", {
    method: "POST",
  });
}

export async function getDemoPersonas(): Promise<DemoPersona[]> {
  return fetchAPI<DemoPersona[]>("/auth/demo-personas");
}

// -------------------------------------------------------------
// 6. Autonomous AI Browser Harvester APIs
// -------------------------------------------------------------
export async function getHarvestPortals(): Promise<HarvestPortal[]> {
  return fetchAPI<HarvestPortal[]>("/harvest/portals");
}

export async function triggerAIAgentHarvest(params: {
  route: string;
  departure_date?: string;
  portal?: string;
  horizon_days?: number;
}): Promise<HarvestResponse> {
  invalidateApiCache();
  return fetchAPI<HarvestResponse>("/harvest/ai-agent", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(params),
  });
}

