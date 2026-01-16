"""FastAPI dependencies for RAG components and authentication"""
from functools import lru_cache
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.rag_service import BookRAGAssistant
from services.search_service import VectorSearchEngine
from services.database_service import BookDatabase
from services.query_enrichment_service import QueryEnrichmentService
from database.postgres_service import postgres_db
from core.config import settings, get_books_db_path
from core.security import decode_access_token

# HTTP Bearer token security scheme
security = HTTPBearer()


@lru_cache()
def get_rag_assistant() -> BookRAGAssistant:
    """
    Get or create RAG assistant instance (singleton pattern)
    This function is cached, so the same instance is reused across requests
    """
    db_path = get_books_db_path()
    book_db = BookDatabase(db_path)
    search_engine = VectorSearchEngine(book_db)
    return BookRAGAssistant(
        search_engine=search_engine,
        api_key=settings.mistral_api_key
    )


@lru_cache()
def get_query_enrichment_service() -> QueryEnrichmentService:
    """
    Get or create query enrichment service instance (singleton pattern)
    This function is cached, so the same instance is reused across requests
    """
    return QueryEnrichmentService(api_key=settings.mistral_api_key)


# ============================================================
# NEW DEPENDENCIES - Authentication and Database
# ============================================================

def get_postgres_db():
    """
    Get PostgreSQL database instance.
    This is the global instance, already connected on app startup.
    """
    return postgres_db


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_postgres_db)
) -> dict:
    """
    Get current authenticated user from JWT token.
    
    Raises:
        HTTPException 401: If token is invalid or user not found
        
    Returns:
        User dict with id, username, etc.
    """
    token = credentials.credentials
    
    # Decode JWT token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from token
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db = Depends(get_postgres_db)
) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.
    Used for endpoints that work both with and without auth.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
