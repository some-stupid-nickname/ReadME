"""Library management API endpoints"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from loguru import logger

from models.schemas import BookDetailResponse, LibraryAddRequest, LibraryResponse
from api.dependencies import get_postgres_db, get_current_user
from services.sqlite_helper import sqlite_book_service

router = APIRouter(prefix="/library", tags=["Library"])


def transform_book_to_detail_response(
    book_data: dict,
    library_data: Optional[dict] = None,
    cover_url: Optional[str] = None
) -> BookDetailResponse:
    """
    Transform book data from SQLite + PostgreSQL into BookDetailResponse.
    
    Data transformations:
    - authors (DB) → author (first), authors (full)
    - category (DB) → genres (parsed array)
    - Add library context if available
    """
    # Parse first author for display
    authors_list = book_data['authors'].split(',')
    first_author = authors_list[0].strip() if authors_list else book_data['authors']
    
    # Parse genres from category (split by comma or semicolon)
    category = book_data['category']
    if category:
        genres = [g.strip() for g in category.replace(';', ',').split(',') if g.strip()]
    else:
        genres = []
    
    # Build response
    book_id = str(book_data['book_id'])
    response = BookDetailResponse(
        book_id=book_id,
        id=book_id,  # Add id field for frontend compatibility
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
    
    # Add library context if available
    if library_data:
        response.in_library = True
        response.added_at = library_data.get('added_at')
        response.rating = library_data.get('rating')
        response.review = library_data.get('review_text')
    
    return response


@router.get("", response_model=LibraryResponse)
async def get_library(
    sort: str = Query('added_at', pattern='^(added_at|rating|alphabetical)$'),
    rated_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_postgres_db)
):
    """
    Get user's library with book details.
    
    Query parameters:
    - sort: 'added_at' (default), 'rating', 'alphabetical'
    - rated_only: if true, only return books with ratings
    
    Returns:
        List of books with details, reviews, and cover images
    """
    user_id = current_user['id']
    
    try:
        # Get library entries with reviews (excluding onboarding books by default)
        library_entries = await db.get_library_with_details(
            user_id=user_id,
            sort=sort,
            rated_only=rated_only,
            exclude_onboarding=True
        )
        
        logger.info(f"User {user_id} library: found {len(library_entries)} entries (sort={sort}, rated_only={rated_only})")
        
        if not library_entries:
            return LibraryResponse(books=[])
        
        # Get book IDs
        book_ids = [entry['book_id'] for entry in library_entries]
        
        # Fetch book details from SQLite
        books_data = sqlite_book_service.get_books_by_ids(book_ids)
        books_by_id = {book['book_id']: book for book in books_data}
        
        logger.debug(f"Fetched {len(books_data)} books from SQLite for user {user_id}")
        
        # Combine data
        result_books = []
        for entry in library_entries:
            book_id = entry['book_id']
            
            # Skip if book not found in SQLite (shouldn't happen)
            if book_id not in books_by_id:
                logger.warning(f"Book {book_id} in library but not in SQLite")
                continue
            
            # Get cover URL
            cover_url = await db.get_cover_url(book_id)
            
            # Transform to response
            book_response = transform_book_to_detail_response(
                book_data=books_by_id[book_id],
                library_data=entry,
                cover_url=cover_url
            )
            
            result_books.append(book_response)
        
        logger.info(f"Returning {len(result_books)} books to user {user_id}")
        return LibraryResponse(books=result_books)
    
    except Exception as e:
        logger.error(f"Error fetching library for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch library"
        )


@router.post("/{book_id}", status_code=status.HTTP_201_CREATED)
async def add_to_library(
    book_id: str,
    request: LibraryAddRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_postgres_db)
):
    """
    Add book to user's library.
    
    Path parameters:
        book_id: ID of book to add
    
    Body:
        source_query: Optional query that led to this book
    
    Returns:
        Success message
    """
    user_id = current_user['id']
    
    # Validate that book exists in SQLite
    book = sqlite_book_service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )
    
    # Check if already in library
    already_in_library = await db.is_in_library(user_id, book_id)
    
    if already_in_library:
        return {
            "success": True,
            "message": "Book already in library",
            "status": "existing"
        }
    
    # Add to library
    try:
        await db.add_to_library(
            user_id=user_id,
            book_id=book_id,
            source='search',
            source_query=request.source_query
        )
        
        logger.info(f"User {user_id} added book {book_id} to library")
        
        return {
            "success": True,
            "message": "Book added to library",
            "status": "added"
        }
    
    except Exception as e:
        logger.error(f"Error adding book to library: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add book to library"
        )


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_library(
    book_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_postgres_db)
):
    """
    Remove book from user's library.
    Also removes associated review if exists.
    
    Path parameters:
        book_id: ID of book to remove
    """
    user_id = current_user['id']
    
    try:
        await db.remove_from_library(user_id, book_id)
        logger.info(f"User {user_id} removed book {book_id} from library")
        return None  # 204 No Content
    
    except Exception as e:
        logger.error(f"Error removing book from library: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove book from library"
        )
