"""Search endpoints for book recommendations"""
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import (
    SearchRequest, SearchResponse, BookInfo,
    ClarificationRequest, ClarificationResponse,
    EnrichedSearchRequest, PersonalizedSearchResponse
)
from services.rag_service import BookRAGAssistant
from services.query_enrichment_service import QueryEnrichmentService
from services.personalized_search_service import PersonalizedSearchService
from services.sqlite_helper import sqlite_book_service
from api.dependencies import get_rag_assistant, get_query_enrichment_service, get_postgres_db, get_current_user
from models.book import Book

router = APIRouter(prefix="/api/search", tags=["search"])


def book_to_book_info(book: Book, score: float) -> BookInfo:
    """Convert Book model to BookInfo schema"""
    # Extract category as genres list
    genres = []
    if book.category:
        # Split category by common delimiters if needed
        category_clean = book.category.strip()
        if category_clean and category_clean != "Unknown":
            genres = [category_clean]

    return BookInfo(
        id=f"book_{book.id}",
        title=book.title,
        author=book.authors,
        genres=genres,
        description=book.description,
        source_link=None  # Not available in current data
    )


@router.post("", response_model=SearchResponse, status_code=200)
async def search_books(
    request: SearchRequest,
    assistant: BookRAGAssistant = Depends(get_rag_assistant)
) -> SearchResponse:
    """
    Анонимный поиск книг (БЕЗ сохранения в историю)

    - **query**: Поисковый запрос пользователя
    """
    # Validate query
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    try:
        # Get RAG response and search results
        response_text, search_results = assistant.ask(
            user_query=request.query.strip(),
            top_k=10
        )

        # Convert books to API format
        books = [
            book_to_book_info(book, score)
            for book, score in search_results
        ]

        return SearchResponse(
            response=response_text,
            books=books,
            message_id=None  # Anonymous search, no message ID
        )

    except Exception as e:
        # Log error in production
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/clarify", response_model=ClarificationResponse, status_code=200)
async def clarify_query(
    request: ClarificationRequest,
    enrichment_service: QueryEnrichmentService = Depends(get_query_enrichment_service)
) -> ClarificationResponse:
    """
    Analyze if a query is too vague and generate clarifying questions

    - **query**: User's search query to analyze

    Returns:
    - **is_vague**: Whether the query needs clarification
    - **clarifying_questions**: Questions to ask (if vague)
    - **original_query**: Original query from user
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    try:
        query = request.query.strip()

        # Check if query is vague
        is_vague = enrichment_service.is_query_vague(query)

        # Generate clarifying questions if vague
        clarifying_questions = None
        if is_vague:
            clarifying_questions = enrichment_service.generate_clarifying_questions(query)

        return ClarificationResponse(
            is_vague=is_vague,
            clarifying_questions=clarifying_questions,
            original_query=query
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/enriched", response_model=SearchResponse, status_code=200)
async def enriched_search(
    request: EnrichedSearchRequest,
    assistant: BookRAGAssistant = Depends(get_rag_assistant),
    enrichment_service: QueryEnrichmentService = Depends(get_query_enrichment_service)
) -> SearchResponse:
    """
    Search with enriched query (original query + user's additional context)

    - **original_query**: User's original query
    - **user_context**: Additional context provided by user

    Returns enriched search results
    """
    if not request.original_query or not request.original_query.strip():
        raise HTTPException(
            status_code=400,
            detail="Original query cannot be empty"
        )

    if not request.user_context or not request.user_context.strip():
        raise HTTPException(
            status_code=400,
            detail="User context cannot be empty"
        )

    try:
        # Enrich query with user context
        enriched_query = enrichment_service.enrich_query_with_context(
            original_query=request.original_query.strip(),
            user_context=request.user_context.strip()
        )

        # Get RAG response with enriched query
        response_text, search_results = assistant.ask(
            user_query=enriched_query,
            top_k=10
        )

        # Convert books to API format
        books = [
            book_to_book_info(book, score)
            for book, score in search_results
        ]

        return SearchResponse(
            response=response_text,
            books=books,
            message_id=None
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# ============================================================
# NEW ENDPOINT - Personalized Search
# ============================================================

@router.post("/personalized", response_model=PersonalizedSearchResponse, status_code=200)
async def personalized_search(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user),
    assistant: BookRAGAssistant = Depends(get_rag_assistant),
    db = Depends(get_postgres_db)
) -> PersonalizedSearchResponse:
    """
    Personalized book search using user's reading history.
    
    This endpoint wraps the existing RAG assistant with personalization layer:
    1. Analyzes user's library and ratings
    2. Computes similarity between query and user preferences
    3. If similar enough, enhances query with context from user's favorite books
    4. Calls standard RAG assistant (unchanged)
    5. Filters out books already in user's library
    6. Logs recommendation for metrics
    
    Requires authentication: Authorization: Bearer <token>
    
    Args:
        query: Search query
    
    Returns:
        Search results with personalization metadata
    """
    # Validate query
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )
    
    try:
        # Create personalized search service (wraps existing RAG)
        personalized_service = PersonalizedSearchService(
            rag_assistant=assistant,
            postgres_db=db,
            sqlite_db=sqlite_book_service
        )
        
        # Perform personalized search
        result = await personalized_service.search(
            user_id=current_user['id'],
            query=request.query.strip()
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
