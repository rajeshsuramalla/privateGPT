"""Enhanced ingest router with document ownership and access control."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from private_gpt.server.ingest.ingest_service import IngestService
from private_gpt.server.ingest.model import IngestedDoc
from private_gpt.server.auth.auth import get_current_user, require_permission
from private_gpt.server.auth.database import get_db
from private_gpt.server.auth.auth_service import AuthService
from private_gpt.server.auth.models import User, Permission

enhanced_ingest_router = APIRouter(prefix="/v1", tags=["Enhanced Ingestion"])

class EnhancedIngestTextBody(BaseModel):
    file_name: str = Field(examples=["Avatar: The Last Airbender"])
    text: str = Field(
        examples=[
            "Avatar is set in an Asian and Arctic-inspired world in which some "
            "people can telekinetically manipulate one of the four elements—water, "
            "earth, fire or air—through practices known as 'bending', inspired by "
            "Chinese martial arts."
        ]
    )
    is_public: bool = Field(default=False, description="Make document accessible to all users")

class EnhancedIngestResponse(BaseModel):
    object: str = "list"
    model: str = "private-gpt"
    data: List[IngestedDoc]
    owner_id: int
    is_public: bool

@enhanced_ingest_router.post("/ingest/file", tags=["Enhanced Ingestion"])
def enhanced_ingest_file(
    request: Request, 
    file: UploadFile,
    is_public: bool = False,
    current_user: User = Depends(require_permission(Permission.INGEST_DOCUMENT)),
    db: Session = Depends(get_db)
) -> EnhancedIngestResponse:
    """Ingest and process a file with ownership tracking.

    The file will be associated with the authenticated user as the owner.
    Access control will be applied based on the ownership and public settings.
    """
    service = request.state.injector.get(IngestService)
    auth_service = AuthService(db)
    
    if file.filename is None:
        raise HTTPException(400, "No file name provided")
    
    # Ingest the file
    ingested_documents = service.ingest_bin_data(file.filename, file.file)
    
    # Create document records with ownership
    for doc in ingested_documents:
        auth_service.create_document_record(
            doc_id=doc.doc_id,
            filename=file.filename,
            owner_id=current_user.id.__int__(),
            is_public=is_public
        )
    
    return EnhancedIngestResponse(
        data=ingested_documents,
        owner_id=current_user.id.__int__(),
        is_public=is_public
    )

@enhanced_ingest_router.post("/ingest/text", tags=["Enhanced Ingestion"])
def enhanced_ingest_text(
    request: Request, 
    body: EnhancedIngestTextBody,
    current_user: User = Depends(require_permission(Permission.INGEST_DOCUMENT)),
    db: Session = Depends(get_db)
) -> EnhancedIngestResponse:
    """Ingest and process text with ownership tracking."""
    service = request.state.injector.get(IngestService)
    auth_service = AuthService(db)
    
    if len(body.file_name) == 0:
        raise HTTPException(400, "No file name provided")
    
    # Ingest the text
    ingested_documents = service.ingest_text(body.file_name, body.text)
    
    # Create document records with ownership
    for doc in ingested_documents:
        auth_service.create_document_record(
            doc_id=doc.doc_id,
            filename=body.file_name,
            owner_id=current_user.id.__int__(),
            is_public=body.is_public
        )
    
    return EnhancedIngestResponse(
        data=ingested_documents,
        owner_id=current_user.id.__int__(),
        is_public=body.is_public
    )

@enhanced_ingest_router.get("/ingest/list", tags=["Enhanced Ingestion"])
def enhanced_list_ingested(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> EnhancedIngestResponse:
    """List ingested documents accessible to the current user.
    
    Returns only documents that the user owns, has explicit access to, or are public.
    """
    service = request.state.injector.get(IngestService)
    auth_service = AuthService(db)
    
    # Get all ingested documents
    all_ingested_documents = service.list_ingested()
    
    # Get user's accessible documents
    accessible_docs = auth_service.get_user_accessible_documents(current_user)
    accessible_doc_ids = {doc.id for doc in accessible_docs}
    
    # Filter ingested documents based on access
    filtered_documents = [
        doc for doc in all_ingested_documents 
        if doc.doc_id in accessible_doc_ids
    ]
    
    return EnhancedIngestResponse(
        data=filtered_documents,
        owner_id=current_user.id.__int__(),
        is_public=False  # Mixed ownership
    )

class DeleteResponse(BaseModel):
    """Delete operation response model."""
    message: str

@enhanced_ingest_router.delete("/ingest/{doc_id}", tags=["Enhanced Ingestion"])
def enhanced_delete_ingested(
    request: Request, 
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DeleteResponse:
    """Delete an ingested document.
    
    Only the document owner or users with DELETE_DOCUMENT permission can delete.
    """
    from private_gpt.server.auth.models import Document
    
    service = request.state.injector.get(IngestService)
    auth_service = AuthService(db)
    
    # Check if user can delete this document
    if not auth_service.can_access_document(current_user, doc_id, Permission.DELETE_DOCUMENT):
        # Check if user is the owner
        doc_record = db.query(Document).filter(Document.id == doc_id).first()
        
        if not doc_record or doc_record.owner_id != current_user.id.__int__():
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to delete this document"
            )
    
    # Delete the document from the vector store
    service.delete(doc_id)
    
    # Delete the document record
    doc_record = db.query(Document).filter(Document.id == doc_id).first()
    if doc_record:
        db.delete(doc_record)
        db.commit()
    
    return DeleteResponse(message="Document deleted successfully")

class DocumentInfo(BaseModel):
    """Document information response model."""
    id: str
    filename: str
    is_public: bool
    created_at: str
    updated_at: str

class DocumentVisibilityUpdate(BaseModel):
    """Document visibility update response model."""
    message: str
    doc_id: str
    is_public: bool

@enhanced_ingest_router.get("/ingest/my-documents", tags=["Enhanced Ingestion"])
def get_my_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[DocumentInfo]:
    """Get documents owned by the current user."""
    from private_gpt.server.auth.models import Document
    
    # Get user's owned documents
    owned_docs = db.query(Document).filter(
        Document.owner_id == current_user.id.__int__()
    ).all()
    
    return [
        DocumentInfo(
            id=str(doc.id),
            filename=str(doc.filename),
            is_public=bool(doc.is_public),
            created_at=doc.created_at.isoformat(),
            updated_at=doc.updated_at.isoformat()
        )
        for doc in owned_docs
    ]

@enhanced_ingest_router.put("/ingest/{doc_id}/visibility", tags=["Enhanced Ingestion"])
def update_document_visibility(
    doc_id: str,
    is_public: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DocumentVisibilityUpdate:
    """Update document visibility (public/private).
    
    Only the document owner can change visibility settings.
    """
    from private_gpt.server.auth.models import Document
    
    # Get the document record
    doc_record = db.query(Document).filter(Document.id == doc_id).first()
    
    if not doc_record:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if user is the owner
    if doc_record.owner_id != current_user.id.__int__():
        raise HTTPException(
            status_code=403,
            detail="Only document owners can change visibility settings"
        )
    
    # Update visibility using SQLAlchemy update
    db.query(Document).filter(Document.id == doc_id).update({"is_public": is_public})
    db.commit()
    
    return DocumentVisibilityUpdate(
        message="Document visibility updated successfully",
        doc_id=doc_id,
        is_public=is_public
    )
