import os
import hmac
import hashlib
import base64
import json
import time
import secrets
from typing import Optional, Dict, Any

# Secret key for JWT signing - defaults to a secure development key or env var
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "mospi_cen_airindex_jwt_secret_key_2026_secure_hash")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def generate_salt(length: int = 16) -> str:
    """Generate a cryptographically secure random hex salt."""
    return secrets.token_hex(length)


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Returns (hashed_password_hex, salt_hex).
    """
    if not salt:
        salt = generate_salt()
    
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        pwd_bytes,
        salt_bytes,
        iterations=100000
    )
    return hash_bytes.hex(), salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify a plaintext password against the stored PBKDF2-HMAC-SHA256 hash.
    Uses hmac.compare_digest for constant-time comparison.
    """
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, hashed_password)


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def create_access_token(payload: Dict[str, Any], expires_in_hours: int = JWT_EXPIRATION_HOURS) -> str:
    """
    Generate an RFC 7519 standard JSON Web Token (JWT) with HMAC-SHA256 signature.
    Zero external dependencies, highly resilient and fast.
    """
    header = {
        "alg": JWT_ALGORITHM,
        "typ": "JWT"
    }
    
    issued_at = int(time.time())
    expires_at = issued_at + (expires_in_hours * 3600)
    
    token_payload = {
        **payload,
        "iat": issued_at,
        "exp": expires_at
    }
    
    header_encoded = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_encoded = _base64url_encode(json.dumps(token_payload, separators=(",", ":")).encode("utf-8"))
    
    signing_input = f"{header_encoded}.{payload_encoded}".encode("utf-8")
    signature = hmac.new(JWT_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_encoded = _base64url_encode(signature)
    
    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JSON Web Token.
    Returns payload dict if valid, or None if expired/tampered.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
            
        header_encoded, payload_encoded, signature_encoded = parts
        
        # Verify signature
        signing_input = f"{header_encoded}.{payload_encoded}".encode("utf-8")
        expected_signature = hmac.new(JWT_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_signature = _base64url_decode(signature_encoded)
        
        if not hmac.compare_digest(expected_signature, actual_signature):
            return None
            
        # Parse payload
        payload_json = _base64url_decode(payload_encoded).decode("utf-8")
        payload = json.loads(payload_json)
        
        # Check expiration
        current_time = int(time.time())
        if payload.get("exp") and current_time > payload["exp"]:
            return None
            
        return payload
    except Exception:
        return None
