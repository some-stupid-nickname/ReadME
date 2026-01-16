"""Onboarding API endpoints"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from loguru import logger

from models.schemas import OnboardingBook, OnboardingComplete
from api.dependencies import get_postgres_db, get_current_user

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get("/books", response_model=List[OnboardingBook])
async def get_onboarding_books(
    db = Depends(get_postgres_db)
):
    """
    Get curated list of books for onboarding.
    
    Returns 16 books across 4 categories:
    - Classic (4 books)
    - Fantasy (4 books)
    - Thriller (4 books)
    - Modern (4 books)
    
    Note: This endpoint does not require authentication
    """
    try:
        books = await db.get_onboarding_books()
        
        result = []
        for book in books:
            # Get cover URL if cached
            cover_url = await db.get_cover_url(book['book_id'])
            
            result.append(OnboardingBook(
                book_id=book['book_id'],
                title=book['title'],
                author=book['author'],
                category=book['category'],
                cover_url=cover_url
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error fetching onboarding books: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch onboarding books"
        )


@router.post("/complete", status_code=status.HTTP_200_OK)
async def complete_onboarding(
    completion_data: OnboardingComplete,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_postgres_db)
):
    """
    Complete user onboarding by selecting 3-10 books.
    
    Requires:
        Authorization: Bearer <token>
    
    Body:
        selected_book_ids: List of 3-10 book IDs
    
    Actions:
        1. Add books to user's library with source='onboarding'
        2. Mark user.onboarding_completed = true
        3. Flag preference vector for recalculation
    
    Returns:
        Success status and library count
    """
    user_id = current_user['id']
    selected_ids = completion_data.selected_book_ids
    
    # Validate selection count
    if not (3 <= len(selected_ids) <= 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must select between 3 and 10 books"
        )
    
    # Get valid onboarding book IDs
    valid_books = await db.get_onboarding_books()
    valid_ids = {book['book_id'] for book in valid_books}
    
    # Validate that all selected IDs are valid
    invalid_ids = [bid for bid in selected_ids if bid not in valid_ids]
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid book IDs: {invalid_ids}"
        )
    
    try:
        # Add books to library
        for book_id in selected_ids:
            await db.add_to_library(
                user_id=user_id,
                book_id=book_id,
                source='onboarding',
                source_query=None
            )
        
        # Mark onboarding as completed
        await db.complete_onboarding(user_id)
        
        # Get updated library count
        library_count = await db.get_library_count(user_id)
        
        logger.info(f"User {user_id} completed onboarding with {len(selected_ids)} books")
        
        return {
            "success": True,
            "library_count": library_count
        }
    
    except Exception as e:
        logger.error(f"Error completing onboarding for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete onboarding"
        )
