"""Review management API endpoints"""
from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger

from models.schemas import ReviewRequest, ReviewResponse
from api.dependencies import get_postgres_db, get_current_user
from services.sqlite_helper import sqlite_book_service

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_review(
    review_data: ReviewRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_postgres_db)
):
    """
    Create or update a book review.
    
    Body:
        book_id: Book ID
        rating: Rating 1-10
        review_text: Optional review text (max 2000 chars)
    
    Returns:
        Created/updated review
    """
    user_id = current_user['id']
    
    # Validate that book exists
    book = sqlite_book_service.get_book_by_id(review_data.book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {review_data.book_id} not found"
        )
    
    # Validate rating range
    if not (1 <= review_data.rating <= 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 10"
        )
    
    try:
        # Upsert review
        review = await db.upsert_review(
            user_id=user_id,
            book_id=review_data.book_id,
            rating=review_data.rating,
            review_text=review_data.review_text
        )
        
        logger.info(f"User {user_id} reviewed book {review_data.book_id} with rating {review_data.rating}")
        
        return ReviewResponse(
            book_id=review['book_id'],
            rating=review['rating'],
            review_text=review['review_text'],
            created_at=review['created_at'],
            updated_at=review['updated_at']
        )
    
    except Exception as e:
        logger.error(f"Error creating/updating review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save review"
        )


@router.get("/{book_id}", response_model=ReviewResponse)
async def get_review(
    book_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_postgres_db)
):
    """
    Get user's review for a specific book.
    
    Path parameters:
        book_id: Book ID
    
    Returns:
        Review or 404 if not found
    """
    user_id = current_user['id']
    
    review = await db.get_review(user_id, book_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return ReviewResponse(
        book_id=review['book_id'],
        rating=review['rating'],
        review_text=review['review_text'],
        created_at=review['created_at'],
        updated_at=review['updated_at']
    )


@router.put("/{book_id}", response_model=ReviewResponse)
async def update_review(
    book_id: str,
    review_data: ReviewRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_postgres_db)
):
    """
    Update existing review.
    
    Path parameters:
        book_id: Book ID
    
    Body:
        rating: Updated rating 1-10
        review_text: Updated review text
    
    Returns:
        Updated review
    """
    user_id = current_user['id']
    
    # Check if review exists
    existing_review = await db.get_review(user_id, book_id)
    if not existing_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found. Use POST to create a new review."
        )
    
    # Validate rating
    if not (1 <= review_data.rating <= 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 10"
        )
    
    try:
        # Update review (upsert handles this)
        review = await db.upsert_review(
            user_id=user_id,
            book_id=book_id,
            rating=review_data.rating,
            review_text=review_data.review_text
        )
        
        logger.info(f"User {user_id} updated review for book {book_id}")
        
        return ReviewResponse(
            book_id=review['book_id'],
            rating=review['rating'],
            review_text=review['review_text'],
            created_at=review['created_at'],
            updated_at=review['updated_at']
        )
    
    except Exception as e:
        logger.error(f"Error updating review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review"
        )


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    book_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_postgres_db)
):
    """
    Delete review for a book.
    Book remains in library.
    
    Path parameters:
        book_id: Book ID
    """
    user_id = current_user['id']
    
    try:
        await db.delete_review(user_id, book_id)
        logger.info(f"User {user_id} deleted review for book {book_id}")
        return None  # 204 No Content
    
    except Exception as e:
        logger.error(f"Error deleting review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete review"
        )
