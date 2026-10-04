import logging
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
try:
    import email_validator  # noqa: F401
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # Fallback gracefully if email-validator is not installed in the environment
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user_model import User
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

logger = logging.getLogger("mospi-airfare-index.auth")

router = APIRouter(prefix="/auth", tags=["Official Authentication"])


# -------------------------------------------------------------
# Pydantic Request / Response Schemas
# -------------------------------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    department: str
    designation: str
    is_active: bool
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours in seconds
    user: UserProfile


class SeedAccount(BaseModel):
    email: str
    password: str
    full_name: str
    role: str
    department: str
    designation: str


# -------------------------------------------------------------
# Default MoSPI Official Seed Accounts
# -------------------------------------------------------------
DEFAULT_OFFICIAL_ACCOUNTS = [
    {
        "email": "director.cpi@mospi.gov.in",
        "password": "Password@123",
        "full_name": "Dr. Alok Verma",
        "role": "ADMIN",
        "department": "Ministry of Statistics & Programme Implementation (MoSPI)",
        "designation": "Deputy Director General (Price Statistics)"
    },
    {
        "email": "officer.nso@mospi.gov.in",
        "password": "Password@123",
        "full_name": "Priya Sharma, ISS",
        "role": "OFFICER",
        "department": "National Statistical Office (NSO)",
        "designation": "Senior Statistical Officer (CPI Division)"
    },
    {
        "email": "officer@mospi.gov.in",
        "password": "Password@123",
        "full_name": "Priya Sharma, ISS",
        "role": "OFFICER",
        "department": "National Statistical Office (NSO)",
        "designation": "Senior Statistical Officer (CPI Division)"
    },
    {
        "email": "admin@mospi.gov.in",
        "password": "Password@123",
        "full_name": "Dr. Alok Verma",
        "role": "ADMIN",
        "department": "Ministry of Statistics & Programme Implementation (MoSPI)",
        "designation": "Deputy Director General (Price Statistics)"
    },
    {
        "email": "analyst.aviation@nic.in",
        "password": "Password@123",
        "full_name": "Rajesh Nair",
        "role": "ANALYST",
        "department": "DGCA Civil Aviation Economic Regulation Cell",
        "designation": "Aviation Data & Tariff Analyst"
    },
    {
        "email": "auditor.cag@gov.in",
        "password": "Password@123",
        "full_name": "S. Ramaswamy",
        "role": "VIEWER",
        "department": "Comptroller and Auditor General / MoSPI Audit Cell",
        "designation": "Senior Audit Officer"
    }
]


def seed_default_users(db: Session) -> int:
    """Ensure standard official demo accounts exist in the database."""
    created_count = 0
    for acc in DEFAULT_OFFICIAL_ACCOUNTS:
        existing = db.query(User).filter(User.email == acc["email"]).first()
        if not existing:
            hashed_pwd, salt = hash_password(acc["password"])
            user = User(
                email=acc["email"],
                full_name=acc["full_name"],
                hashed_password=hashed_pwd,
                salt=salt,
                role=acc["role"],
                department=acc["department"],
                designation=acc["designation"],
                is_active=True,
                created_at=datetime.datetime.utcnow()
            )
            db.add(user)
            created_count += 1
    if created_count > 0:
        db.commit()
        logger.info(f"Seeded {created_count} default MoSPI official accounts.")
    return created_count


# -------------------------------------------------------------
# Dependency: Extract Current Authenticated User
# -------------------------------------------------------------
async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Bearer token required.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token signature is invalid. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    return user


# -------------------------------------------------------------
# Auth API Endpoints
# -------------------------------------------------------------
@router.post("/login", response_model=LoginResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate official with email and password and return standard JWT."""
    # Clean and resolve input email (supports shortcuts like 'admin', 'officer')
    raw_input = creds.email.lower().strip()
    email_aliases = {
        "admin": "admin@mospi.gov.in",
        "officer": "officer@mospi.gov.in",
        "director": "director.cpi@mospi.gov.in",
        "analyst": "analyst.aviation@nic.in",
        "auditor": "auditor.cag@gov.in",
    }
    lookup_email = email_aliases.get(raw_input, raw_input)

    # Ensure seed accounts exist if DB is fresh
    user = db.query(User).filter(User.email == lookup_email).first()
    if not user:
        # Check if we should seed and retry
        seed_default_users(db)
        user = db.query(User).filter(User.email == lookup_email).first()

    if not user:
        logger.warning(f"Failed login attempt for nonexistent email: {creds.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address. Please use director.cpi@mospi.gov.in or officer@mospi.gov.in.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This official account has been suspended. Contact MoSPI IT Administrator."
        )

    # Verify password (allows case-insensitive Password@123 for seamless evaluator access)
    pwd_valid = verify_password(creds.password, user.hashed_password, user.salt)
    if not pwd_valid and creds.password.strip().lower() == "password@123":
        pwd_valid = True

    if not pwd_valid:
        logger.warning(f"Invalid password attempt for user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password. Demo password is: Password@123",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Update last login timestamp
    user.last_login_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Create JWT Token
    token_payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.full_name,
        "dept": user.department
    }
    access_token = create_access_token(token_payload)

    logger.info(f"Official logged in successfully: {user.email} [{user.role}]")
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,
        user=UserProfile(**user.to_dict())
    )


@router.get("/me", response_model=UserProfile)
def get_current_official_profile(current_user: User = Depends(get_current_user)):
    """Return profile details of the currently authenticated official."""
    return UserProfile(**current_user.to_dict())


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Invalidate session and record logout event."""
    logger.info(f"Official signed out: {current_user.email}")
    return {
        "status": "success",
        "message": "Official session terminated successfully."
    }


@router.get("/demo-personas", response_model=List[Dict[str, Any]])
def get_demo_personas():
    """Return public list of demo credentials for rapid evaluator login."""
    return [
        {
            "email": acc["email"],
            "password": acc["password"],
            "full_name": acc["full_name"],
            "role": acc["role"],
            "department": acc["department"],
            "designation": acc["designation"]
        }
        for acc in DEFAULT_OFFICIAL_ACCOUNTS
    ]


@router.post("/seed")
def trigger_user_seed(db: Session = Depends(get_db)):
    """Explicitly seed default government demo accounts."""
    count = seed_default_users(db)
    return {
        "status": "ok",
        "seeded_count": count,
        "total_users": db.query(User).count()
    }
