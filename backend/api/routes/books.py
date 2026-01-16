"""Book details API endpoints"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from loguru import logger
import os

from models.schemas import BookDetailResponse
from api.dependencies import get_postgres_db, get_current_user_optional
from services.sqlite_helper import sqlite_book_service
from services.cover_fetch_service import CoverFetchService

router = APIRouter(prefix="/books", tags=["Books"])


def transform_book_to_detail_response(
    book_data: dict,
    cover_url: Optional[str] = None,
    user_context: Optional[dict] = None
) -> BookDetailResponse:
    """
    Transform book data from SQLite into BookDetailResponse.
    
    Data transformations:
    - authors (DB) → author (first), authors (full)
    - category (DB) → genres (parsed array)
    - Add user context if authenticated
    """
    # Parse first author for display
    authors_list = book_data['authors'].split(',')
    first_author = authors_list[0].strip() if authors_list else book_data['authors']
    
    # Parse genres from category
    category = book_data['category']
    if category:
        genres = [g.strip() for g in category.replace(';', ',').split(',') if g.strip()]
    else:
        genres = []
    
    # Build response
    response = BookDetailResponse(
        book_id=book_data['book_id'],
        title=book_data['title'],
        author=first_author,
        authors=book_data['authors'],
        category=category,
        genres=genres,
        description=book_data['description'],
        publish_year=book_data.get('publish_year'),
        publish_month=book_data.get('publish_month'),
        cover_url=cover_url,
        source_link=None  # Always None for compatibility
    )
    
    # Add user context if available
    if user_context:
        response.in_library = user_context.get('in_library', False)
        response.added_at = user_context.get('added_at')
        response.rating = user_context.get('rating')
        response.review = user_context.get('review_text')
    
    return response


@router.get("/{book_id}", response_model=BookDetailResponse)
async def get_book_details(
    book_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db = Depends(get_postgres_db)
):
    """
    Get detailed information about a book.
    
    This endpoint works both with and without authentication:
    - If authenticated: includes library status, rating, review
    - If not authenticated: returns only book data
    
    Path parameters:
        book_id: Book ID
    
    Returns:
        Detailed book information with cover image
    """
    
    # Get book from SQLite
    book = sqlite_book_service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )
    
    try:
        # Get cover URL (from cache or fetch)
        cover_service = CoverFetchService(
            postgres_db=db,
            api_key=os.getenv('GOOGLE_BOOKS_API_KEY')
        )
        
        cover_url = await cover_service.get_cover_url(
            book_id=book_id,
            title=book['title'],
            author=book['authors'].split(',')[0].strip()
        )
        
        # Get user context if authenticated
        user_context = None
        if current_user:
            user_id = current_user['id']
            
            # Check if in library
            in_library = await db.is_in_library(user_id, book_id)
            
            if in_library:
                # Get library entry with review
                library_entries = await db.get_library_with_details(
                    user_id=user_id,
                    sort='added_at',
                    rated_only=False
                )
                
                # Find this book
                for entry in library_entries:
                    if entry['book_id'] == book_id:
                        user_context = {
                            'in_library': True,
                            'added_at': entry['added_at'],
                            'rating': entry.get('rating'),
                            'review_text': entry.get('review_text')
                        }
                        break
        
        # Transform to response
        return transform_book_to_detail_response(
            book_data=book,
            cover_url=cover_url,
            user_context=user_context
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching book details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch book details"
        )
