"""Search endpoints for book recommendations"""
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import SearchRequest, SearchResponse, BookInfo
from services.rag_service import BookRAGAssistant
from api.dependencies import get_rag_assistant
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

