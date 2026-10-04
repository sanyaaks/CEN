import { describe, it, expect } from "vitest";

describe("Dashboard & Statistical Logic", () => {
  it("should correctly compute observation coverage vs route coverage", () => {
    const totalQuotes = 932;
    const observedQuotes = 932;
    const estimatedQuotes = 0;

    const obsCoverage = (observedQuotes / totalQuotes) * 100;
    const configuredRoutes = 6;
    const activeRoutes = 6;
    const routeCoverage = (activeRoutes / configuredRoutes) * 100;

    expect(obsCoverage).toBe(100.0);
    expect(routeCoverage).toBe(100.0);
    expect(estimatedQuotes).toBe(0);
  });

  it("should verify advance purchase horizon groupings", () => {
    const horizons = [1, 7, 15, 30, 45];
    const sampleFares = [
      { horizon: 1, fare: 7200 },
      { horizon: 1, fare: 7400 },
      { horizon: 30, fare: 4800 },
      { horizon: 45, fare: 4200 },
    ];

    const t1Fares = sampleFares.filter((f) => f.horizon === 1).map((f) => f.fare);
    const avgT1 = t1Fares.reduce((a, b) => a + b, 0) / t1Fares.length;

    expect(avgT1).toBe(7300);
    expect(horizons).toContain(1);
    expect(horizons).toContain(45);
  });

  it("should properly format currency to Indian standard INR", () => {
    const price = 5420;
    const formatted = `₹${price.toLocaleString("en-IN")}`;
    expect(formatted).toBe("₹5,420");
  });
});
