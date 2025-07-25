"""Authentication and user management API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from private_gpt.server.auth.database import get_db
from private_gpt.server.auth.auth_service import AuthService
from private_gpt.server.auth.auth import (
    get_current_user, require_admin, require_superadmin
)
from private_gpt.server.auth.models import (
    User, UserCreate, UserResponse, UserUpdate, LoginRequest, Token,
    DocumentAccessRequest, ModelAccessRequest, LLMModelCreate, LLMModelResponse
)

auth_router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

@auth_router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    auth_service = AuthService(db)
    
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = auth_service.create_access_token(user)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user)
    )

@auth_router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse.model_validate(current_user)

@auth_router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new user. Requires admin privileges."""
    auth_service = AuthService(db)
    
    try:
        user = auth_service.create_user(user_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@auth_router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users. Requires admin privileges."""
    auth_service = AuthService(db)
    users = auth_service.get_all_users()
    return [UserResponse.model_validate(user) for user in users]

@auth_router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get user by ID. Requires admin privileges."""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)

@auth_router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user information. Requires admin privileges."""
    auth_service = AuthService(db)
    user = auth_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)

@auth_router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Delete a user. Requires superadmin privileges."""
    auth_service = AuthService(db)
    success = auth_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@auth_router.post("/documents/access")
def grant_document_access(
    access_data: DocumentAccessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Grant document access to a user. Requires admin privileges."""
    auth_service = AuthService(db)
    auth_service.grant_document_access(
        access_data.user_id,
        access_data.document_id,
        access_data.permissions
    )
    return {"message": "Document access granted successfully"}

@auth_router.delete("/documents/{document_id}/access/{user_id}")
def revoke_document_access(
    document_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Revoke document access from a user. Requires admin privileges."""
    auth_service = AuthService(db)
    auth_service.revoke_document_access(user_id, document_id)
    return {"message": "Document access revoked successfully"}

@auth_router.post("/models", response_model=LLMModelResponse)
def create_llm_model(
    model_data: LLMModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Create a new LLM model entry. Requires superadmin privileges."""
    auth_service = AuthService(db)
    model = auth_service.create_llm_model(
        model_data.name,
        model_data.provider,
        model_data.model_path,
        model_data.description or ""
    )
    return LLMModelResponse.model_validate(model)

@auth_router.get("/models", response_model=List[LLMModelResponse])
def list_llm_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List accessible LLM models for the current user."""
    auth_service = AuthService(db)
    models = auth_service.get_user_accessible_models(current_user)
    return [LLMModelResponse.model_validate(model) for model in models]

@auth_router.post("/models/access")
def grant_model_access(
    access_data: ModelAccessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Grant model access to a user. Requires admin privileges."""
    auth_service = AuthService(db)
    auth_service.grant_model_access(access_data.user_id, access_data.model_id)
    return {"message": "Model access granted successfully"}

@auth_router.delete("/models/{model_id}/access/{user_id}")
def revoke_model_access(
    model_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Revoke model access from a user. Requires admin privileges."""
    auth_service = AuthService(db)
    auth_service.revoke_model_access(user_id, model_id)
    return {"message": "Model access revoked successfully"}
