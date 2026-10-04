import sys
sys.path.insert(0, ".")
from app.db import SessionLocal
from app.models.db_models import IndexValue

db = SessionLocal()
recs = db.query(IndexValue).order_by(IndexValue.id.desc()).limit(13).all()
recs = list(reversed(recs))

print("=" * 88)
print(f"{'Route':<22} | {'Method':<20} | {'Index Value':<12} | {'Sample Size':<12} | {'Mean / Geo-Mean'}")
print("=" * 88)
for r in recs:
    name = r.route or "ALL_INDIA_COMPOSITE"
    val = r.index_value
    meta = r.metadata_json or {}
    mean_val = meta.get("current_mean_price") or meta.get("geometric_mean") or "N/A"
    if isinstance(mean_val, (int, float)):
        mean_str = f"INR {mean_val:,.2f}"
    else:
        mean_str = str(mean_val)
    print(f"{name:<22} | {r.method:<20} | {val:<12.4f} | {r.sample_size:<12} | {mean_str}")
print("=" * 88)

db.close()
