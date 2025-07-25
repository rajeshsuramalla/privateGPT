"""Authentication and authorization models."""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    SUPERADMIN = "superadmin"
    ADMIN = "admin" 
    USER = "user"

class Permission(str, Enum):
    """Available permissions in the system."""
    # Document permissions
    READ_DOCUMENT = "read_document"
    WRITE_DOCUMENT = "write_document"
    DELETE_DOCUMENT = "delete_document"
    INGEST_DOCUMENT = "ingest_document"
    
    # Chat permissions
    CHAT = "chat"
    CHAT_WITH_CONTEXT = "chat_with_context"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_MODELS = "manage_models"
    VIEW_SYSTEM_LOGS = "view_system_logs"
    
    # Super admin permissions
    MANAGE_SYSTEM = "manage_system"
    MANAGE_PERMISSIONS = "manage_permissions"

# Association table for user-document permissions
user_document_permissions = Table(
    'user_document_permissions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('document_id', String, ForeignKey('documents.id')),
    Column('permission', String)
)

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default=UserRole.USER.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    documents = relationship("Document", back_populates="owner")
    model_access = relationship("UserModelAccess", back_populates="user")

class Document(Base):
    """Document model with ownership and access control."""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True)  # Document ID from ingestion
    filename = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    owner = relationship("User", back_populates="documents")

class LLMModel(Base):
    """Available LLM models in the system."""
    __tablename__ = "llm_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # e.g., "llama3.1", "codellama"
    provider = Column(String, nullable=False)  # e.g., "ollama", "openai", "local"
    model_path = Column(String, nullable=False)  # Path or identifier for the model
    is_active = Column(Boolean, default=True)
    description = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user_access = relationship("UserModelAccess", back_populates="model")

class UserModelAccess(Base):
    """User access to specific LLM models."""
    __tablename__ = "user_model_access"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    model_id = Column(Integer, ForeignKey('llm_models.id'), nullable=False)
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="model_access")
    model = relationship("LLMModel", back_populates="user_access")

# Pydantic models for API
class UserCreate(BaseModel):
    """Model for creating a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER

class UserResponse(BaseModel):
    """Model for user responses."""
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Model for updating user information."""
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    permissions: list[str] = []

class Token(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str

class DocumentAccessRequest(BaseModel):
    """Request model for granting document access."""
    user_id: int
    document_id: str
    permissions: list[Permission]

class ModelAccessRequest(BaseModel):
    """Request model for granting model access."""
    user_id: int
    model_id: int

class LLMModelCreate(BaseModel):
    """Model for creating a new LLM model entry."""
    name: str
    provider: str
    model_path: str
    description: Optional[str] = None

class LLMModelResponse(BaseModel):
    """Model for LLM model responses."""
    id: int
    name: str
    provider: str
    model_path: str
    is_active: bool
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.SUPERADMIN: [
        Permission.READ_DOCUMENT,
        Permission.WRITE_DOCUMENT,
        Permission.DELETE_DOCUMENT,
        Permission.INGEST_DOCUMENT,
        Permission.CHAT,
        Permission.CHAT_WITH_CONTEXT,
        Permission.MANAGE_USERS,
        Permission.MANAGE_MODELS,
        Permission.VIEW_SYSTEM_LOGS,
        Permission.MANAGE_SYSTEM,
        Permission.MANAGE_PERMISSIONS,
    ],
    UserRole.ADMIN: [
        Permission.READ_DOCUMENT,
        Permission.WRITE_DOCUMENT,
        Permission.DELETE_DOCUMENT,
        Permission.INGEST_DOCUMENT,
        Permission.CHAT,
        Permission.CHAT_WITH_CONTEXT,
        Permission.MANAGE_USERS,
        Permission.VIEW_SYSTEM_LOGS,
    ],
    UserRole.USER: [
        Permission.READ_DOCUMENT,
        Permission.CHAT,
        Permission.CHAT_WITH_CONTEXT,
    ]
}
