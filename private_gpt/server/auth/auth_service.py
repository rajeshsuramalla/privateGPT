"""Authentication and authorization service."""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import bcrypt
import jwt
from sqlalchemy.orm import Session
from sqlalchemy import and_

from private_gpt.server.auth.models import (
    User, Document, LLMModel, UserModelAccess,
    UserCreate, UserUpdate, UserRole, Permission, ROLE_PERMISSIONS,
    user_document_permissions
)
from private_gpt.settings.settings import settings

class AuthService:
    """Service for authentication and authorization operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.secret_key = getattr(settings().server.auth, 'jwt_secret', 'your-secret-key-change-in-production')
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if username or email already exists
        existing_user = self.db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing_user:
            raise ValueError("Username or email already exists")
        
        hashed_password = self._hash_password(user_data.password)
        
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role.value
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        user = self.get_user_by_username(username)
        if not user or not self._verify_password(password, str(user.hashed_password)):
            return None
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user."""
        permissions = self.get_user_permissions(user)
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode: Dict[str, Any] = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role,
            "permissions": permissions,
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: Optional[str] = payload.get("sub")
            if username is None:
                return None
            return payload
        except jwt.PyJWTError:
            return None

    def get_user_permissions(self, user: User) -> List[str]:
        """Get all permissions for a user based on their role."""
        role = UserRole(user.role)
        return [perm.value for perm in ROLE_PERMISSIONS.get(role, [])]

    def has_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        user_permissions = self.get_user_permissions(user)
        return permission.value in user_permissions

    def can_access_document(self, user: User, document_id: str, permission: Permission) -> bool:
        """Check if user can access a specific document with given permission."""
        # Get the document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        # SuperAdmin can access everything
        if str(user.role) == UserRole.SUPERADMIN.value:
            return True
            
        # Owner can access their own documents  
        if document.owner_id == user.id:  # type: ignore
            return True
            
        # Public documents can be read by anyone with read permission
        if bool(document.is_public) and permission == Permission.READ_DOCUMENT:
            return self.has_permission(user, Permission.READ_DOCUMENT)
            
        # Check specific document permissions
        doc_permission = self.db.query(user_document_permissions).filter(
            and_(
                user_document_permissions.c.user_id == user.id,
                user_document_permissions.c.document_id == document_id,
                user_document_permissions.c.permission == permission.value
            )
        ).first()
        
        return doc_permission is not None

    def grant_document_access(self, user_id: int, document_id: str, permissions: List[Permission]):
        """Grant document access to a user."""
        # Remove existing permissions for this user-document pair
        self.db.execute(
            user_document_permissions.delete().where(
                and_(
                    user_document_permissions.c.user_id == user_id,
                    user_document_permissions.c.document_id == document_id
                )
            )
        )
        
        # Add new permissions
        for permission in permissions:
            self.db.execute(
                user_document_permissions.insert().values(
                    user_id=user_id,
                    document_id=document_id,
                    permission=permission.value
                )
            )
        self.db.commit()

    def revoke_document_access(self, user_id: int, document_id: str):
        """Revoke all document access for a user."""
        self.db.execute(
            user_document_permissions.delete().where(
                and_(
                    user_document_permissions.c.user_id == user_id,
                    user_document_permissions.c.document_id == document_id
                )
            )
        )
        self.db.commit()

    def create_document_record(self, doc_id: str, filename: str, owner_id: int, is_public: bool = False) -> Document:
        """Create a document record in the database."""
        document = Document(
            id=doc_id,
            filename=filename,
            owner_id=owner_id,
            is_public=is_public
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_user_accessible_documents(self, user: User) -> List[Document]:
        """Get all documents a user can access."""
        if str(user.role) == UserRole.SUPERADMIN.value:
            return self.db.query(Document).all()
        
        # Documents owned by user
        owned_docs = self.db.query(Document).filter(Document.owner_id == user.id).all()
        
        # Public documents
        public_docs = self.db.query(Document).filter(Document.is_public == True).all()
        
        # Documents with explicit permissions
        permitted_doc_ids = self.db.query(user_document_permissions.c.document_id).filter(
            user_document_permissions.c.user_id == user.id
        ).distinct().all()
        
        permitted_docs = []
        if permitted_doc_ids:
            doc_ids = [row[0] for row in permitted_doc_ids]
            permitted_docs = self.db.query(Document).filter(Document.id.in_(doc_ids)).all()
        
        # Combine and deduplicate
        all_docs = {doc.id: doc for doc in owned_docs + public_docs + permitted_docs}
        return list(all_docs.values())

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "role" and value:
                setattr(user, field, value.value)
            else:
                setattr(user, field, value)
        
        # Note: updated_at is handled by the database if auto-update is configured
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True

    def get_all_users(self) -> List[User]:
        """Get all users."""
        return self.db.query(User).all()

    # LLM Model management
    def create_llm_model(self, name: str, provider: str, model_path: str, description: Optional[str] = None) -> LLMModel:
        """Create a new LLM model entry."""
        model = LLMModel(
            name=name,
            provider=provider,
            model_path=model_path,
            description=description
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_llm_models(self) -> List[LLMModel]:
        """Get all LLM models."""
        return self.db.query(LLMModel).filter(LLMModel.is_active == True).all()

    def get_user_accessible_models(self, user: User) -> List[LLMModel]:
        """Get LLM models accessible to a user."""
        if str(user.role) == UserRole.SUPERADMIN.value:
            return self.get_llm_models()
        
        # Get models with explicit access
        accessible_models = self.db.query(LLMModel).join(UserModelAccess).filter(
            and_(
                UserModelAccess.user_id == user.id,
                LLMModel.is_active == True
            )
        ).all()
        
        return accessible_models

    def grant_model_access(self, user_id: int, model_id: int):
        """Grant model access to a user."""
        # Check if access already exists
        existing = self.db.query(UserModelAccess).filter(
            and_(
                UserModelAccess.user_id == user_id,
                UserModelAccess.model_id == model_id
            )
        ).first()
        
        if not existing:
            access = UserModelAccess(user_id=user_id, model_id=model_id)
            self.db.add(access)
            self.db.commit()

    def revoke_model_access(self, user_id: int, model_id: int):
        """Revoke model access from a user."""
        access = self.db.query(UserModelAccess).filter(
            and_(
                UserModelAccess.user_id == user_id,
                UserModelAccess.model_id == model_id
            )
        ).first()
        
        if access:
            self.db.delete(access)
            self.db.commit()
