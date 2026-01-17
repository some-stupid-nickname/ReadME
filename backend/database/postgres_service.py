"""PostgreSQL database service for user data and personalization."""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from loguru import logger
from core.config import settings


class PostgresService:
    """
    Async PostgreSQL service using asyncpg.
    Handles all user-related data (auth, library, reviews, preferences, metrics).
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._connection_params = {
            'host': settings.postgres_host,
            'port': settings.postgres_port,
            'database': settings.postgres_db,
            'user': settings.postgres_user,
            'password': settings.postgres_password,
        }
    
    async def connect(self):
        """Initialize connection pool."""
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(
                    **self._connection_params,
                    min_size=2,
                    max_size=10,
                    command_timeout=60
                )
                logger.info("PostgreSQL connection pool created")
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                raise
    
    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")
    
    async def execute(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute query and return all rows as list of dicts."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def execute_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute query and return single row as dict or None."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def execute_val(self, query: str, *args) -> Any:
        """Execute query and return single value."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    # ============================================================
    # User Authentication Methods
    # ============================================================
    
    async def create_user(self, username: str, password_hash: str) -> int:
        """Create new user and return user_id."""
        user_id = await self.execute_val("""
            INSERT INTO users (username, password_hash)
            VALUES ($1, $2)
            RETURNING id
        """, username, password_hash)
        logger.info(f"Created user: {username} (id={user_id})")
        return user_id
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        return await self.execute_one("""
            SELECT id, username, password_hash, created_at, last_login, onboarding_completed
            FROM users
            WHERE username = $1
        """, username)
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return await self.execute_one("""
            SELECT id, username, created_at, last_login, onboarding_completed
            FROM users
            WHERE id = $1
        """, user_id)
    
    async def update_last_login(self, user_id: int):
        """Update last login timestamp."""
        await self.execute("""
            UPDATE users
            SET last_login = NOW()
            WHERE id = $1
        """, user_id)
    
    async def complete_onboarding(self, user_id: int):
        """Mark user onboarding as completed."""
        await self.execute("""
            UPDATE users
            SET onboarding_completed = TRUE
            WHERE id = $1
        """, user_id)
    
    async def get_library_count(self, user_id: int, exclude_onboarding: bool = True) -> int:
        """
        Get count of books in user's library.
        
        Args:
            exclude_onboarding: if True, exclude books added during onboarding (default: True)
        """
        where_clause = "AND source != 'onboarding'" if exclude_onboarding else ""
        query = f"""
            SELECT COUNT(*)
            FROM user_library
            WHERE user_id = $1 {where_clause}
        """
        count = await self.execute_val(query, user_id)
        return count or 0
    
    # ============================================================
    # User Library Methods
    # ============================================================
    
    async def add_to_library(
        self,
        user_id: int,
        book_id: str,
        source: Optional[str] = None,
        source_query: Optional[str] = None
    ) -> bool:
        """
        Add book to user's library.
        Returns True if added, False if already exists.
        """
        try:
            await self.execute("""
                INSERT INTO user_library (user_id, book_id, source, source_query)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, book_id) DO NOTHING
            """, user_id, book_id, source, source_query)
            
            # Mark preference vector for recalculation
            await self.mark_preference_for_recalculation(user_id)
            
            logger.info(f"User {user_id} added book {book_id} to library")
            return True
        except Exception as e:
            logger.error(f"Error adding to library: {e}")
            return False
    
    async def remove_from_library(self, user_id: int, book_id: str):
        """Remove book from user's library and associated review."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Delete review if exists
                await conn.execute("""
                    DELETE FROM user_reviews
                    WHERE user_id = $1 AND book_id = $2
                """, user_id, book_id)
                
                # Delete from library
                await conn.execute("""
                    DELETE FROM user_library
                    WHERE user_id = $1 AND book_id = $2
                """, user_id, book_id)
        
        # Mark preference vector for recalculation
        await self.mark_preference_for_recalculation(user_id)
        
        logger.info(f"User {user_id} removed book {book_id} from library")
    
    async def get_user_library_book_ids(self, user_id: int, exclude_onboarding: bool = True) -> List[str]:
        """
        Get list of book IDs in user's library.
        
        Args:
            exclude_onboarding: if True, exclude books added during onboarding (default: True)
        """
        where_clause = "AND source != 'onboarding'" if exclude_onboarding else ""
        query = f"""
            SELECT book_id
            FROM user_library
            WHERE user_id = $1 {where_clause}
        """
        rows = await self.execute(query, user_id)
        return [row['book_id'] for row in rows]
    
    async def is_in_library(self, user_id: int, book_id: str) -> bool:
        """Check if book is in user's library."""
        result = await self.execute_val("""
            SELECT EXISTS(
                SELECT 1 FROM user_library
                WHERE user_id = $1 AND book_id = $2
            )
        """, user_id, book_id)
        return result or False
    
    async def get_library_with_details(
        self,
        user_id: int,
        sort: str = 'added_at',
        rated_only: bool = False,
        exclude_onboarding: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get user's library with book details and reviews.
        
        Args:
            sort: 'added_at', 'rating', 'alphabetical'
            rated_only: if True, only return books with ratings
            exclude_onboarding: if True, exclude books added during onboarding (default: True)
        """
        order_clause = {
            'added_at': 'ul.added_at DESC',
            'rating': 'ur.rating DESC NULLS LAST, ul.added_at DESC',
            'alphabetical': 'ul.book_id ASC'  # Will sort by book_id as proxy
        }.get(sort, 'ul.added_at DESC')
        
        where_clauses = []
        if rated_only:
            where_clauses.append("ur.rating IS NOT NULL")
        if exclude_onboarding:
            where_clauses.append("ul.source != 'onboarding'")
        
        where_clause = ""
        if where_clauses:
            where_clause = "AND " + " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                ul.book_id,
                ul.added_at,
                ul.source,
                ul.source_query,
                ur.rating,
                ur.review_text,
                ur.created_at as review_created_at,
                ur.updated_at as review_updated_at
            FROM user_library ul
            LEFT JOIN user_reviews ur ON ul.user_id = ur.user_id AND ul.book_id = ur.book_id
            WHERE ul.user_id = $1 {where_clause}
            ORDER BY {order_clause}
        """
        
        return await self.execute(query, user_id)
    
    # ============================================================
    # Review Methods
    # ============================================================
    
    async def upsert_review(
        self,
        user_id: int,
        book_id: str,
        rating: int,
        review_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update review."""
        row = await self.execute_one("""
            INSERT INTO user_reviews (user_id, book_id, rating, review_text)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, book_id) DO UPDATE SET
                rating = EXCLUDED.rating,
                review_text = EXCLUDED.review_text,
                updated_at = NOW()
            RETURNING id, book_id, rating, review_text, created_at, updated_at
        """, user_id, book_id, rating, review_text)
        
        # Mark preference vector for recalculation
        await self.mark_preference_for_recalculation(user_id)
        
        logger.info(f"User {user_id} reviewed book {book_id} with rating {rating}")
        return row
    
    async def get_review(self, user_id: int, book_id: str) -> Optional[Dict[str, Any]]:
        """Get user's review for a book."""
        return await self.execute_one("""
            SELECT book_id, rating, review_text, created_at, updated_at
            FROM user_reviews
            WHERE user_id = $1 AND book_id = $2
        """, user_id, book_id)
    
    async def delete_review(self, user_id: int, book_id: str):
        """Delete review (keep book in library)."""
        await self.execute("""
            DELETE FROM user_reviews
            WHERE user_id = $1 AND book_id = $2
        """, user_id, book_id)
        
        # Mark preference vector for recalculation
        await self.mark_preference_for_recalculation(user_id)
        
        logger.info(f"User {user_id} deleted review for book {book_id}")
    
    # ============================================================
    # Preference Vector Methods
    # ============================================================
    
    async def get_user_preference_vector(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's preference vector."""
        row = await self.execute_one("""
            SELECT preference_vector, last_updated, books_count, needs_recalculation
            FROM user_preference_vectors
            WHERE user_id = $1
        """, user_id)
        
        if row and row['preference_vector']:
            import pickle
            row['vector'] = pickle.loads(row['preference_vector'])
        
        return row
    
    async def save_preference_vector(
        self,
        user_id: int,
        vector_bytes: bytes,
        books_count: int
    ):
        """Save preference vector for user."""
        await self.execute("""
            INSERT INTO user_preference_vectors 
            (user_id, preference_vector, last_updated, books_count, needs_recalculation)
            VALUES ($1, $2, NOW(), $3, FALSE)
            ON CONFLICT (user_id) DO UPDATE SET
                preference_vector = EXCLUDED.preference_vector,
                last_updated = NOW(),
                books_count = EXCLUDED.books_count,
                needs_recalculation = FALSE
        """, user_id, vector_bytes, books_count)
    
    async def mark_preference_for_recalculation(self, user_id: int):
        """Mark user's preference vector for recalculation."""
        await self.execute("""
            INSERT INTO user_preference_vectors (user_id, preference_vector, needs_recalculation)
            VALUES ($1, $2, TRUE)
            ON CONFLICT (user_id) DO UPDATE SET needs_recalculation = TRUE
        """, user_id, b'')
    
    async def get_users_needing_recalculation(self) -> List[int]:
        """Get list of user IDs needing preference recalculation."""
        rows = await self.execute("""
            SELECT user_id 
            FROM user_preference_vectors 
            WHERE needs_recalculation = TRUE
        """)
        return [row['user_id'] for row in rows]
    
    # ============================================================
    # Onboarding Methods
    # ============================================================
    
    async def get_onboarding_books(self) -> List[Dict[str, Any]]:
        """Get all onboarding books grouped by category."""
        return await self.execute("""
            SELECT book_id, title, author, category, display_order
            FROM onboarding_books
            ORDER BY category, display_order
        """)
    
    # ============================================================
    # Book Cover Methods
    # ============================================================
    
    async def get_cover_url(self, book_id: str) -> Optional[str]:
        """
        Get cached cover URL. 
        
        Returns:
            Cover URL if cached (including placeholders), None if not in cache.
            Note: With new fallback strategy, this should always return a URL once fetched.
        """
        row = await self.execute_one("""
            SELECT cover_url, fetch_failed 
            FROM book_covers 
            WHERE book_id = $1
        """, book_id)
        
        if row is None:
            return None  # Not in cache
        
        # Return URL even if fetch_failed=True (for old records or placeholders)
        # New implementation always stores a URL (even if placeholder)
        return row['cover_url']
    
    async def cache_cover_url(
        self,
        book_id: str,
        cover_url: str,  # Now always str, never None
        source: str = 'unknown',  # NEW: track source
        fetch_failed: bool = False  # Kept for backward compatibility
    ):
        """
        Cache cover URL result.
        
        Args:
            book_id: Book ID
            cover_url: Cover URL (can be real URL or placeholder)
            source: Source of cover ('google_books', 'duckduckgo', 'generated')
            fetch_failed: Deprecated, kept for backward compatibility
        """
        await self.execute("""
            INSERT INTO book_covers (book_id, cover_url, source, fetched_at, fetch_failed)
            VALUES ($1, $2, $3, NOW(), $4)
            ON CONFLICT (book_id) DO UPDATE SET
                cover_url = EXCLUDED.cover_url,
                source = EXCLUDED.source,
                fetched_at = NOW(),
                fetch_failed = EXCLUDED.fetch_failed
        """, book_id, cover_url, source, fetch_failed)
    
    # ============================================================
    # Recommendation Logging Methods
    # ============================================================
    
    async def log_recommendation(
        self,
        user_id: int,
        query: str,
        returned_book_ids: List[str],
        personalization_used: bool = False,
        similarity_score: Optional[float] = None
    ):
        """Log recommendation for metrics tracking."""
        await self.execute("""
            INSERT INTO recommendation_logs 
            (user_id, query, returned_book_ids, personalization_used, similarity_score)
            VALUES ($1, $2, $3, $4, $5)
        """, user_id, query, returned_book_ids, personalization_used, similarity_score)
    
    async def update_recommendation_likes(
        self,
        log_id: int,
        liked_book_ids: List[str]
    ):
        """Update recommendation log with books user added to library."""
        await self.execute("""
            UPDATE recommendation_logs
            SET liked_book_ids = $1
            WHERE id = $2
        """, liked_book_ids, log_id)
    
    # ============================================================
    # Metrics Methods
    # ============================================================
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics for admin dashboard."""
        metrics = {}
        
        # Total users
        metrics['total_users'] = await self.execute_val("""
            SELECT COUNT(*) FROM users
        """) or 0
        
        # Active users (7 days)
        metrics['active_users_7d'] = await self.execute_val("""
            SELECT COUNT(DISTINCT user_id)
            FROM recommendation_logs
            WHERE timestamp > NOW() - INTERVAL '7 days'
        """) or 0
        
        # Total queries
        metrics['total_queries_all_time'] = await self.execute_val("""
            SELECT COUNT(*) FROM recommendation_logs
        """) or 0
        
        # Queries today
        metrics['total_queries_today'] = await self.execute_val("""
            SELECT COUNT(*)
            FROM recommendation_logs
            WHERE DATE(timestamp) = CURRENT_DATE
        """) or 0
        
        # Queries this week
        metrics['total_queries_week'] = await self.execute_val("""
            SELECT COUNT(*)
            FROM recommendation_logs
            WHERE timestamp > NOW() - INTERVAL '7 days'
        """) or 0
        
        # Primary acceptance rate
        # Count books added from search (excluding onboarding) as "liked"
        # Count total books returned in search results as "returned"
        # Since we don't have recommendation_logs populated, use alternative:
        # Count search-added books vs total search results (approximation)
        search_books_count = await self.execute_val("""
            SELECT COUNT(*) 
            FROM user_library 
            WHERE source = 'search'
        """) or 0
        
        # Get total search results from recommendation_logs if available
        total_returned = await self.execute_val("""
            SELECT COALESCE(SUM(array_length(returned_book_ids, 1)), 0)
            FROM recommendation_logs
        """) or 0
        
        # If no logs, estimate based on search books (assume ~10 results per search)
        if total_returned == 0 and search_books_count > 0:
            # Rough estimate: assume each search returns ~10 books
            # This is a fallback until recommendation_logs are properly populated
            total_returned = search_books_count * 10
        
        if total_returned > 0:
            metrics['primary_acceptance_rate'] = float(search_books_count) / float(total_returned) * 100.0
        else:
            metrics['primary_acceptance_rate'] = 0.0
        
        # Final acceptance rate
        # Percentage of books in library that have rating >= 7
        final_data = await self.execute_one("""
            SELECT 
                COUNT(CASE WHEN ur.rating >= 7 THEN 1 END) as high_rated,
                COUNT(DISTINCT ul.book_id) as total_library
            FROM user_library ul
            LEFT JOIN user_reviews ur ON ul.user_id = ur.user_id AND ul.book_id = ur.book_id
            WHERE ul.source != 'onboarding'
        """)
        
        if final_data and final_data['total_library'] and final_data['total_library'] > 0:
            metrics['final_acceptance_rate'] = float(
                final_data['high_rated'] or 0
            ) / float(final_data['total_library']) * 100.0
        else:
            metrics['final_acceptance_rate'] = 0.0
        
        # Average library size (excluding onboarding books - they are just placeholders)
        avg_lib_size = await self.execute_val("""
            SELECT AVG(book_count)::float
            FROM (
                SELECT user_id, COUNT(*) as book_count
                FROM user_library
                WHERE source != 'onboarding'
                GROUP BY user_id
            ) subq
        """)
        # Return 0.0 if no non-onboarding books (don't fallback to include onboarding)
        metrics['avg_library_size'] = float(avg_lib_size) if avg_lib_size is not None else 0.0
        
        # Average rating (excluding onboarding books)
        avg_rating = await self.execute_val("""
            SELECT AVG(ur.rating)::float
            FROM user_reviews ur
            JOIN user_library ul ON ur.user_id = ul.user_id AND ur.book_id = ul.book_id
            WHERE ul.source != 'onboarding'
        """)
        metrics['avg_rating'] = float(avg_rating) if avg_rating is not None else 0.0
        
        # Median rating (excluding onboarding books)
        median_rating = await self.execute_val("""
            SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ur.rating)::float
            FROM user_reviews ur
            JOIN user_library ul ON ur.user_id = ul.user_id AND ur.book_id = ul.book_id
            WHERE ul.source != 'onboarding'
        """)
        metrics['median_rating'] = float(median_rating) if median_rating is not None else 0.0
        
        return metrics


# Global instance
postgres_db = PostgresService()
