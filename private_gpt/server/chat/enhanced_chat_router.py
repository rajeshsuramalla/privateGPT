"""Enhanced chat router with role-based access control and multi-model support."""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from llama_index.core.llms import ChatMessage, MessageRole
from pydantic import BaseModel, Field, ConfigDict
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session

from private_gpt.open_ai.extensions.context_filter import ContextFilter
from private_gpt.open_ai.openai_models import (
    OpenAICompletion,
    OpenAIMessage,
    to_openai_response,
    to_openai_sse_stream,
)
from private_gpt.server.chat.chat_service import ChatService
from private_gpt.server.auth.auth import get_current_user
from private_gpt.server.auth.database import get_db
from private_gpt.server.auth.auth_service import AuthService
from private_gpt.server.auth.models import User

logger = logging.getLogger(__name__)

enhanced_chat_router = APIRouter(prefix="/v1", tags=["Enhanced Chat"])

class EnhancedChatBody(BaseModel):
    messages: list[OpenAIMessage]
    use_context: bool = Field(default=False, description="Use context from ingested documents")
    context_filter: ContextFilter | None = Field(
        default=None,
        description="Filter to apply to documents for context retrieval"
    )
    include_sources: bool = Field(default=True, description="Include source references")
    stream: bool = Field(default=False, description="Stream the response")
    model: Optional[str] = Field(
        default=None,
        description="Specific model to use (e.g., 'ollama:llama3.1', 'openai:gpt-4')"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello, how are you?"}
                    ],
                    "use_context": True,
                    "include_sources": True,
                    "stream": False,
                    "model": "ollama:llama3.1"
                }
            ]
        }
    )

@enhanced_chat_router.post(
    "/chat/completions",
    response_model=None,
    responses={200: {"model": OpenAICompletion}},
    tags=["Enhanced Chat"],
    openapi_extra={
        "x-fern-streaming": {
            "stream-condition": "stream",
            "response": {"$ref": "#/components/schemas/OpenAICompletion"},
            "response-stream": {"$ref": "#/components/schemas/OpenAICompletion"},
        }
    },
)
def enhanced_chat_completion(
    request: Request, 
    body: EnhancedChatBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OpenAICompletion | StreamingResponse:
    """Enhanced chat completion with model selection and access control.

    This endpoint provides enhanced chat functionality with:
    - Model selection support
    - Role-based access control
    - Document-specific context filtering
    - User permission validation

    Requires authentication and appropriate permissions based on usage:
    - Basic chat: requires 'chat' permission
    - Chat with context: requires 'chat_with_context' permission
    """
    auth_service = AuthService(db)
    
    # Check permissions based on context usage
    if body.use_context:
        from private_gpt.server.auth.models import Permission
        if not auth_service.has_permission(current_user, Permission.CHAT_WITH_CONTEXT):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for context-aware chat"
            )
    else:
        from private_gpt.server.auth.models import Permission
        if not auth_service.has_permission(current_user, Permission.CHAT):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for chat"
            )
    
    # For now, we'll use the standard LLM without model validation
    # In a full implementation, this would check user's model access
    if body.model:
        logger.info(f"User {current_user.username} requested model: {body.model}")
        # Model validation would go here
    
    # Filter context based on user's document access
    filtered_context_filter = body.context_filter
    if body.use_context and body.context_filter:
        # Use all accessible documents
        accessible_docs = auth_service.get_user_accessible_documents(current_user)
        accessible_doc_ids = [doc.id for doc in accessible_docs]
        
        # Filter the context to only include accessible documents
        if body.context_filter and body.context_filter.docs_ids:
            # Intersection of requested docs and accessible docs
            allowed_doc_ids = list(set(body.context_filter.docs_ids) & set(accessible_doc_ids))
            filtered_context_filter = ContextFilter(docs_ids=allowed_doc_ids)
        else:
            # Use all accessible documents
            filtered_context_filter = ContextFilter(docs_ids=[str(doc_id) for doc_id in accessible_doc_ids])
    
    # Get the chat service
    service = request.state.injector.get(ChatService)
    
    # Convert OpenAI messages to ChatMessage format
    all_messages = [
        ChatMessage(content=m.content, role=MessageRole(m.role)) for m in body.messages
    ]
    
    # Handle streaming vs non-streaming response
    if body.stream:
        if hasattr(service, 'stream_chat_with_model'):
            completion_gen = service.stream_chat_with_model(
                messages=all_messages,
                use_context=body.use_context,
                context_filter=filtered_context_filter,
                model_name=body.model
            )
        else:
            completion_gen = service.stream_chat(
                messages=all_messages,
                use_context=body.use_context,
                context_filter=filtered_context_filter,
            )
        
        return StreamingResponse(
            to_openai_sse_stream(
                completion_gen.response,
                completion_gen.sources if body.include_sources else None,
            ),
            media_type="text/event-stream",
        )
    else:
        if hasattr(service, 'chat_with_model'):
            completion = service.chat_with_model(
                messages=all_messages,
                use_context=body.use_context,
                context_filter=filtered_context_filter,
                model_name=body.model
            )
        else:
            completion = service.chat(
                messages=all_messages,
                use_context=body.use_context,
                context_filter=filtered_context_filter,
            )
        
        return to_openai_response(
            completion.response, 
            completion.sources if body.include_sources else None
        )

@enhanced_chat_router.get("/chat/models")
def get_available_models(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get models available to the current user."""
    try:
        # Get auth service to access user's models
        auth_service = AuthService(db)
        
        # Get user accessible models
        user_models = auth_service.get_user_accessible_models(current_user)
        
        models_list = []
        for model in user_models:
            # Split provider:model_name format
            if ':' in model.model_id:
                provider, model_name = model.model_id.split(':', 1)
            else:
                provider = 'default'
                model_name = model.model_id
            
            models_list.append({
                "provider": provider,
                "name": model_name,
                "id": model.model_id,
                "available": True
            })
        
        # If no models found, provide default
        if not models_list:
            models_list = [{
                "provider": "default",
                "name": "llamacpp",
                "id": "default:llamacpp",
                "available": True
            }]
        
        return {
            "models": models_list,
            "count": len(models_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting models for user {current_user.username}: {e}")
        # Return default model on error
        return {
            "models": [{
                "provider": "default",
                "name": "llamacpp",
                "id": "default:llamacpp",
                "available": True
            }],
            "count": 1
        }
