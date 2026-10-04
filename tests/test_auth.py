import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.security import hash_password, verify_password, create_access_token, decode_access_token


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_password_hashing_and_verification():
    raw_pwd = "SecureOfficial@MoSPI2026"
    hashed_pwd, salt = hash_password(raw_pwd)
    
    assert hashed_pwd != raw_pwd
    assert len(salt) > 0
    assert verify_password(raw_pwd, hashed_pwd, salt) is True
    assert verify_password("WrongPassword123", hashed_pwd, salt) is False


def test_jwt_token_generation_and_decode():
    payload = {"sub": 42, "email": "officer@mospi.gov.in", "role": "OFFICER"}
    token = create_access_token(payload, expires_in_hours=1)
    
    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == 42
    assert decoded["email"] == "officer@mospi.gov.in"
    assert decoded["role"] == "OFFICER"


def test_auth_login_with_seeded_account(client):
    # Test valid login with default MoSPI demo official
    response = client.post("/auth/login", json={
        "email": "director.cpi@mospi.gov.in",
        "password": "Password@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "director.cpi@mospi.gov.in"
    assert data["user"]["role"] == "ADMIN"

    token = data["access_token"]

    # Test /auth/me with Bearer token
    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "director.cpi@mospi.gov.in"
    assert me_data["full_name"] == "Dr. Alok Verma"


def test_auth_login_invalid_password(client):
    response = client.post("/auth/login", json={
        "email": "director.cpi@mospi.gov.in",
        "password": "WrongPasswordXYZ"
    })
    assert response.status_code == 401


def test_auth_demo_personas_endpoint(client):
    response = client.get("/auth/demo-personas")
    assert response.status_code == 200
    personas = response.json()
    assert len(personas) >= 4
    emails = [p["email"] for p in personas]
    assert "director.cpi@mospi.gov.in" in emails
    assert "officer.nso@mospi.gov.in" in emails
