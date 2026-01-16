"""Pydantic schemas for API requests and responses"""
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request schema for book search"""
    query: str = Field(..., min_length=1, description="Search query")


class ClarificationRequest(BaseModel):
    """Request schema for query clarification check"""
    query: str = Field(..., min_length=1, description="User's search query to analyze")


class ClarificationResponse(BaseModel):
    """Response schema for query clarification"""
    is_vague: bool = Field(..., description="Whether the query needs clarification")
    clarifying_questions: Optional[str] = Field(None, description="Questions to ask user (if vague)")
    original_query: str = Field(..., description="Original query from user")


class EnrichedSearchRequest(BaseModel):
    """Request schema for enriched book search"""
    original_query: str = Field(..., min_length=1, description="User's original query")
    user_context: str = Field(..., min_length=1, description="Additional context from user")


class BookInfo(BaseModel):
    """Book information for API response"""
    id: str = Field(..., description="Book ID")
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author(s)")
    genres: List[str] = Field(default_factory=list, description="Book genres/categories")
    description: Optional[str] = Field(None, description="Book description")
    source_link: Optional[str] = Field(None, description="Source link for the book")


class SearchResponse(BaseModel):
    """Response schema for book search"""
    response: str = Field(..., description="Assistant's response with recommendations")
    books: List[BookInfo] = Field(default_factory=list, description="List of found books")
    message_id: Optional[int] = Field(None, description="Message ID (null for anonymous searches)")


class ServiceStatus(BaseModel):
    """Status of a service"""
    status: str = Field(..., description="Service status: 'ok' or 'error'")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall API status")
    services: dict[str, str] = Field(..., description="Status of individual services")
    version: str = Field(default="1.0.0", description="API version")


# Placeholder schemas for future features
class User(BaseModel):
    """User schema (for future authentication)"""
    id: int
    username: str
    created_at: str


class Chat(BaseModel):
    """Chat schema (for future chat history)"""
    id: int
    title: str
    created_at: str
    updated_at: str
    messages_count: int


class Message(BaseModel):
    """Message schema (for future chat messages)"""
    id: int
    role: str
    content: str
    created_at: str
    feedback: Optional[str] = None
