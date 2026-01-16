"""Background jobs for preference vector recalculation"""
import asyncio
import gc
from datetime import datetime
from typing import List, Optional
import numpy as np
import pickle
from loguru import logger

from database.postgres_service import PostgresService
from services.sqlite_helper import SQLiteBookService


class PreferenceVectorRecalculator:
    """
    Background service to recalculate user preference vectors.
    Optimized for low memory usage on weak servers.
    
    Strategy:
    - Process users in small batches (10 at a time)
    - Load embeddings incrementally (not all at once)
    - Force garbage collection between batches
    - Use weighted average based on ratings
    """
    
    BATCH_SIZE = 10  # Process 10 users at a time
    MIN_BOOKS_REQUIRED = 3  # Minimum books to create preference vector
    
    def __init__(self, postgres_db: PostgresService, sqlite_db: SQLiteBookService):
        self.pg_db = postgres_db
        self.sqlite_db = sqlite_db
    
    async def recalculate_pending_users(self):
        """
        Main job function - runs every hour via APScheduler.
        Only processes users marked with needs_recalculation=TRUE.
        """
        start_time = datetime.utcnow()
        
        # Find users needing update
        users_to_update = await self._get_users_needing_update()
        
        if not users_to_update:
            logger.info("No users need preference vector recalculation")
            return
        
        total = len(users_to_update)
        logger.info(f"Starting preference recalculation for {total} users")
        
        success_count = 0
        error_count = 0
        
        # Process in batches to limit memory usage
        for i in range(0, total, self.BATCH_SIZE):
            batch = users_to_update[i:i + self.BATCH_SIZE]
            batch_num = (i // self.BATCH_SIZE) + 1
            total_batches = (total + self.BATCH_SIZE - 1) // self.BATCH_SIZE
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} users)")
            
            # Process batch
            batch_success, batch_errors = await self._process_batch(batch)
            success_count += batch_success
            error_count += batch_errors
            
            # Force garbage collection between batches
            gc.collect()
            
            # Small delay to prevent CPU spike
            await asyncio.sleep(0.5)
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Preference recalculation complete: "
            f"{success_count} succeeded, {error_count} failed, "
            f"elapsed {elapsed:.1f}s"
        )
    
    async def _process_batch(self, user_ids: List[int]) -> tuple:
        """
        Process one batch of users.
        
        Returns:
            tuple: (success_count, error_count)
        """
        success = 0
        errors = 0
        
        for user_id in user_ids:
            try:
                await self._recalculate_user(user_id)
                success += 1
            except Exception as e:
                logger.error(f"Failed to recalculate user {user_id}: {e}")
                errors += 1
                continue  # Don't stop entire batch on one failure
        
        return success, errors
    
    async def _recalculate_user(self, user_id: int):
        """
        Recalculate preference vector for a single user.
        Memory-efficient: loads embeddings one at a time, not all at once.
        
        Algorithm:
        1. Fetch user's library books with ratings
        2. Load embeddings incrementally
        3. Compute weighted average (higher ratings = higher weight)
        4. Normalize to unit vector
        5. Save to PostgreSQL
        
        Args:
            user_id: User ID to recalculate
        """
        
        # 1. Fetch library books with ratings
        library_data = await self.pg_db.execute("""
            SELECT 
                ul.book_id,
                ur.rating
            FROM user_library ul
            LEFT JOIN user_reviews ur ON ul.user_id = ur.user_id 
                AND ul.book_id = ur.book_id
            WHERE ul.user_id = $1
            ORDER BY ul.added_at DESC
        """, user_id)
        
        if len(library_data) < self.MIN_BOOKS_REQUIRED:
            logger.debug(f"User {user_id} has < {self.MIN_BOOKS_REQUIRED} books, skipping")
            await self._mark_recalculation_done(user_id)
            return
        
        # 2. Load embeddings incrementally (memory-efficient)
        embeddings = []
        weights = []
        
        for row in library_data:
            book_id = row['book_id']
            rating = row.get('rating')
            
            # Fetch embedding from SQLite (single read)
            embedding = self.sqlite_db.get_embedding(book_id)
            if embedding is None:
                logger.warning(f"No embedding for book {book_id}, skipping")
                continue
            
            embeddings.append(embedding)
            weights.append(self._compute_weight(rating))
            
            # Clear reference immediately to help GC
            del embedding
        
        if len(embeddings) < self.MIN_BOOKS_REQUIRED:
            logger.warning(f"User {user_id} has insufficient valid embeddings")
            await self._mark_recalculation_done(user_id)
            return
        
        # 3. Compute weighted average (vectorized operation)
        embeddings_array = np.array(embeddings, dtype=np.float32)
        weights_array = np.array(weights, dtype=np.float32)
        
        # Normalize weights
        weights_array = weights_array / weights_array.sum()
        
        # Weighted average
        preference_vector = np.average(
            embeddings_array,
            weights=weights_array,
            axis=0
        )
        
        # Normalize to unit vector (improves cosine similarity performance)
        preference_vector = preference_vector / (np.linalg.norm(preference_vector) + 1e-10)
        
        # 4. Pickle and save to PostgreSQL
        vector_bytes = pickle.dumps(preference_vector)
        
        await self.pg_db.save_preference_vector(
            user_id=user_id,
            vector_bytes=vector_bytes,
            books_count=len(embeddings)
        )
        
        logger.debug(f"Updated preference vector for user {user_id} ({len(embeddings)} books)")
        
        # 5. Clean up
        del embeddings, weights, embeddings_array, weights_array, preference_vector, vector_bytes
    
    def _compute_weight(self, rating: Optional[int]) -> float:
        """
        Convert rating (1-10) to weight for embedding aggregation.
        
        Formula: (rating - 5) / 5
        - Rating 10 → weight 1.0 (strong positive)
        - Rating 5 → weight 0.0 (neutral)
        - Rating 1 → weight -0.8 (negative, but not fully discounted)
        - No rating → weight 0.5 (mild positive, user saved it)
        
        Args:
            rating: User rating (1-10) or None
        
        Returns:
            Weight for embedding aggregation
        """
        if rating is None:
            return 0.5  # Neutral-positive weight for unrated books
        
        return (rating - 5) / 5.0
    
    async def _get_users_needing_update(self) -> List[int]:
        """
        Get list of users marked for recalculation.
        Flag is set when library/reviews change.
        
        Returns:
            List of user IDs
        """
        rows = await self.pg_db.execute("""
            SELECT user_id 
            FROM user_preference_vectors 
            WHERE needs_recalculation = TRUE
        """)
        
        return [row['user_id'] for row in rows]
    
    async def _mark_recalculation_done(self, user_id: int):
        """
        Mark user as processed (even if skipped due to insufficient data).
        
        Args:
            user_id: User ID
        """
        await self.pg_db.execute("""
            UPDATE user_preference_vectors 
            SET needs_recalculation = FALSE 
            WHERE user_id = $1
        """, user_id)


# Convenience function to mark user for recalculation
async def mark_user_for_recalculation(postgres_db: PostgresService, user_id: int):
    """
    Call this when user's library or reviews change.
    Sets flag for background job to process.
    
    Args:
        postgres_db: PostgreSQL service instance
        user_id: User ID to mark
    """
    await postgres_db.mark_preference_for_recalculation(user_id)
