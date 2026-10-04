"""
Outlier Detection Stress Test
=============================
1. Injects a fake CleanFare with an absurd price (INR 50,000) into DEL-BOM.
2. Computes the index WITHOUT outlier detection.
3. Runs outlier detection.
4. Re-computes the index WITH outlier filtering.
5. Reports whether the fake row was caught and the index distortion.
"""

import sys
import datetime
import numpy as np

sys.path.insert(0, ".")
from app.db import SessionLocal
from app.models.db_models import CleanFare, IndexValue
from app.processing.outliers import OutlierDetector
from app.processing.index_engine import IndexEngine

ROUTE = "DEL-BOM"
ABSURD_PRICE = 50_000.0

db = SessionLocal()

# Cleanup any previous fake runs
db.query(CleanFare).filter(CleanFare.flight_number == "FK-9999").delete()
db.commit()

# ── 1. Baseline: current DEL-BOM prices (non-outlier) ──────────────────
real_fares = (
    db.query(CleanFare)
    .filter(CleanFare.route == ROUTE, CleanFare.is_outlier == False)
    .all()
)
real_prices = [f.total_price for f in real_fares]

if not real_prices:
    print(f"ERROR: No existing CleanFare data for {ROUTE}. Run a scrape first.")
    db.close()
    sys.exit(1)

mean_real = float(np.mean(real_prices))
std_real = float(np.std(real_prices))

print("=" * 64)
print("  OUTLIER DETECTION STRESS TEST")
print("=" * 64)
print(f"\n  Route            : {ROUTE}")
print(f"  Existing fares   : {len(real_prices)}")
print(f"  Price range      : INR {min(real_prices):,.0f} - {max(real_prices):,.0f}")
print(f"  Mean             : INR {mean_real:,.2f}")
print(f"  Std Dev          : INR {std_real:,.2f}")
print(f"  Injected price   : INR {ABSURD_PRICE:,.0f}")
z_of_fake = abs(ABSURD_PRICE - mean_real) / std_real if std_real > 0 else float("inf")
print(f"  Expected Z-score : {z_of_fake:.2f}")

# ── 2. Compute index BEFORE injection (baseline) ───────────────────────
engine = IndexEngine()
_, dutot_p0_map, _, _ = engine.get_baseline_p0_map(db)
base_p = dutot_p0_map.get(ROUTE, mean_real)
dutot_baseline = engine.calculate_dutot(real_prices, base_p)
print(f"\n  Dutot Index (baseline, no fake)    : {dutot_baseline:.4f}")

# ── 3. Inject the fake row ──────────────────────────────────────────────
fake = CleanFare(
    source_raw_fare_id=None,  # No real source
    route=ROUTE,
    date=datetime.datetime(2026, 9, 15),
    horizon=7,
    airline="FakeAir",
    flight_number="FK-9999",
    base_fare=ABSURD_PRICE * 0.85,
    tax=ABSURD_PRICE * 0.15,
    total_price=ABSURD_PRICE,
    ancillary_fees=0.0,
    tax_estimated=True,
    is_outlier=False,       # Not yet flagged
    outlier_reason=None,
    outlier_score=None,
    cleaned_at=datetime.datetime.now(datetime.timezone.utc)
)
db.add(fake)
db.commit()
db.refresh(fake)
fake_id = fake.id
print(f"\n  [+] Injected fake CleanFare ID: {fake_id}  (INR {ABSURD_PRICE:,.0f})")

# ── 4. Index WITH the fake row (before outlier detection) ───────────────
all_prices_with_fake = real_prices + [ABSURD_PRICE]
dutot_with_fake = engine.calculate_dutot(all_prices_with_fake, base_p)
print(f"  Dutot Index (with fake, no filter) : {dutot_with_fake:.4f}")
distortion = abs(dutot_with_fake - dutot_baseline)
print(f"  Distortion from fake               : {distortion:.4f} index points")

# ── 5. Run outlier detection ────────────────────────────────────────────
detector = OutlierDetector(z_threshold=3.0)
flagged = detector.flag_outliers_for_route(db, route=ROUTE)

# Check if our fake was caught
fake_after = db.query(CleanFare).filter(CleanFare.id == fake_id).first()
was_caught = fake_after.is_outlier

print(f"\n  -- Outlier Detection Results --")
print(f"  Total flagged in route            : {len(flagged)}")
print(f"  Fake row flagged as outlier?      : {'YES [PASS]' if was_caught else 'NO [FAIL]'}")
if was_caught:
    print(f"  Outlier reason assigned           : {fake_after.outlier_reason}")
    print(f"  Outlier Z-score recorded          : {fake_after.outlier_score}")

# ── 6. Index AFTER outlier filtering (fake excluded) ────────────────────
clean_prices_after = [
    f.total_price for f in
    db.query(CleanFare)
    .filter(CleanFare.route == ROUTE, CleanFare.is_outlier == False)
    .all()
]
dutot_after_filter = engine.calculate_dutot(clean_prices_after, base_p)
print(f"\n  Dutot Index (after outlier filter) : {dutot_after_filter:.4f}")
print(f"  Baseline (no fake)                 : {dutot_baseline:.4f}")
residual = abs(dutot_after_filter - dutot_baseline)
print(f"  Residual distortion after filter   : {residual:.4f} index points")

# ── 7. Clean up: remove the fake row ───────────────────────────────────
db.delete(fake_after)
db.commit()
print(f"\n  [OK] Cleaned up: deleted fake CleanFare ID {fake_id}")

print("\n" + "=" * 64)
if was_caught and residual == 0.0:
    print("  RESULT: OUTLIER DETECTION FULLY OPERATIONAL")
    print(f"          Fake price INR 50,000 was isolated (Z-score: {fake_after.outlier_score})")
    print(f"          Distortion eliminated: {distortion:.4f} -> {residual:.4f} index points")
else:
    print("  RESULT: OUTLIER DETECTION FAILED TO PROTECT INDEX ACCURACY")
print("=" * 64)

db.close()
