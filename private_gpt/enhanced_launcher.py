"""Enhanced launcher with RBAC, multi-model support, and document access control."""
import logging
from typing import Dict, Any
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from injector import Injector

# Import enhanced routers
from private_gpt.server.auth.auth_router import auth_router
from private_gpt.server.chat.enhanced_chat_router import enhanced_chat_router
from private_gpt.server.ingest.enhanced_ingest_router import enhanced_ingest_router

# Import original routers for backward compatibility
from private_gpt.server.chat.chat_router import chat_router
from private_gpt.server.chunks.chunks_router import chunks_router
from private_gpt.server.completions.completions_router import completions_router
from private_gpt.server.embeddings.embeddings_router import embeddings_router
from private_gpt.server.health.health_router import health_router
from private_gpt.server.ingest.ingest_router import ingest_router
from private_gpt.server.recipes.summarize.summarize_router import summarize_router

# Import authentication system
from private_gpt.server.auth.init_enhanced import setup_enhanced_private_gpt

from private_gpt.settings.settings import Settings

logger = logging.getLogger(__name__)

def create_enhanced_app(root_injector: Injector) -> FastAPI:
    """Create enhanced FastAPI application with RBAC and multi-model support."""
    
    # Initialize enhanced features
    try:
        logger.info("Initializing enhanced PrivateGPT features...")
        setup_enhanced_private_gpt()
    except Exception as e:
        logger.warning(f"Failed to initialize enhanced features: {e}")
        logger.info("Continuing with basic functionality...")
    
    # Start the API
    async def bind_injector_to_request(request: Request) -> None:
        request.state.injector = root_injector

    app = FastAPI(
        title="Enhanced PrivateGPT API",
        description="A private GPT API with role-based access control, document ownership, and multi-model support",
        version="0.6.2-enhanced",
        dependencies=[Depends(bind_injector_to_request)]
    )

    # Enhanced routers (with authentication and authorization)
    app.include_router(auth_router)
    app.include_router(enhanced_chat_router)
    app.include_router(enhanced_ingest_router)
    
    # Original routers (for backward compatibility)
    app.include_router(completions_router)
    app.include_router(chat_router)
    app.include_router(chunks_router)
    app.include_router(embeddings_router)
    app.include_router(health_router)
    app.include_router(ingest_router)
    app.include_router(summarize_router)

    # Configure CORS
    settings = root_injector.get(Settings)
    if settings.server.cors.enabled:
        logger.debug("Setting up CORS")
        # Handle allow_origin_regex - convert list to string if needed
        origin_regex = settings.server.cors.allow_origin_regex
        if origin_regex and len(origin_regex) > 0:
            origin_regex = origin_regex[0]  # Take first regex if it's a list
        else:
            origin_regex = None
        
        app.add_middleware(
            CORSMiddleware,
            allow_credentials=settings.server.cors.allow_credentials,
            allow_origins=settings.server.cors.allow_origins,
            allow_origin_regex=origin_regex,
            allow_methods=settings.server.cors.allow_methods,
            allow_headers=settings.server.cors.allow_headers,
        )

    @app.get("/health/enhanced")
    async def enhanced_health_check() -> Dict[str, Any]:  # type: ignore # FastAPI route handler
        """Enhanced health check with feature status."""
        try:
            from private_gpt.server.auth.database import SessionLocal
            from private_gpt.server.auth.auth_service import AuthService
            
            # Test database connection
            db = SessionLocal()
            try:
                auth_service = AuthService(db)
                user_count = len(auth_service.get_all_users())
                model_count = len(auth_service.get_llm_models())
                
                return {
                    "status": "healthy",
                    "features": {
                        "authentication": True,
                        "role_based_access": True,
                        "document_ownership": True,
                        "multi_model_support": True
                    },
                    "stats": {
                        "total_users": user_count,
                        "total_models": model_count
                    },
                    "version": "0.6.2-enhanced"
                }
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Enhanced health check failed: {e}")
            return {
                "status": "degraded",
                "error": str(e),
                "features": {
                    "authentication": False,
                    "role_based_access": False,
                    "document_ownership": False,
                    "multi_model_support": False
                },
                "version": "0.6.2-enhanced"
            }

    @app.get("/")
    async def root() -> Dict[str, Any]:  # type: ignore # FastAPI route handler
        """Root endpoint with enhanced API information."""
        return {
            "message": "Enhanced PrivateGPT API",
            "version": "0.6.2-enhanced",
            "features": [
                "Role-based access control (SuperAdmin, Admin, User)",
                "Document-specific access permissions",
                "JWT-based authentication",
                "Multi-model support (Ollama, OpenAI)",
                "Document ownership tracking",
                "Enhanced chat with model selection",
                "Backward compatibility with original API"
            ],
            "authentication": {
                "enabled": True,
                "endpoints": {
                    "login": "/v1/auth/login",
                    "user_info": "/v1/auth/me",
                    "users": "/v1/auth/users"
                }
            },
            "enhanced_endpoints": {
                "chat": "/v1/chat/completions (with model selection)",
                "models": "/v1/chat/models",
                "ingest": "/v1/ingest/* (with ownership)",
                "documents": "/v1/ingest/my-documents"
            },
            "documentation": "/docs"
        }

    # Mount UI if enabled
    settings = root_injector.get(Settings)
    if settings.ui.enabled:
        try:
            logger.info("Mounting UI...")
            import gradio as gr
            from private_gpt.ui.ui import PrivateGptUi
            private_gpt_ui = root_injector.get(PrivateGptUi)
            ui_blocks = private_gpt_ui.get_ui_blocks()
            app = gr.mount_gradio_app(app, ui_blocks, path=settings.ui.path)
            logger.info(f"UI mounted successfully at {settings.ui.path}")
        except Exception as e:
            logger.error(f"Failed to mount UI: {e}")

    logger.info("Enhanced PrivateGPT API created successfully")
    return app
