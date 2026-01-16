"""HTTP client for FastAPI backend"""
import httpx
from typing import Optional
from pydantic import BaseModel, Field
from config import BACKEND_API_URL


class BookInfo(BaseModel):
    """Book information from API"""
    id: str
    title: str
    author: str
    genres: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    source_link: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response from API"""
    response: str
    books: list[BookInfo] = Field(default_factory=list)
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

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.post(
                    url,
                    json={"query": query},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                data = response.json()
                return SearchResponse(**data)

        except httpx.TimeoutException:
            raise Exception("Request timeout: Backend API is not responding")
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
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

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.post(
                    url,
                    json={"query": query},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                data = response.json()
                return ClarificationResponse(**data)

        except httpx.TimeoutException:
            raise Exception("Request timeout: Backend API is not responding")
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
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
                response.raise_for_status()

                data = response.json()
                return SearchResponse(**data)

        except httpx.TimeoutException:
            raise Exception("Request timeout: Backend API is not responding")
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
