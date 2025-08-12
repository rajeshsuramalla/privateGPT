"""API endpoints for the custom HTML UI."""

import logging
from pathlib import Path
from typing import Any, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from injector import inject, singleton
from llama_index.core.llms import ChatMessage, MessageRole
from pydantic import BaseModel

from private_gpt.open_ai.extensions.context_filter import ContextFilter
from private_gpt.server.chat.chat_service import ChatService
from private_gpt.server.chunks.chunks_service import ChunksService
from private_gpt.server.ingest.ingest_service import IngestService
from private_gpt.server.recipes.summarize.summarize_service import SummarizeService
from private_gpt.settings.settings import settings

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    mode: str = "rag"
    selected_files: List[str] = []
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[dict] = []


class FileInfo(BaseModel):
    name: str
    size: int
    type: str


class ModelInfo(BaseModel):
    llm_mode: str
    model_name: Optional[str]
    embedding_mode: str


@singleton
class HtmlUiApiRouter:
    @inject
    def __init__(
        self,
        chat_service: ChatService,
        chunks_service: ChunksService,
        ingest_service: IngestService,
        summarize_service: SummarizeService,
    ) -> None:
        self._chat_service = chat_service
        self._chunks_service = chunks_service
        self._ingest_service = ingest_service
        self._summarize_service = summarize_service
        self.router = APIRouter(prefix="/api/html-ui", tags=["HTML UI"])
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup all API routes for the HTML UI."""
        
        @self.router.post("/chat", response_model=ChatResponse)
        async def chat(chat_request: ChatRequest) -> ChatResponse:
            """Handle chat requests from the HTML UI."""
            try:
                logger.info(f"Chat request: mode={chat_request.mode}, message length={len(chat_request.message)}")
                
                # Build context filter for selected files
                context_filter = None
                if chat_request.selected_files and chat_request.mode in ["rag", "summarize"]:
                    docs_ids = []
                    for ingested_document in self._ingest_service.list_ingested():
                        if (
                            ingested_document.doc_metadata
                            and ingested_document.doc_metadata["file_name"] in chat_request.selected_files
                        ):
                            docs_ids.append(ingested_document.doc_id)
                    if docs_ids:
                        context_filter = ContextFilter(docs_ids=docs_ids)

                # Handle different modes
                if chat_request.mode == "rag":
                    # RAG mode - get contextualized answers
                    completion = self._chat_service.chat(
                        messages=[ChatMessage(content=chat_request.message, role=MessageRole.USER)],
                        use_context=True,
                        context_filter=context_filter,
                    )
                    
                    # Extract sources
                    sources = []
                    if completion.sources:
                        sources = [
                            {
                                "file": chunk.document.doc_metadata.get("file_name", "Unknown") if chunk.document.doc_metadata else "Unknown",
                                "page": chunk.document.doc_metadata.get("page_label", "-") if chunk.document.doc_metadata else "-",
                                "text": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                            }
                            for chunk in completion.sources
                        ]
                    
                    return ChatResponse(response=completion.response, sources=sources)
                
                elif chat_request.mode == "search":
                    # Search mode - find relevant chunks
                    chunks = self._chunks_service.retrieve_relevant(
                        text=chat_request.message,
                        limit=4,
                        prev_next_chunks=0
                    )
                    
                    search_results = []
                    for i, chunk in enumerate(chunks, 1):
                        file_name = chunk.document.doc_metadata.get("file_name", "Unknown") if chunk.document.doc_metadata else "Unknown"
                        page_label = chunk.document.doc_metadata.get("page_label", "-") if chunk.document.doc_metadata else "-"
                        search_results.append(f"{i}. **{file_name} (page {page_label})**\n{chunk.text}")
                    
                    response_text = "\n\n".join(search_results) if search_results else "No relevant content found."
                    return ChatResponse(response=response_text)
                
                elif chat_request.mode == "chat":
                    # Basic chat mode - no context
                    completion = self._chat_service.chat(
                        messages=[ChatMessage(content=chat_request.message, role=MessageRole.USER)],
                        use_context=False,
                    )
                    
                    return ChatResponse(response=completion.response)
                
                elif chat_request.mode == "summarize":
                    # Summarize mode
                    summary_gen = self._summarize_service.stream_summarize(
                        use_context=True,
                        context_filter=context_filter,
                        instructions=chat_request.message,
                    )
                    
                    full_response = ""
                    for token in summary_gen:
                        full_response += str(token)
                    
                    return ChatResponse(response=full_response)
                
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown mode: {chat_request.mode}")
                    
            except Exception as e:
                logger.error(f"Chat error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/upload")
        async def upload_files(files: List[UploadFile] = File(...)) -> JSONResponse:
            """Handle file uploads from the HTML UI."""
            try:
                uploaded_files = []
                
                for file in files:
                    if not file.filename:
                        continue  # Skip files without names
                        
                    # Save the uploaded file temporarily
                    temp_path = Path(f"/tmp/{file.filename}")
                    temp_path.parent.mkdir(exist_ok=True)
                    
                    with open(temp_path, "wb") as f:
                        content = await file.read()
                        f.write(content)
                    
                    # Ingest the file
                    self._ingest_service.bulk_ingest([(file.filename, temp_path)])
                    
                    uploaded_files.append({
                        "name": file.filename,
                        "size": len(content),
                        "type": file.content_type or "unknown"
                    })
                    
                    # Clean up temp file
                    temp_path.unlink(missing_ok=True)
                
                logger.info(f"Successfully uploaded {len(uploaded_files)} files")
                return JSONResponse({"files": uploaded_files, "message": "Files uploaded successfully"})
                
            except Exception as e:
                logger.error(f"Upload error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/files")
        async def list_files() -> JSONResponse:
            """Get list of ingested files."""
            try:
                files = []
                for ingested_document in self._ingest_service.list_ingested():
                    if ingested_document.doc_metadata:
                        file_name = ingested_document.doc_metadata.get("file_name", "Unknown")
                        if file_name not in [f["name"] for f in files]:  # Avoid duplicates
                            files.append({
                                "name": file_name,
                                "id": ingested_document.doc_id,
                                "type": "document"
                            })
                
                return JSONResponse({"files": files})
                
            except Exception as e:
                logger.error(f"List files error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.delete("/files/{file_name}")
        async def delete_file(file_name: str) -> JSONResponse:
            """Delete a specific file."""
            try:
                deleted_count = 0
                for ingested_document in self._ingest_service.list_ingested():
                    if (
                        ingested_document.doc_metadata
                        and ingested_document.doc_metadata["file_name"] == file_name
                    ):
                        self._ingest_service.delete(ingested_document.doc_id)
                        deleted_count += 1
                
                if deleted_count > 0:
                    logger.info(f"Deleted {deleted_count} document(s) for file: {file_name}")
                    return JSONResponse({"message": f"File '{file_name}' deleted successfully"})
                else:
                    raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Delete file error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/model-info")
        async def get_model_info() -> ModelInfo:
            """Get current model information."""
            try:
                config_settings = settings()
                llm_mode = config_settings.llm.mode
                embedding_mode = config_settings.embedding.mode
                
                # Get model name based on mode
                model_name = None
                model_mapping = {
                    "llamacpp": getattr(config_settings.llamacpp, 'llm_hf_model_file', None),
                    "openai": getattr(config_settings.openai, 'model', None),
                    "ollama": getattr(config_settings.ollama, 'llm_model', None),
                    "mock": "Mock Model",
                }
                
                model_name = model_mapping.get(llm_mode, llm_mode)
                
                return ModelInfo(
                    llm_mode=llm_mode,
                    model_name=model_name,
                    embedding_mode=embedding_mode
                )
                
            except Exception as e:
                logger.error(f"Model info error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
