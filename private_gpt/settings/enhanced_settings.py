"""Enhanced settings with authentication and multi-model support."""
from pydantic import BaseModel, Field
from private_gpt.settings.settings import AuthSettings

class EnhancedAuthSettings(AuthSettings):
    """Enhanced authentication configuration."""
    
    # JWT Configuration
    jwt_secret: str = Field(
        description="Secret key for JWT token signing. Change this in production!",
        default="your-secret-key-change-in-production"
    )
    jwt_algorithm: str = Field(
        description="Algorithm for JWT token signing",
        default="HS256"
    )
    access_token_expire_minutes: int = Field(
        description="JWT token expiration time in minutes",
        default=30
    )
    
    # Database Configuration
    database_url: str = Field(
        description="Database URL for user and document management",
        default="sqlite:///./private_gpt.db"
    )
    
    # Default permissions
    create_default_superadmin: bool = Field(
        description="Create default superadmin user on startup",
        default=True
    )

class MultiModelSettings(BaseModel):
    """Multi-model configuration."""
    
    enabled: bool = Field(
        description="Enable multi-model support",
        default=True
    )
    
    # Ollama Configuration
    ollama_enabled: bool = Field(
        description="Enable Ollama models",
        default=True
    )
    ollama_base_url: str = Field(
        description="Ollama server base URL",
        default="http://localhost:11434"
    )
    
    # OpenAI Configuration
    openai_enabled: bool = Field(
        description="Enable OpenAI models",
        default=False
    )
    openai_api_key: str = Field(
        description="OpenAI API key",
        default=""
    )
    
    # Default model
    default_model_provider: str = Field(
        description="Default model provider (ollama, openai)",
        default="ollama"
    )
    default_model_name: str = Field(
        description="Default model name",
        default="llama3.1"
    )

class RoleBasedAccessSettings(BaseModel):
    """Role-based access control settings."""
    
    enabled: bool = Field(
        description="Enable role-based access control",
        default=True
    )
    
    # Document permissions
    allow_public_documents: bool = Field(
        description="Allow users to make documents public",
        default=True
    )
    
    # Default user permissions
    default_user_can_ingest: bool = Field(
        description="Allow regular users to ingest documents by default",
        default=False
    )
    
    # Admin settings
    admin_can_see_all_documents: bool = Field(
        description="Allow admins to see all documents",
        default=True
    )
    
    # Model access
    restrict_model_access: bool = Field(
        description="Restrict model access based on user permissions",
        default=True
    )
