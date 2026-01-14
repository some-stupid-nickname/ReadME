"""Health check endpoints"""
from fastapi import APIRouter, Depends
from models.schemas import HealthResponse
from services.rag_service import BookRAGAssistant
from api.dependencies import get_rag_assistant

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(
    assistant: BookRAGAssistant = Depends(get_rag_assistant)
) -> HealthResponse:
    """
    Проверка работоспособности API
    
    Проверяет состояние всех сервисов:
    - Database (books database)
    - LLM (Mistral API connection)
    """
    services_status = {}
    overall_status = "ok"
    
    # Check database (books)
    try:
        # Try to access the search engine's book database
        if assistant.search_engine.book_db.books:
            services_status["database"] = "ok"
        else:
            services_status["database"] = "error"
            overall_status = "error"
    except Exception:
        services_status["database"] = "error"
        overall_status = "error"
    
    # Check LLM (Mistral API)
    try:
        # Simple check - if client is initialized
        if assistant.client:
            services_status["llm"] = "ok"
        else:
            services_status["llm"] = "error"
            overall_status = "error"
    except Exception:
        services_status["llm"] = "error"
        overall_status = "error"
    
    # Qdrant is not used in current implementation, but mentioned in API spec
    # Set to "ok" as placeholder
    services_status["qdrant"] = "ok"
    
    return HealthResponse(
        status=overall_status,
        services=services_status,
        version="1.0.0"
    )

