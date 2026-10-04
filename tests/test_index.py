import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models.db_models import IndexValue, CleanFare, RawFare

client = TestClient(app)


def setup_module():
    db = SessionLocal()
    try:
        if not db.query(IndexValue).filter(IndexValue.route == "DEL-BOM").first():
            db.add(IndexValue(
                route="DEL-BOM",
                date=datetime.datetime.utcnow(),
                index_value=100.0,
                method="Dutot",
                sample_size=10,
                base_period="2026-08-28",
                base_period_is_real_data=True
            ))
        if not db.query(CleanFare).filter(CleanFare.route == "DEL-BOM").first():
            raw_rec = RawFare(
                timestamp=datetime.datetime.utcnow(),
                source="google_flights",
                origin="DEL",
                destination="BOM",
                travel_date=datetime.datetime.utcnow() + datetime.timedelta(days=7),
                booking_horizon_days=7,
                raw_payload={"mock": True}
            )
            db.add(raw_rec)
            db.commit()
            db.refresh(raw_rec)

            clean_rec = CleanFare(
                raw_fare_id=raw_rec.id,
                route="DEL-BOM",
                airline="6E",
                flight_number="6E-101",
                booking_horizon_days=7,
                date=datetime.datetime.utcnow(),
                total_price=5000.0,
                base_fare=4500.0,
                tax=500.0,
                is_outlier=False
            )
            db.add(clean_rec)
        db.commit()
    finally:
        db.close()


def test_index_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_get_latest_indices_dutot():
    res = client.get("/index/?method=Dutot&frequency=DAILY&observation_type=OBSERVED")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    assert len(data["data"]) > 0
    first_item = data["data"][0]
    assert "route" in first_item
    assert "index_value" in first_item
    assert first_item["method"] == "Dutot"


def test_get_latest_indices_jevons():
    res = client.get("/index/?method=Jevons&frequency=DAILY&observation_type=OBSERVED")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    assert len(data["data"]) > 0
    first_item = data["data"][0]
    assert first_item["method"] == "Jevons"


def test_get_route_index_history():
    res = client.get("/index/DEL-BOM?method=Dutot&frequency=DAILY")
    assert res.status_code == 200
    data = res.json()
    assert data["route"] == "DEL-BOM"
    assert "history" in data
    assert len(data["history"]) > 0


def test_invalid_method():
    res = client.get("/index/?method=InvalidMethod")
    assert res.status_code == 400


def test_route_not_found():
    res = client.get("/index/INVALID-ROUTE")
    assert res.status_code == 404
