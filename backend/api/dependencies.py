"""FastAPI dependencies for RAG components"""
from functools import lru_cache
from services.rag_service import BookRAGAssistant
from services.search_service import VectorSearchEngine
from services.database_service import BookDatabase
from core.config import settings, get_books_db_path


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

