"""Service for fetching book covers with fallback strategy"""
import asyncio
from typing import Optional, List, Dict
from urllib.parse import quote
import httpx
from loguru import logger
from database.postgres_service import PostgresService

# duckduckgo-search==8.1.1
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logger.warning("duckduckgo-search not installed. Install with: pip install duckduckgo-search==8.1.1")


class CoverFetchService:
    """
    Fetch book covers with waterfall strategy:
    1. Cache (instant)
    2. Google Books API (best quality)
    3. DuckDuckGo Images (good coverage, works in Russia)
    4. Generated placeholder (always works)
    """
    
    GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
    RATE_LIMIT_DELAY = 1.0  # seconds between requests
    REQUEST_TIMEOUT = 5.0  # seconds
    
    def __init__(self, postgres_db: PostgresService, api_key: Optional[str] = None):
        self.pg_db = postgres_db
        self.api_key = api_key
        self._last_request_time = 0
        self._lock = asyncio.Lock()
    
    async def get_cover_url(
        self,
        book_id: str,
        title: str,
        author: str
    ) -> str:
        """
        Get cover URL for a book with fallback strategy.
        
        Strategy:
        1. Check cache (instant)
        2. Try Google Books API
        3. Try DuckDuckGo Images (fallback)
        4. Generate placeholder (always works)
        
        Returns:
            Cover URL (always returns a valid URL, never None)
        """
        
        # 1. Check cache first
        cached = await self.pg_db.get_cover_url(book_id)
        if cached is not None:
            return cached
        
        # 2. Try Google Books API
        logger.debug(f"Fetching cover for '{title}' by {author}")
        cover_url = await self._fetch_from_google_books(title, author)
        if cover_url:
            await self.pg_db.cache_cover_url(
                book_id=book_id,
                cover_url=cover_url,
                source='google_books'
            )
            logger.info(f"✓ Found cover via Google Books: {title}")
            return cover_url
        
        # Small delay between different services
        await asyncio.sleep(0.5)
        
        # 3. Try DuckDuckGo (fallback)
        cover_url = await self._fetch_from_duckduckgo(title, author)
        if cover_url:
            await self.pg_db.cache_cover_url(
                book_id=book_id,
                cover_url=cover_url,
                source='duckduckgo'
            )
            logger.info(f"✓ Found cover via DuckDuckGo: {title}")
            return cover_url
        
        # 4. Generate placeholder (always works)
        placeholder_url = self._generate_placeholder(title, author)
        await self.pg_db.cache_cover_url(
            book_id=book_id,
            cover_url=placeholder_url,
            source='generated'
        )
        logger.info(f"→ Generated placeholder for: {title}")
        return placeholder_url
    
    async def _fetch_from_google_books(self, title: str, author: str) -> Optional[str]:
        """
        Fetch cover URL from Google Books API.
        Rate-limited to 1 request/second.
        """
        
        # Rate limiting
        async with self._lock:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self._last_request_time
            
            if time_since_last < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)
            
            self._last_request_time = asyncio.get_event_loop().time()
        
        # Construct query
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
                
                if data.get('totalItems', 0) > 0:
                    items = data.get('items', [])
                    if items:
                        volume_info = items[0].get('volumeInfo', {})
                        image_links = volume_info.get('imageLinks', {})
                        
                        cover_url = (
                            image_links.get('large') or
                            image_links.get('medium') or
                            image_links.get('thumbnail')
                        )
                        
                        if cover_url:
                            cover_url = cover_url.replace('http://', 'https://')
                            return cover_url
                
                return None
        
        except httpx.HTTPStatusError as e:
            logger.warning(f"Google Books HTTP error for '{title}': {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"Google Books network error for '{title}': {e}")
            return None
        except Exception as e:
            logger.error(f"Google Books unexpected error for '{title}': {e}")
            return None
    
    async def _fetch_from_duckduckgo(self, title: str, author: str) -> Optional[str]:
        """
        Fetch cover URL from DuckDuckGo Images using version 8.1.1 API.
        Works in Russia, no API key needed, no strict rate limits.
        
        Returns:
            Cover URL or None if not found
        """
        
        if not DDGS_AVAILABLE:
            logger.debug("DuckDuckGo search not available (library not installed)")
            return None
        
        try:
            # Construct search query
            query = f'"{title}" "{author}" book cover'
            
            # DDGS is synchronous in v8.x, run in executor
            loop = asyncio.get_event_loop()
            
            def search_images():
                """Synchronous search function to run in executor"""
                try:
                    # Create DDGS instance (v8.1.1 API)
                    ddgs = DDGS()
                    
                    # Search images with v8.x parameters
                    results = ddgs.images(
                        keywords=query,
                        region='wt-wt',  # Worldwide
                        safesearch='off',  # Get all results
                        size=None,  # Any size (we'll validate dimensions)
                        max_results=5  # Get top 5 results
                    )
                    
                    # Convert generator to list
                    return list(results)
                
                except Exception as e:
                    logger.error(f"DDGS search error: {e}")
                    return []
            
            # Run search in thread pool to avoid blocking
            results = await loop.run_in_executor(None, search_images)
            
            if not results:
                logger.debug(f"DuckDuckGo returned no results for '{title}'")
                return None
            
            # Try each result until we find a valid image
            for i, result in enumerate(results):
                # v8.x returns dict with 'image' key for full image URL
                image_url = result.get('image')
                
                if not image_url:
                    continue
                
                # Validate image URL (check accessibility and content type)
                if await self._validate_image_url(image_url):
                    logger.debug(f"Valid image found at position {i+1}: {image_url[:50]}...")
                    return image_url
            
            logger.debug(f"No valid images found via DuckDuckGo for '{title}' (checked {len(results)} results)")
            return None
        
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed for '{title}': {e}")
            return None
    
    async def _validate_image_url(self, url: str) -> bool:
        """
        Quick validation that image URL is accessible.
        
        Args:
            url: Image URL to validate
        
        Returns:
            True if image is accessible, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # HEAD request to check without downloading
                response = await client.head(url, follow_redirects=True)
                
                # Check status code
                if response.status_code != 200:
                    return False
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                is_image = any(img_type in content_type for img_type in ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'])
                
                return is_image
        
        except httpx.TimeoutException:
            logger.debug(f"Timeout validating image: {url[:50]}...")
            return False
        except Exception as e:
            logger.debug(f"Error validating image {url[:50]}...: {e}")
            return False
    
    def _generate_placeholder(self, title: str, author: str) -> str:
        """
        Generate beautiful placeholder cover using free SVG generation service.
        
        Uses boringavatars.com which generates unique, colorful patterns
        based on the seed (title + author). Same book always gets same pattern.
        
        Returns:
            URL to generated SVG placeholder (always valid)
        """
        
        # Create unique seed from title and author
        seed = f"{title}{author}"
        
        # Color palette - pleasant blue gradient
        colors = '3b82f6,60a5fa,93c5fd,bfdbfe,dbeafe'
        
        # Alternative palettes based on category (if you want to customize):
        # category_colors = {
        #     'fiction': 'e63946,f1faee,a8dadc,457b9d,1d3557',
        #     'fantasy': '8b5cf6,a78bfa,c4b5fd,ddd6fe,ede9fe',
        #     'thriller': 'dc2626,ef4444,f87171,fca5a5,fee2e2',
        #     'romance': 'ec4899,f472b6,f9a8d4,fbcfe8,fce7f3',
        #     'classic': '78716c,a8a29e,d6d3d1,e7e5e4,f5f5f4',
        #     'science': '10b981,34d399,6ee7b7,a7f3d0,d1fae5',
        #     'default': '3b82f6,60a5fa,93c5fd,bfdbfe,dbeafe'
        # }
        
        # URL encode the seed
        encoded_seed = quote(seed)
        
        # Use boringavatars beam style (abstract, colorful pattern)
        placeholder_url = (
            f"https://source.boringavatars.com/beam/400/{encoded_seed}"
            f"?colors={colors}"
        )
        
        return placeholder_url
    
    async def prefetch_covers_batch(
        self,
        books: List[Dict[str, str]]
    ):
        """
        Prefetch covers for a batch of books (background task).
        
        With fallback strategy, this always succeeds (generates placeholder if needed).
        
        Args:
            books: List of dicts with book_id, title, author
        """
        logger.info(f"Prefetching covers for {len(books)} books")
        
        success_count = 0
        google_count = 0
        ddg_count = 0
        placeholder_count = 0
        
        for i, book in enumerate(books, 1):
            try:
                cover_url = await self.get_cover_url(
                    book_id=book['book_id'],
                    title=book['title'],
                    author=book['author']
                )
                
                # Count source type (optional, for statistics)
                if 'google' in cover_url or 'googleapis' in cover_url:
                    google_count += 1
                elif 'boringavatars' in cover_url:
                    placeholder_count += 1
                else:
                    ddg_count += 1
                
                success_count += 1
                
                # Log progress every 10 books
                if i % 10 == 0:
                    logger.info(
                        f"Progress: {i}/{len(books)} books "
                        f"(Google: {google_count}, DDG: {ddg_count}, Placeholder: {placeholder_count})"
                    )
                
                # Delay between requests
                await asyncio.sleep(self.RATE_LIMIT_DELAY)
            
            except Exception as e:
                logger.error(f"Failed to prefetch cover for {book.get('title')}: {e}")
                continue
        
        logger.info(
            f"Cover prefetching completed: {success_count}/{len(books)} successful\n"
            f"  - Google Books: {google_count}\n"
            f"  - DuckDuckGo: {ddg_count}\n"
            f"  - Placeholders: {placeholder_count}"
        )