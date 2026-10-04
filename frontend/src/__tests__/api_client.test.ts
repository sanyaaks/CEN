import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  getLatestIndices,
  getRouteIndexHistory,
  getAuditSummary,
  getSourcesHealth,
  getBacktest,
  getValidationCoverage
} from "../lib/api";

describe("AirIndex India Centralized API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("should fetch latest indices with proper parameters", async () => {
    const mockResponse = {
      count: 2,
      data: [
        {
          id: 1,
          route: null,
          date: "2026-08-30",
          index_value: 71.76,
          method: "Dutot",
          frequency: "DAILY",
          observation_type: "OBSERVED",
          sample_size: 932,
          observed_count: 932,
          estimated_count: 0,
          coverage_percent: 100.0,
          base_period: "2026-08-30",
          base_period_is_real_data: true,
          methodology_version: "v1.0-prototype",
          created_at: "2026-08-29T00:00:00Z"
        }
      ]
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    });

    const res = await getLatestIndices("Dutot", "DAILY", "OBSERVED");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/index/?method=Dutot&frequency=DAILY&observation_type=OBSERVED"),
      expect.any(Object)
    );
    expect(res.data[0].index_value).toBe(71.76);
    expect(res.data[0].coverage_percent).toBe(100.0);
  });

  it("should handle API error cleanly without crashing", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error"
    });

    await expect(getLatestIndices()).rejects.toThrow("API Error [500]");
  });
});
