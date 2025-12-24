"""Pydantic schemas for API requests and responses"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DocumentState(str, Enum):
    """Document processing state"""
    ACTIVE = "STATE_ACTIVE"
    PENDING = "STATE_PENDING"
    FAILED = "STATE_FAILED"


class FileSearchStoreCreate(BaseModel):
    """Request to create a new File Search Store"""
    display_name: str = Field(..., description="Display name for the store")


class FileSearchStoreResponse(BaseModel):
    """File Search Store information"""
    name: str
    display_name: str
    create_time: Optional[str] = None
    update_time: Optional[str] = None
    active_documents_count: int = 0
    pending_documents_count: int = 0
    failed_documents_count: int = 0
    size_bytes: int = 0


class CustomMetadata(BaseModel):
    """Custom metadata for documents"""
    key: str
    string_value: Optional[str] = None
    numeric_value: Optional[float] = None


class ChunkingConfig(BaseModel):
    """Chunking configuration for document processing"""
    chunk_size: int = Field(800, description="Size of each chunk")
    chunk_overlap: int = Field(400, description="Overlap between chunks")


class DocumentUploadRequest(BaseModel):
    """Request to upload a document"""
    display_name: str
    mime_type: str
    custom_metadata: Optional[List[CustomMetadata]] = None
    chunking_config: Optional[ChunkingConfig] = Field(
        default_factory=lambda: ChunkingConfig()
    )


class DocumentResponse(BaseModel):
    """Document information"""
    name: str
    display_name: str
    state: DocumentState
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    create_time: Optional[str] = None
    update_time: Optional[str] = None


class OperationResponse(BaseModel):
    """Long running operation response"""
    name: str
    done: bool
    metadata: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class Citation(BaseModel):
    """Citation from File Search results"""
    document_name: str
    chunk_id: str
    score: float
    text: str


class ChatMessage(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Role: 'user' or 'model'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request to send a chat message"""
    message: str = Field(..., description="User message")
    store_name: str = Field(..., description="File Search Store name")
    history: Optional[List[ChatMessage]] = Field(
        default_factory=list, description="Chat history"
    )
    document_names: Optional[List[str]] = Field(
        default_factory=list, description="Selected document names to search in"
    )


class ChatResponse(BaseModel):
    """Response from chat"""
    message: str
    citations: List[Citation] = Field(default_factory=list)


class ReportRequest(BaseModel):
    """Request to generate a report"""
    store_name: str
    chat_history: List[ChatMessage]
    report_type: str = Field(
        "comprehensive", description="Type of report to generate"
    )


class ReportResponse(BaseModel):
    """Generated report"""
    title: str
    content: str
    generated_at: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
