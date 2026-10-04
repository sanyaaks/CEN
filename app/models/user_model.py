import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.db import Base


class User(Base):
    """
    Authorized personnel user model for MoSPI Civil Aviation Airfare Index.
    Roles:
    - ADMIN: Full system access (trigger scraping, alter weights, export raw data, manage users)
    - OFFICER: MoSPI / NSO Statistical Officer (run validations, backtest analyses, download official indices)
    - ANALYST: Aviation Data Analyst (view audit trails, inspect outliers and route trends)
    - VIEWER: General access with authenticated session
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    hashed_password = Column(String(128), nullable=False)
    salt = Column(String(64), nullable=False)
    
    role = Column(String(30), default="OFFICER", nullable=False, index=True)
    department = Column(String(200), default="Ministry of Statistics & Programme Implementation (MoSPI)", nullable=False)
    designation = Column(String(150), default="Statistical Officer", nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "department": self.department,
            "designation": self.designation,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
