"""Helper service for reading book data from SQLite database"""
import sqlite3
import pickle
from typing import Optional, Dict, Any, List
import numpy as np
from loguru import logger


class SQLiteBookService:
    """
    Service for reading book data from SQLite storage.sqlite database.
    READ-ONLY operations - never writes to SQLite.
    """
    
    def __init__(self, db_path: str = "data/storage.sqlite"):
        self.db_path = db_path
    
    def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """
        Get book details by book_id from SQLite.
        
        Returns:
            Dict with book data or None if not found
            Fields: book_id, title, authors, category, description, 
                    publish_year, publish_month, embedding
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query by id from points table
            cursor.execute("SELECT id, point FROM points WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Deserialize point data
            point_data = pickle.loads(row[1])
            payload = point_data.payload
            
            # Extract fields according to ACTUAL schema
            return {
                'book_id': point_data.id,
                'title': payload.get('Title', 'Unknown'),
                'authors': payload.get('Authors', 'Unknown'),  # Comma-separated list
                'category': payload.get('Category', 'Unknown'),  # Single category
                'description': payload.get('Description', ''),
                'publish_year': payload.get('Publish Date (Year)'),
                'publish_month': payload.get('Publish Date (Month)'),
                'embedding': np.array(point_data.vector) if hasattr(point_data, 'vector') else None
            }
        
        except Exception as e:
            logger.error(f"Error fetching book {book_id} from SQLite: {e}")
            return None
    
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
            from sentence_transformers import SentenceTransformer
            
            # Use same model as vector search
            encoder = SentenceTransformer("all-MiniLM-L6-v2")
            embedding = encoder.encode([text])[0]
            
            # Normalize to unit vector
            embedding = embedding / (np.linalg.norm(embedding) + 1e-10)
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(384, dtype=np.float32)


# Global instance
sqlite_book_service = SQLiteBookService()
