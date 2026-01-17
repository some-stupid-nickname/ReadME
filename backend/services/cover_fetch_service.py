"""Service for fetching book covers with fallback strategy"""
import asyncio
from typing import Optional, List, Dict
from urllib.parse import quote
import httpx
from loguru import logger
from database.postgres_service import PostgresService

# New package name: ddgs (renamed from duckduckgo-search)
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
    logger.info("DuckDuckGo search (ddgs) is available")
except ImportError:
    try:
        # Fallback to old package name
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
        logger.warning("Using deprecated duckduckgo-search package. Please upgrade: pip install ddgs")
    except ImportError:
        DDGS_AVAILABLE = False
        logger.warning("DuckDuckGo search not installed. Install with: pip install ddgs")


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
        try:
            # 1. Check cache first
            cached = await self.pg_db.get_cover_url(book_id)
            if cached is not None:
                logger.debug(f"Cache hit for '{title}'")
                return cached
            
            # 2. Try Google Books API
            logger.debug(f"Trying Google Books for '{title}' by {author}")
            cover_url = await self._fetch_from_google_books(title, author)
            if cover_url:
                await self.pg_db.cache_cover_url(
                    book_id=book_id,
                    cover_url=cover_url,
                    source='google_books'
                )
                logger.info(f"✓ Google Books: {title}")
                return cover_url
            
            logger.debug(f"Google Books failed for '{title}', trying DuckDuckGo...")
            
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
                logger.info(f"✓ DuckDuckGo: {title}")
                return cover_url
            
            logger.debug(f"DuckDuckGo failed for '{title}', generating placeholder...")
            
            # 4. Generate placeholder (always works)
            placeholder_url = self._generate_placeholder(title, author)
            await self.pg_db.cache_cover_url(
                book_id=book_id,
                cover_url=placeholder_url,
                source='generated'
            )
            logger.info(f"→ Placeholder: {title}")
            return placeholder_url
        
        except Exception as e:
            # If anything goes wrong, always return a placeholder
            logger.error(f"Unexpected error in get_cover_url for '{title}': {e}", exc_info=True)
            placeholder_url = self._generate_placeholder(title, author)
            # Try to cache it, but don't fail if caching fails
            try:
                await self.pg_db.cache_cover_url(
                    book_id=book_id,
                    cover_url=placeholder_url,
                    source='generated'
                )
            except Exception as cache_error:
                logger.debug(f"Failed to cache placeholder for {book_id}: {cache_error}")
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
                
                logger.debug(f"No cover in Google Books response for '{title}'")
                return None
        
        except httpx.HTTPStatusError as e:
            logger.debug(f"Google Books HTTP {e.response.status_code} for '{title}'")
            return None
        except httpx.RequestError as e:
            logger.debug(f"Google Books network error for '{title}': {e}")
            return None
        except Exception as e:
            logger.warning(f"Google Books unexpected error for '{title}': {e}")
            return None
    
    async def _fetch_from_duckduckgo(self, title: str, author: str) -> Optional[str]:
        """
        Fetch cover URL from DuckDuckGo Images.
        Works in Russia, no API key needed, no strict rate limits.
        
        Returns:
            Cover URL or None if not found
        """
        
        if not DDGS_AVAILABLE:
            logger.debug("DuckDuckGo search library not available")
            return None
        
        try:
            # Construct search query
            # Clean author name - take only first author
            first_author = author.split(',')[0].strip() if author else ""
            query = f'"{title}" "{first_author}" book cover'
            
            logger.debug(f"DuckDuckGo query: {query}")
            
            # DDGS is synchronous, run in executor
            loop = asyncio.get_event_loop()
            
            def search_images():
                """Synchronous search function to run in executor"""
                try:
                    logger.debug(f"Creating DDGS instance for '{title}'")
                    ddgs = DDGS()
                    
                    logger.debug(f"Searching images for '{title}'...")
                    # Search images with current API
                    results = ddgs.images(
                        keywords=query,
                        region='wt-wt',  # Worldwide
                        safesearch='off',
                        max_results=5
                    )
                    
                    # Convert generator to list
                    results_list = list(results)
                    logger.debug(f"DuckDuckGo returned {len(results_list)} results for '{title}'")
                    return results_list
                
                except Exception as e:
                    logger.error(f"DDGS search error for '{title}': {e}", exc_info=True)
                    return []
            
            # Run search in thread pool to avoid blocking
            results = await loop.run_in_executor(None, search_images)
            
            if not results:
                logger.debug(f"DuckDuckGo: no results for '{title}'")
                return None
            
            # Try each result until we find a valid image
            for i, result in enumerate(results):
                # Get image URL from result
                image_url = result.get('image')
                
                if not image_url:
                    logger.debug(f"Result {i+1} has no 'image' key")
                    continue
                
                logger.debug(f"Validating image {i+1}/{len(results)}: {image_url[:60]}...")
                
                # Validate image URL (check accessibility)
                if await self._validate_image_url(image_url):
                    logger.info(f"Valid image found for '{title}' at position {i+1}")
                    return image_url
                else:
                    logger.debug(f"Image {i+1} validation failed")
            
            logger.debug(f"No valid images found in {len(results)} DuckDuckGo results for '{title}'")
            return None
        
        except Exception as e:
            logger.error(f"DuckDuckGo fetch failed for '{title}': {e}", exc_info=True)
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
                    logger.debug(f"Image validation failed: HTTP {response.status_code}")
                    return False
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                is_image = any(img_type in content_type for img_type in ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/'])
                
                if not is_image:
                    logger.debug(f"Image validation failed: content-type is {content_type}")
                    return False
                
                return True
        
        except httpx.TimeoutException:
            logger.debug(f"Image validation timeout for: {url[:50]}...")
            return False
        except Exception as e:
            logger.debug(f"Image validation error for {url[:50]}...: {e}")
            return False
    
    def _generate_placeholder(self, title: str, author: str) -> str:
        """
        Generate beautiful placeholder cover using free SVG generation service.
        
        Uses DiceBear API (api.dicebear.com) which generates unique, colorful patterns
        based on the seed (title + author). Same book always gets same pattern.
        
        Returns:
            URL to generated SVG placeholder (always valid)
        """
        
        # Create unique seed from title and author
        seed = f"{title}{author}"
        
        # URL encode the seed
        encoded_seed = quote(seed)
        
        # Use DiceBear shapes style (abstract, colorful geometric pattern)
        # Style 'shapes' creates unique abstract patterns suitable for book covers
        placeholder_url = (
            f"https://api.dicebear.com/7.x/shapes/svg"
            f"?seed={encoded_seed}&size=400"
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
        logger.info(f"Starting prefetch for {len(books)} books")
        
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
                
                # Count source type (for statistics)
                if 'google' in cover_url or 'googleapis' in cover_url:
                    google_count += 1
                elif 'dicebear' in cover_url or 'boringavatars' in cover_url:
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
            f"Prefetch complete: {success_count}/{len(books)} successful\n"
            f"  - Google Books: {google_count}\n"
            f"  - DuckDuckGo: {ddg_count}\n"
            f"  - Placeholders: {placeholder_count}"
        )