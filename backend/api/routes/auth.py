"""Authentication API endpoints"""
from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger
import re

from models.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserProfile
)
from core.security import verify_password, get_password_hash, create_access_token
from api.dependencies import get_postgres_db, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def validate_username(username: str) -> bool:
    """
    Validate username format.
    Requirements: 3-50 chars, alphanumeric + underscore only
    """
    if not (3 <= len(username) <= 50):
        return False
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False
    return True


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db = Depends(get_postgres_db)
):
    """
    Register a new user.
    
    Requirements:
    - Username: 3-50 chars, alphanumeric + underscore
    - Password: min 6 chars
    
    Returns:
        JWT access token and user_id
    """
    # Validate username format
    if not validate_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be 3-50 characters, alphanumeric and underscore only"
        )
    
    # Check if username already exists
    existing_user = await db.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash password
    password_hash = get_password_hash(user_data.password)
    
    # Create user
    try:
        user_id = await db.create_user(user_data.username, password_hash)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user_id})
    
    logger.info(f"User registered: {user_data.username} (id={user_id})")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db = Depends(get_postgres_db)
):
    """
    Login with username and password.
    
    Returns:
        JWT access token and user_id
    """
    # Get user by username
    user = await db.get_user_by_username(credentials.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login timestamp
    await db.update_last_login(user['id'])
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user['id']})
    
    logger.info(f"User logged in: {credentials.username} (id={user['id']})")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user['id']
    )


@router.get("/me", response_model=UserProfile)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_postgres_db)
):
    """
    Get current user's profile.
    
    Requires:
        Authorization: Bearer <token>
    
    Returns:
        User profile information
    """
    # Get library count
    library_count = await db.get_library_count(current_user['id'])
    
    return UserProfile(
        user_id=current_user['id'],
        username=current_user['username'],
        onboarding_completed=current_user['onboarding_completed'],
        library_count=library_count
    )
