"""Helper service for reading book data from SQLite database"""
import sqlite3
import pickle
from typing import Optional, Dict, Any, List
import numpy as np
from loguru import logger
import re


def _parse_publish_year(value: Any) -> Optional[int]:
    """Parse publish year from various formats (int, 'YYYY', 'YYYY-MM-DD', etc.)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        try:
            return int(value)
        except Exception:
            return None
    if isinstance(value, str):
        v = value.strip()
        if not v or v.lower() == "unknown":
            return None
        # Accept 'YYYY-MM-DD' or any string starting with a 4-digit year
        m = re.match(r"^(\d{4})", v)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
        try:
            return int(v)
        except Exception:
            return None
    return None


_MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def _parse_publish_month(value: Any) -> Optional[int]:
    """Parse publish month from various formats (int, '10', 'October', 'YYYY-MM-DD', etc.)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 1 <= value <= 12 else None
    if isinstance(value, float):
        try:
            i = int(value)
            return i if 1 <= i <= 12 else None
        except Exception:
            return None
    if isinstance(value, str):
        v = value.strip()
        if not v or v.lower() == "unknown":
            return None
        # 'YYYY-MM-DD'
        m = re.match(r"^\d{4}[-/](\d{1,2})[-/]\d{1,2}", v)
        if m:
            try:
                i = int(m.group(1))
                return i if 1 <= i <= 12 else None
            except Exception:
                return None
        # numeric month
        if v.isdigit():
            try:
                i = int(v)
                return i if 1 <= i <= 12 else None
            except Exception:
                return None
        # month name
        key = v.lower()
        return _MONTHS.get(key) or _MONTHS.get(key[:3])
    return None


class SQLiteBookService:
    """
    Service for reading book data from SQLite storage.sqlite database.
    READ-ONLY operations - never writes to SQLite.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        else:
            from core.config import get_books_db_path
            self.db_path = get_books_db_path()
        self._encoder = None
        self._books_cache: Dict[str, Dict[str, Any]] = {}  # Cache: numeric_id -> book_data
        self._cache_loaded = False
    
    def _get_encoder(self):
        """Lazy load and cache the encoder"""
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            # Use same model as vector search, force CPU in Docker
            self._encoder = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        return self._encoder
    
    def _load_cache(self):
        """Load all books into cache for fast lookup by numeric ID"""
        if self._cache_loaded and len(self._books_cache) > 0:
            return  # Already loaded
        
        # Prevent concurrent loading
        if hasattr(self, '_loading') and self._loading:
            return
        self._loading = True
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT point FROM points")
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                point_data = pickle.loads(row[0])
                payload = point_data.payload
                
                # Use numeric ID from point_data, not table ID
                numeric_id = str(point_data.id)
                
                publish_year = _parse_publish_year(payload.get('Publish Date (Year)'))
                publish_month = _parse_publish_month(payload.get('Publish Date (Month)'))
                if publish_month is None and isinstance(payload.get('Publish Date (Year)'), str):
                    publish_month = _parse_publish_month(payload.get('Publish Date (Year)'))
                
                self._books_cache[numeric_id] = {
                    'book_id': numeric_id,
                    'title': payload.get('Title', 'Unknown'),
                    'authors': payload.get('Authors', 'Unknown'),
                    'category': payload.get('Category', 'Unknown'),
                    'description': payload.get('Description', ''),
                    'publish_year': publish_year,
                    'publish_month': publish_month,
                    'embedding': np.array(point_data.vector) if hasattr(point_data, 'vector') else None
                }
            
            self._cache_loaded = True
            self._loading = False
            logger.info(f"SQLiteBookService: cached {len(self._books_cache)} books")
        
        except Exception as e:
            self._loading = False
            logger.error(f"Error loading books cache: {e}")
    
    def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """
        Get book details by book_id from SQLite.
        
        Returns:
            Dict with book data or None if not found
            Fields: book_id, title, authors, category, description, 
                    publish_year, publish_month, embedding
        """
        # Ensure cache is loaded
        self._load_cache()
        
        # Lookup by numeric ID
        return self._books_cache.get(str(book_id))
    
    def get_books_by_ids(self, book_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple books by IDs.
        
        Returns:
            List of book dicts (only books that exist)
        """
        books = []
        for book_id in book_ids:
            book = self.get_book_by_id(book_id)
            if book:
                books.append(book)
        return books
    
    def get_embedding(self, book_id: str) -> Optional[np.ndarray]:
        """
        Get book embedding vector by book_id.
        Used for preference vector calculation.
        
        Returns:
            numpy array (384,) or None if not found
        """
        book = self.get_book_by_id(book_id)
        if book and book['embedding'] is not None:
            return book['embedding']
        return None
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text using same model as books (all-MiniLM-L6-v2).
        Used for query similarity calculation.
        
        Returns:
            numpy array (384,)
        """
        try:
            encoder = self._get_encoder()
            embedding = encoder.encode([text])[0]
            
            # Normalize to unit vector
            embedding = embedding / (np.linalg.norm(embedding) + 1e-10)
            
            return embedding
        
        except Exception as e:
            from loguru import logger
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(384, dtype=np.float32)


# Global instance
sqlite_book_service = SQLiteBookService()
