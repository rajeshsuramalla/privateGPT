"""Enhanced authentication and authorization system for PrivateGPT."""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from private_gpt.server.auth.database import get_db
from private_gpt.server.auth.auth_service import AuthService
from private_gpt.server.auth.models import User, Permission, UserRole
from private_gpt.settings.settings import settings

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# 401 signify that the request requires authentication.
# 403 signify that the authenticated user is not authorized to perform the operation.
NOT_AUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)

NOT_AUTHORIZED = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not authorized to perform this operation",
)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    auth_service = AuthService(db)
    
    if not credentials:
        raise NOT_AUTHENTICATED
    
    token_data = auth_service.verify_token(credentials.credentials)  # type: ignore
    if not token_data:
        raise NOT_AUTHENTICATED
    
    # Type assertion since we know token_data is not None here
    username = str(token_data.get("sub", ""))  # type: ignore
    if not username:
        raise NOT_AUTHENTICATED
        
    user = auth_service.get_user_by_username(username)
    if not user or not bool(user.is_active):
        raise NOT_AUTHENTICATED
    
    return user

def require_permission(permission: Permission):
    """Decorator factory to require specific permissions."""
    def permission_dependency(current_user: User = Depends(get_current_user)) -> User:
        auth_service = AuthService(next(get_db()))
        if not auth_service.has_permission(current_user, permission):
            raise NOT_AUTHORIZED
        return current_user
    return permission_dependency

def require_role(*allowed_roles: UserRole):
    """Decorator factory to require specific roles."""
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in [role.value for role in allowed_roles]:
            raise NOT_AUTHORIZED
        return current_user
    return role_dependency

def require_document_access(permission: Permission):
    """Decorator factory to require document-specific access."""
    def document_access_dependency(
        document_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        auth_service = AuthService(db)
        if not auth_service.can_access_document(current_user, document_id, permission):
            raise NOT_AUTHORIZED
        return current_user
    return document_access_dependency



# Main authentication dependency
if not settings().server.auth.enabled:
    logger.debug("Authentication disabled - using dummy authentication")
    
    def authenticated() -> bool:  # type: ignore
        """Dummy authentication when auth is disabled."""
        return True
else:
    logger.info("Using JWT-based authentication")
    
    def authenticated(current_user: User = Depends(get_current_user)) -> User:  # type: ignore
        """JWT-based authentication."""
        return current_user

# Convenience dependencies for common permission checks
require_chat = require_permission(Permission.CHAT)
require_chat_with_context = require_permission(Permission.CHAT_WITH_CONTEXT)
require_ingest = require_permission(Permission.INGEST_DOCUMENT)
require_admin = require_role(UserRole.ADMIN, UserRole.SUPERADMIN)
require_superadmin = require_role(UserRole.SUPERADMIN)
