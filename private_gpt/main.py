"""FastAPI app creation, logger configuration and main API routes."""

from private_gpt.di import global_injector
from private_gpt.enhanced_launcher import create_enhanced_app

app = create_enhanced_app(global_injector)
