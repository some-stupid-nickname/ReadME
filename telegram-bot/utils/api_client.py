"""HTTP client for FastAPI backend"""
import httpx
import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from config import BACKEND_API_URL

logger = logging.getLogger(__name__)


class BookInfo(BaseModel):
    """Book information from API"""
    id: str
    title: str
    author: str
    genres: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    cover_url: Optional[str] = None
    source_link: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response from API"""
    response: str
    books: List[BookInfo] = Field(default_factory=list)
    message_id: Optional[int] = None


class ClarificationResponse(BaseModel):
    """Clarification response from API"""
    is_vague: bool
    clarifying_questions: Optional[str] = None
    original_query: str


class APIClient:
    """HTTP client for interacting with FastAPI backend"""

    def __init__(self, base_url: str = BACKEND_API_URL):
        self.base_url = base_url.rstrip('/')
        # Increased timeout for slow backend responses (RAG processing can take time)
        self.timeout = httpx.Timeout(320.0, connect=10.0)  # 120s total, 10s connect

    async def search_books(self, query: str) -> SearchResponse:
        """
        Search for books using the backend API

        Args:
            query: Search query string

        Returns:
            SearchResponse with books and LLM response

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If response is invalid
        """
        url = f"{self.base_url}/api/search"
        logger.debug(f"Search request to {url} with query: '{query[:50]}...'")

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.post(
                    url,
                    json={"query": query},
                    headers={"Content-Type": "application/json"}
                )
                logger.debug(f"Search response status: {response.status_code}")
                response.raise_for_status()

                data = response.json()
                logger.debug(f"Search response data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                # Validate response structure matches our schema
                try:
                    result = SearchResponse(**data)
                    logger.info(f"Search successful, found {len(result.books)} books")
                    return result
                except Exception as validation_error:
                    logger.error(f"Search response validation failed: {validation_error}, data: {data}")
                    raise Exception(f"Invalid API response format: {str(validation_error)}")

        except httpx.TimeoutException as e:
            logger.error(f"Search request timeout: {e}")
            raise Exception("Request timeout: Backend API is not responding")
        except httpx.HTTPStatusError as e:
            error_text = e.response.text[:500] if e.response.text else "No error details"
            logger.error(
                f"Search API HTTP error {e.response.status_code}: {error_text}, "
                f"URL: {url}, query: '{query[:50]}...'"
            )
            raise Exception(f"API error: {e.response.status_code} - {error_text}")
        except httpx.RequestError as e:
            logger.error(f"Search request error: {e}, URL: {url}")
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected search error: {e}", exc_info=True)
            raise Exception(f"Unexpected error: {str(e)}")

    async def clarify_query(self, query: str) -> ClarificationResponse:
        """
        Check if a query is vague and get clarifying questions

        Args:
            query: Search query string

        Returns:
            ClarificationResponse with vagueness status and questions

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/api/search/clarify"
        logger.debug(f"Clarify request to {url} with query: '{query[:50]}...'")

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.post(
                    url,
                    json={"query": query},
                    headers={"Content-Type": "application/json"}
                )
                logger.debug(f"Clarify response status: {response.status_code}")
                response.raise_for_status()

                data = response.json()
                logger.debug(f"Clarify response: is_vague={data.get('is_vague')}")
                # Validate response structure matches our schema
                try:
                    return ClarificationResponse(**data)
                except Exception as validation_error:
                    logger.error(f"Clarify response validation failed: {validation_error}, data: {data}")
                    raise Exception(f"Invalid API response format: {str(validation_error)}")

        except httpx.TimeoutException as e:
            logger.error(f"Clarify request timeout: {e}")
            raise Exception("Request timeout: Backend API is not responding")
        except httpx.HTTPStatusError as e:
            error_text = e.response.text[:500] if e.response.text else "No error details"
            logger.error(
                f"Clarify API HTTP error {e.response.status_code}: {error_text}, "
                f"URL: {url}, query: '{query[:50]}...'"
            )
            raise Exception(f"API error: {e.response.status_code} - {error_text}")
        except httpx.RequestError as e:
            logger.error(f"Clarify request error: {e}, URL: {url}")
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected clarify error: {e}", exc_info=True)
            raise Exception(f"Unexpected error: {str(e)}")

    async def enriched_search(self, original_query: str, user_context: str) -> SearchResponse:
        """
        Search with enriched query (original + context)

        Args:
            original_query: User's original query
            user_context: Additional context from user

        Returns:
            SearchResponse with books and LLM response

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/api/search/enriched"
        logger.debug(
            f"Enriched search request to {url}: "
            f"original='{original_query[:30]}...', context='{user_context[:30]}...'"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.post(
                    url,
                    json={
                        "original_query": original_query,
                        "user_context": user_context
                    },
                    headers={"Content-Type": "application/json"}
                )
                logger.debug(f"Enriched search response status: {response.status_code}")
                response.raise_for_status()

                data = response.json()
                logger.debug(f"Enriched search response data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                # Validate response structure matches our schema
                try:
                    result = SearchResponse(**data)
                    logger.info(f"Enriched search successful, found {len(result.books)} books")
                    return result
                except Exception as validation_error:
                    logger.error(f"Enriched search response validation failed: {validation_error}, data: {data}")
                    raise Exception(f"Invalid API response format: {str(validation_error)}")

        except httpx.TimeoutException as e:
            logger.error(f"Enriched search request timeout: {e}")
            raise Exception("Request timeout: Backend API is not responding")
        except httpx.HTTPStatusError as e:
            error_text = e.response.text[:500] if e.response.text else "No error details"
            logger.error(
                f"Enriched search API HTTP error {e.response.status_code}: {error_text}, "
                f"URL: {url}, original_query: '{original_query[:30]}...', "
                f"user_context: '{user_context[:30]}...'"
            )
            raise Exception(f"API error: {e.response.status_code} - {error_text}")
        except httpx.RequestError as e:
            logger.error(f"Enriched search request error: {e}, URL: {url}")
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected enriched search error: {e}", exc_info=True)
            raise Exception(f"Unexpected error: {str(e)}")
