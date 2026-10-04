import sys
import os
import time
import requests
import statistics
from typing import List, Dict

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

ENDPOINTS = [
    ("/", "Root System Status"),
    ("/health", "Health Liveness Check"),
    ("/health/ready", "Database Readiness Check"),
    ("/index/", "National Composite Index"),
    ("/index/DEL-BOM", "Corridor Historical Time Series"),
    ("/audit/", "Quality & Lineage Overview"),
    ("/audit/sources/health", "Multi-Source Health Monitor"),
    ("/audit/runs", "Scrape Runs History"),
    ("/audit/DEL-BOM", "Corridor Audit Trail"),
    ("/validation/backtest", "Historical Backtest Reconstruction"),
    ("/validation/metrics", "Statistical Comparison Metrics"),
    ("/validation/coverage", "Route & Observation Coverage"),
    ("/validation/routes", "Route Level Benchmark Comparison"),
    ("/export?format=json", "NSO CPI JSON Export"),
    ("/export?format=csv", "NSO CPI CSV Export"),
]


def run_smoke_test(iterations: int = 3):
    print("=" * 80)
    print("   AIRINDEX INDIA — PERFORMANCE & LATENCY SMOKE TEST (PHASE 5)")
    print("=" * 80)
    print(f"Executing {iterations} warm-up / measurement cycles per endpoint...\n")

    results: List[Dict] = []

    for path, label in ENDPOINTS:
        latencies = []
        statuses = []

        for _ in range(iterations):
            start = time.perf_counter()
            resp = client.get(path)
            duration_ms = (time.perf_counter() - start) * 1000.0
            latencies.append(duration_ms)
            statuses.append(resp.status_code)

        avg_lat = statistics.mean(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        status_ok = all(s in (200, 307) for s in statuses)

        results.append({
            "path": path,
            "label": label,
            "status": "PASS" if status_ok else "FAIL",
            "avg_ms": avg_lat,
            "min_ms": min_lat,
            "max_ms": max_lat
        })

        status_str = "✅ PASS" if status_ok else "❌ FAIL"
        print(f"• {label:<35} [{path:<24}]: {status_str} | Avg: {avg_lat:6.2f} ms (Min: {min_lat:5.2f} ms, Max: {max_lat:5.2f} ms)")

    print("-" * 80)
    avg_total = statistics.mean(r["avg_ms"] for r in results)
    print(f"Overall Average API Latency across all {len(results)} endpoints: {avg_total:.2f} ms")
    print("=" * 80)

    all_passed = all(r["status"] == "PASS" for r in results)
    return all_passed


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
