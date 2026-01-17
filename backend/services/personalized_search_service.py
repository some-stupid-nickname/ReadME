"""Personalized search service that wraps existing RAG assistant"""
from typing import Optional, List, Dict, Any
import numpy as np
from loguru import logger

from services.rag_service import BookRAGAssistant
from database.postgres_service import PostgresService
from services.sqlite_helper import SQLiteBookService
from models.schemas import PersonalizedSearchResponse, BookInfo


class PersonalizedSearchService:
    """
    Wrapper service that adds personalization layer around existing RAG.
    DOES NOT modify BookRAGAssistant - only enhances inputs and filters outputs.
    
    Personalization strategy:
    1. BEFORE: Enhance query with user's reading history (if similar)
    2. CALL: Existing RAG assistant (UNCHANGED)
    3. AFTER: Filter out books already in user's library
    """
    
    SIMILARITY_THRESHOLD = 0.3  # Minimum similarity to apply personalization
    MAX_CONTEXT_BOOKS = 3  # Maximum books to include in context
    
    def __init__(
        self,
        rag_assistant: BookRAGAssistant,
        postgres_db: PostgresService,
        sqlite_db: SQLiteBookService
    ):
        self.rag = rag_assistant  # Existing RAG - UNCHANGED
        self.pg_db = postgres_db
        self.sqlite_db = sqlite_db
    
    async def search(
        self,
        user_id: int,
        query: str
    ) -> PersonalizedSearchResponse:
        """
        Perform personalized search with context from user's library.
        Falls back to standard search if insufficient personalization data.
        
        Args:
            user_id: Authenticated user ID
            query: Search query
        
        Returns:
            PersonalizedSearchResponse with metadata
        """
        
        # Step 1: Try to get personalization context
        context = await self._get_personalization_context(user_id, query)
        
        # Step 2: Enhance query if context available
        if context:
            enhanced_query = self._build_enhanced_prompt(query, context)
            personalization_applied = True
            similarity_score = context['similarity']
            context_books = context['book_titles']
            logger.info(f"Personalization applied for user {user_id}, similarity={similarity_score:.3f}")
        else:
            enhanced_query = query
            personalization_applied = False
            similarity_score = None
            context_books = None
            logger.info(f"No personalization for user {user_id} (insufficient data or low similarity)")
        
        # Step 3: Call EXISTING RAG (no modifications to BookRAGAssistant)
        # Returns tuple: (response_text, list of (Book, score))
        rag_response_text, rag_books = await self.rag.ask(enhanced_query)
        
        # Transform rag_books to BookInfo list with cover URLs
        books_list = []
        for book_obj, score in rag_books:
            # Extract authors - handle both string and list
            authors = book_obj.authors
            if isinstance(authors, list):
                author_display = authors[0] if authors else "Unknown"
            else:
                author_display = str(authors).split(',')[0].strip()
            
            # Extract genres
            category = book_obj.category if hasattr(book_obj, 'category') else ""
            if category:
                genres = [g.strip() for g in category.replace(';', ',').split(',') if g.strip()]
            else:
                genres = []
            
            # Get cover URL from cache (don't fetch - too slow for search results)
            cover_url = await self.pg_db.get_cover_url(str(book_obj.id))
            
            books_list.append(BookInfo(
                id=str(book_obj.id),
                title=book_obj.title,
                author=author_display,
                genres=genres,
                description=book_obj.description if hasattr(book_obj, 'description') else "",
                cover_url=cover_url,
                source_link=None
            ))
        
        # Step 4: Post-filter - remove books already in library
        filtered_books = await self._filter_library_books(books_list, user_id)
        
        # Step 5: Log recommendation
        await self._log_recommendation(
            user_id=user_id,
            query=query,
            returned_books=[b.id for b in filtered_books],
            personalization_used=personalization_applied,
            similarity_score=similarity_score
        )
        
        # Step 6: Return enhanced response
        return PersonalizedSearchResponse(
            response=rag_response_text,
            books=filtered_books,
            message_id=None,  # Not using message IDs for web interface
            personalization_applied=personalization_applied,
            similarity_score=similarity_score,
            context_books=context_books
        )
    
    async def _get_personalization_context(
        self,
        user_id: int,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Determine if personalization should be applied based on query similarity
        to user's reading preferences.
        
        Returns:
            dict with {similarity: float, book_titles: List[str], books: List[dict]}
            or None if personalization not applicable
        """
        
        # Load user preference vector
        pref_data = await self.pg_db.get_user_preference_vector(user_id)
        if not pref_data or pref_data.get('books_count', 0) < 3:
            return None  # Insufficient data
        
        preference_vector = pref_data['vector']  # numpy array (384,)
        
        # Generate embedding for current query
        # Use same embedder as RAG (all-MiniLM-L6-v2)
        query_embedding = self.sqlite_db.generate_embedding(query)
        
        # Compute cosine similarity
        similarity = self._cosine_similarity(query_embedding, preference_vector)
        
        # Check threshold
        if similarity < self.SIMILARITY_THRESHOLD:
            return None  # Query not related to user preferences
        
        # Fetch context books (top-rated from library)
        context_books = await self._get_context_books(user_id)
        
        if not context_books:
            return None
        
        return {
            'similarity': similarity,
            'book_titles': [b['title'] for b in context_books],
            'books': context_books
        }
    
    async def _get_context_books(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get top-3 highest-rated books from user's library for context.
        If user has < 3 rated books, include recent additions.
        
        Returns:
            List of dicts with book details
        """
        
        # Get library with details
        library = await self.pg_db.get_library_with_details(
            user_id=user_id,
            sort='rating',
            rated_only=False
        )
        
        if not library:
            return []
        
        # Get book IDs
        book_ids = [entry['book_id'] for entry in library[:self.MAX_CONTEXT_BOOKS]]
        
        # Fetch book details from SQLite
        books_data = self.sqlite_db.get_books_by_ids(book_ids)
        
        # Combine with ratings
        result = []
        for book_data in books_data:
            # Find corresponding library entry
            lib_entry = next((e for e in library if e['book_id'] == book_data['book_id']), None)
            
            result.append({
                'book_id': book_data['book_id'],
                'title': book_data['title'],
                'authors': book_data['authors'],
                'rating': lib_entry['rating'] if lib_entry else None
            })
        
        return result
    
    def _build_enhanced_prompt(self, original_query: str, context: Dict[str, Any]) -> str:
        """
        Build enhanced prompt with personalization context.
        Context is added as system instruction, not as user message modification.
        
        Args:
            original_query: User's original query
            context: Personalization context with books
        
        Returns:
            Enhanced query string
        """
        
        books_list = "\n".join([
            f"- \"{book['title']}\" by {book['authors'].split(',')[0]}" + 
            (f" (rated {book['rating']}/10)" if book.get('rating') else "")
            for book in context['books']
        ])
        
        enhanced_prompt = f"""[PERSONALIZATION CONTEXT]
The user has previously enjoyed these books:
{books_list}

This suggests the user may appreciate similar themes or styles, but only if relevant to their current request.
[END CONTEXT]

User's request: {original_query}

Provide recommendations that best match the user's request. Consider their reading history only if it naturally aligns with what they're asking for."""
        
        return enhanced_prompt
    
    async def _filter_library_books(
        self,
        books: List[BookInfo],
        user_id: int
    ) -> List[BookInfo]:
        """
        Remove books that user already has in library.
        Prevents recommending books they've already saved.
        
        Args:
            books: List of BookInfo objects
            user_id: User ID
        
        Returns:
            Filtered list of BookInfo
        """
        
        library_book_ids = await self.pg_db.get_user_library_book_ids(user_id)
        library_set = set(library_book_ids)
        
        filtered = [book for book in books if book.id not in library_set]
        
        removed_count = len(books) - len(filtered)
        if removed_count > 0:
            logger.info(f"Filtered {removed_count} books already in user {user_id}'s library")
        
        return filtered
    
    async def _log_recommendation(
        self,
        user_id: int,
        query: str,
        returned_books: List[str],
        personalization_used: bool,
        similarity_score: Optional[float]
    ):
        """
        Log recommendation for metrics tracking.
        
        Args:
            user_id: User ID
            query: Search query
            returned_books: List of book IDs returned
            personalization_used: Whether personalization was applied
            similarity_score: Similarity score if personalization used
        """
        try:
            await self.pg_db.log_recommendation(
                user_id=user_id,
                query=query,
                returned_book_ids=returned_books,
                personalization_used=personalization_used,
                similarity_score=similarity_score
            )
        except Exception as e:
            # Don't fail the request if logging fails
            logger.error(f"Failed to log recommendation: {e}")
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Cosine similarity (0-1)
        """
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-10))
