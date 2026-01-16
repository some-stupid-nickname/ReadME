"""Service for fetching book covers from Google Books API"""
import asyncio
from typing import Optional, List, Dict
from urllib.parse import quote_plus
import httpx
from loguru import logger
from database.postgres_service import PostgresService


class CoverFetchService:
    """
    Fetch book covers from Google Books API.
    Features: caching, rate limiting, fallback handling.
    """
    
    GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
    RATE_LIMIT_DELAY = 1.0  # seconds between requests (free tier: 1000/day)
    REQUEST_TIMEOUT = 5.0  # seconds
    
    def __init__(self, postgres_db: PostgresService, api_key: Optional[str] = None):
        self.pg_db = postgres_db
        self.api_key = api_key  # Optional API key for higher quota
        self._last_request_time = 0
        self._lock = asyncio.Lock()  # Prevent concurrent API calls
    
    async def get_cover_url(
        self,
        book_id: str,
        title: str,
        author: str
    ) -> Optional[str]:
        """
        Get cover URL for a book. Checks cache first, fetches if needed.
        
        Args:
            book_id: Book ID for caching
            title: Book title for API search
            author: Book author for API search
        
        Returns:
            Cover URL or None if not found
        """
        
        # 1. Check cache first
        cached = await self.pg_db.get_cover_url(book_id)
        if cached is not None:
            return cached  # May be URL or None (if fetch previously failed)
        
        # 2. Fetch from API
        cover_url = await self._fetch_from_api(title, author)
        
        # 3. Cache result (even if None)
        await self.pg_db.cache_cover_url(
            book_id=book_id,
            cover_url=cover_url,
            fetch_failed=(cover_url is None)
        )
        
        return cover_url
    
    async def _fetch_from_api(self, title: str, author: str) -> Optional[str]:
        """
        Fetch cover URL from Google Books API.
        Rate-limited to 1 request/second.
        
        Args:
            title: Book title
            author: Book author
        
        Returns:
            Cover URL or None if not found
        """
        
        # Rate limiting
        async with self._lock:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self._last_request_time
            
            if time_since_last < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)
            
            self._last_request_time = asyncio.get_event_loop().time()
        
        # Construct query
        # Use first author only (before comma)
        first_author = author.split(',')[0].strip() if author else ""
        query = f'intitle:{title}'
        if first_author:
            query += f'+inauthor:{first_author}'
        
        params = {'q': query, 'maxResults': 1}
        if self.api_key:
            params['key'] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                response = await client.get(self.GOOGLE_BOOKS_API, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Parse response
                if data.get('totalItems', 0) > 0:
                    items = data.get('items', [])
                    if items:
                        volume_info = items[0].get('volumeInfo', {})
                        image_links = volume_info.get('imageLinks', {})
                        
                        # Prefer larger image if available
                        cover_url = (
                            image_links.get('large') or
                            image_links.get('medium') or
                            image_links.get('thumbnail')
                        )
                        
                        if cover_url:
                            # Upgrade to HTTPS if needed
                            cover_url = cover_url.replace('http://', 'https://')
                            logger.info(f"Found cover for '{title}': {cover_url}")
                            return cover_url
                
                logger.debug(f"No cover found for '{title}' by {first_author}")
                return None
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching cover: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Network error fetching cover: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching cover: {e}")
            return None
    
    async def prefetch_covers_batch(
        self,
        books: List[Dict[str, str]]  # [{book_id, title, author}, ...]
    ):
        """
        Prefetch covers for a batch of books (background task).
        Used for onboarding books or popular books.
        
        Args:
            books: List of dicts with book_id, title, author
        """
        logger.info(f"Prefetching covers for {len(books)} books")
        
        for book in books:
            await self.get_cover_url(
                book_id=book['book_id'],
                title=book['title'],
                author=book['author']
            )
            # Delay between requests
            await asyncio.sleep(self.RATE_LIMIT_DELAY)
        
        logger.info("Cover prefetching completed")
