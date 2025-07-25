"""Initialization script for enhanced PrivateGPT with RBAC and multi-model support."""
import logging

from private_gpt.server.auth.database import init_db, SessionLocal
from private_gpt.server.auth.auth_service import AuthService
from private_gpt.server.auth.models import UserCreate, UserRole

logger = logging.getLogger(__name__)

def initialize_default_models():
    """Initialize default LLM models in the database."""
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        
        # Check if models already exist
        existing_models = auth_service.get_llm_models()
        if existing_models:
            logger.info(f"Found {len(existing_models)} existing models")
            return
        
        # Add default Ollama models
        default_ollama_models = [
            {
                "name": "llama3.1",
                "provider": "ollama", 
                "model_path": "llama3.1",
                "description": "Meta's Llama 3.1 model via Ollama"
            },
            {
                "name": "llama3.1:8b",
                "provider": "ollama",
                "model_path": "llama3.1:8b", 
                "description": "Meta's Llama 3.1 8B model via Ollama"
            },
            {
                "name": "codellama",
                "provider": "ollama",
                "model_path": "codellama",
                "description": "Code Llama model for programming tasks"
            },
            {
                "name": "nomic-embed-text",
                "provider": "ollama",
                "model_path": "nomic-embed-text",
                "description": "Nomic embedding model for text"
            }
        ]
        
        # Add default OpenAI models (will be available if API key is configured)
        default_openai_models = [
            {
                "name": "gpt-3.5-turbo",
                "provider": "openai",
                "model_path": "gpt-3.5-turbo",
                "description": "OpenAI GPT-3.5 Turbo model"
            },
            {
                "name": "gpt-4",
                "provider": "openai", 
                "model_path": "gpt-4",
                "description": "OpenAI GPT-4 model"
            },
            {
                "name": "gpt-4-turbo",
                "provider": "openai",
                "model_path": "gpt-4-turbo",
                "description": "OpenAI GPT-4 Turbo model"
            }
        ]
        
        # Create model entries
        for model_info in default_ollama_models + default_openai_models:
            try:
                model = auth_service.create_llm_model(
                    name=model_info["name"],
                    provider=model_info["provider"],
                    model_path=model_info["model_path"],
                    description=model_info["description"]
                )
                logger.info(f"Created model: {model.provider}:{model.name}")
            except Exception as e:
                logger.warning(f"Failed to create model {model_info['name']}: {e}")
                
    finally:
        db.close()

def initialize_default_users():
    """Initialize default users and grant model access."""
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        
        # Check if superadmin already exists
        existing_superadmin = auth_service.get_user_by_username("superadmin")
        if existing_superadmin:
            logger.info("Superadmin user already exists")
        else:
            # Create default superadmin
            superadmin_data = UserCreate(
                username="superadmin",
                email="superadmin@privategpt.local",
                password="admin123!",
                role=UserRole.SUPERADMIN
            )
            superadmin = auth_service.create_user(superadmin_data)
            logger.info("Created default superadmin user")
            
            # Grant access to all models for superadmin
            models = auth_service.get_llm_models()
            for model in models:
                auth_service.grant_model_access(superadmin.id.__int__(), model.id.__int__())
            logger.info(f"Granted access to {len(models)} models for superadmin")
        
        # Create demo admin user
        existing_admin = auth_service.get_user_by_username("admin")
        if not existing_admin:
            admin_data = UserCreate(
                username="admin",
                email="admin@privategpt.local", 
                password="admin123!",
                role=UserRole.ADMIN
            )
            admin = auth_service.create_user(admin_data)
            logger.info("Created demo admin user")
            
            # Grant access to Ollama models for admin
            models = auth_service.get_llm_models()
            ollama_models = [m for m in models if getattr(m, "provider", None) == "ollama"]
            for model in ollama_models:
                auth_service.grant_model_access(admin.id.__int__(), model.id.__int__())
            logger.info(f"Granted access to {len(ollama_models)} Ollama models for admin")
        
        # Create demo user
        existing_user = auth_service.get_user_by_username("user")
        if not existing_user:
            user_data = UserCreate(
                username="user",
                email="user@privategpt.local",
                password="user123!",
                role=UserRole.USER
            )
            user = auth_service.create_user(user_data)
            logger.info("Created demo user")
            
            # Grant access to basic Ollama model for user
            models = auth_service.get_llm_models()
            basic_models = [m for m in models if m.name in ["llama3.1", "llama3.1:8b"]]
            for model in basic_models:
                auth_service.grant_model_access(user.id.__int__(), model.id.__int__())
            logger.info(f"Granted access to {len(basic_models)} basic models for user")
                
    finally:
        db.close()

def setup_enhanced_private_gpt():
    """Complete setup for enhanced PrivateGPT."""
    logger.info("Setting up enhanced PrivateGPT with RBAC and multi-model support...")
    
    try:
        # Initialize database and tables
        logger.info("Initializing database...")
        init_db()
        
        # Initialize default models
        logger.info("Initializing default models...")
        initialize_default_models()
        
        # Initialize default users
        logger.info("Initializing default users...")
        initialize_default_users()
        
        logger.info("Enhanced PrivateGPT setup completed successfully!")
        
        # Print setup information
        print("\n" + "="*70)
        print("🚀 Enhanced PrivateGPT Setup Complete!")
        print("="*70)
        print("\n📋 Default Users Created:")
        print("   👑 SuperAdmin: username=superadmin, password=admin123!")
        print("   🛡️  Admin:      username=admin,      password=admin123!")
        print("   👤 User:       username=user,       password=user123!")
        print("\n🔒 Security Features:")
        print("   ✅ Role-based access control (RBAC)")
        print("   ✅ Document-specific permissions")
        print("   ✅ JWT-based authentication")
        print("   ✅ Multi-model support with access control")
        print("\n🤖 Available Model Providers:")
        print("   🦙 Ollama (local models)")
        print("   🧠 OpenAI (with API key)")
        print("\n📚 API Endpoints:")
        print("   🔐 /v1/auth/* - Authentication & user management")
        print("   💬 /v1/chat/* - Enhanced chat with model selection")
        print("   📄 /v1/ingest/* - Document ingestion with ownership")
        print("\n⚠️  IMPORTANT:")
        print("   🔑 Change default passwords in production!")
        print("   🛡️  Update JWT secret in settings!")
        print("   🔒 Configure proper database in production!")
        print("="*70)
        
    except Exception as e:
        logger.error(f"Failed to setup enhanced PrivateGPT: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_enhanced_private_gpt()
