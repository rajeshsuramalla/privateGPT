"""Enhanced PrivateGPT entry point with RBAC and multi-model support."""
import logging
import uvicorn
from injector import Injector

from private_gpt.di import create_application_injector
from private_gpt.enhanced_launcher import create_enhanced_app
from private_gpt.settings.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for enhanced PrivateGPT."""
    logger.info("Starting Enhanced PrivateGPT server...")
    
    # Create dependency injection container
    root_injector: Injector = create_application_injector()
    
    # Create enhanced FastAPI app
    app = create_enhanced_app(root_injector)
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings().server.port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
