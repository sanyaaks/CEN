import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.scraping.registry import registry
from app.scraping.health import health_tracker


def print_source_coverage_report():
    print("=" * 85)
    print("           SOURCE COVERAGE & HEALTH DIAGNOSTIC REPORT (AIRINDEX INDIA)")
    print("=" * 85)
    print(f"{'SOURCE':<26} | {'TYPE':<12} | {'PRIORITY':<8} | {'STATUS':<12} | {'OBSERVATION PROVENANCE'}")
    print("-" * 85)

    all_sources = registry.list_all_sources()
    live_health = health_tracker.get_all_health()

    for s in all_sources:
        name = s["source_name"]
        stype = s["source_type"]
        prio = str(s["priority"])
        h = live_health.get(name, {})
        status = h.get("status", "AVAILABLE" if s["enabled"] else "DISABLED")
        obs_type = "ESTIMATED (Model Fallback)" if s["is_fallback_model"] else "OBSERVED (Live Data)"

        print(f"{name:<26} | {stype:<12} | {prio:<8} | {status:<12} | {obs_type}")

    print("=" * 85)


if __name__ == "__main__":
    print_source_coverage_report()
