"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from private_gpt.server.auth.models import Base
from typing import Generator
import os

# Database URL - using SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./private_gpt.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database with default data."""
    create_tables()
    
    # Create default superadmin user if not exists
    from private_gpt.server.auth.auth_service import AuthService
    from private_gpt.server.auth.models import UserCreate, UserRole
    
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        
        # Check if superadmin exists
        existing_superadmin = auth_service.get_user_by_username("superadmin")
        if not existing_superadmin:
            superadmin_data = UserCreate(
                username="superadmin",
                email="superadmin@privategpt.local",
                password="admin123!",  # Should be changed in production
                role=UserRole.SUPERADMIN
            )
            auth_service.create_user(superadmin_data)
            print("Created default superadmin user (username: superadmin, password: admin123!)")
    finally:
        db.close()
