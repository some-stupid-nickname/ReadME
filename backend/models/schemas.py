"""Pydantic schemas for API requests and responses"""
from typing import List, Optional
from datetime import datetime
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
    cover_url: Optional[str] = Field(None, description="Book cover image URL")
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


# ============================================================
# NEW MODELS - Authentication and User Management
# ============================================================

class UserRegister(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """User login request"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user_id: int


class UserProfile(BaseModel):
    """User profile information"""
    user_id: int
    username: str
    onboarding_completed: bool
    library_count: int = 0


# ============================================================
# NEW MODELS - Onboarding
# ============================================================

class OnboardingBook(BaseModel):
    """Onboarding book selection"""
    book_id: str
    title: str
    author: str
    category: str
    cover_url: Optional[str] = None


class OnboardingComplete(BaseModel):
    """Onboarding completion request"""
    selected_book_ids: List[str] = Field(..., min_length=3, max_length=10)


# ============================================================
# NEW MODELS - Extended Book Information
# ============================================================

class BookDetailResponse(BaseModel):
    """Extended book info with additional fields - for new endpoints only"""
    book_id: str
    id: str  # Alias for book_id to match BookInfo schema (for frontend compatibility)
    title: str
    author: str  # First author for display
    authors: str  # Full comma-separated list from DB
    category: str  # Raw category from DB
    genres: List[str]  # Parsed array from category
    description: str
    publish_year: Optional[int] = None
    publish_month: Optional[int] = None
    cover_url: Optional[str] = None
    source_link: Optional[str] = None  # Compatibility field, always None
    
    # Library context (populated if user has this book)
    in_library: bool = False
    added_at: Optional[datetime] = None
    rating: Optional[int] = None
    review: Optional[str] = None


# ============================================================
# NEW MODELS - Library Management
# ============================================================

class LibraryAddRequest(BaseModel):
    """Request to add book to library"""
    source_query: Optional[str] = None


class LibraryResponse(BaseModel):
    """Response for library operations"""
    books: List[BookDetailResponse]


# ============================================================
# NEW MODELS - Reviews
# ============================================================

class ReviewRequest(BaseModel):
    """Review creation/update request"""
    book_id: str
    rating: int = Field(..., ge=1, le=10)
    review_text: Optional[str] = Field(None, max_length=2000)


class ReviewResponse(BaseModel):
    """Review information"""
    book_id: str
    rating: int
    review_text: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================
# NEW MODELS - Personalized Search
# ============================================================

class PersonalizedSearchResponse(SearchResponse):
    """Extends SearchResponse with personalization metadata"""
    personalization_applied: bool = False
    similarity_score: Optional[float] = None
    context_books: Optional[List[str]] = None  # Titles of books used for context


# ============================================================
# NEW MODELS - Admin Metrics
# ============================================================

class MetricsResponse(BaseModel):
    """Admin metrics response"""
    total_users: int
    active_users_7d: int
    total_queries_all_time: int
    total_queries_today: int
    total_queries_week: int
    primary_acceptance_rate: float  # (books liked / books returned) * 100
    final_acceptance_rate: float  # (books rated >=7 / books in libraries) * 100
    avg_library_size: float
    avg_rating: float
    median_rating: float
