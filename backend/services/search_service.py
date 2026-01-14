"""Vector search service for semantic book search"""
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from services.database_service import BookDatabase


class VectorSearchEngine:
    """Векторный поиск"""

    def __init__(self, book_db: BookDatabase, model_name: str = "all-MiniLM-L6-v2"):
        self.book_db = book_db
        self.encoder = SentenceTransformer(model_name)

        # Нормализация векторов
        self.normalized_vectors = self._normalize_vectors(book_db.vectors)

    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """Нормализация"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / (norms + 1e-10)

    def search(self, query: str, top_k: int = 5, category_filter: str = None) -> List[tuple]:
        """Поиск книг по запросу"""
        # Кодирование
        query_vector = self.encoder.encode([query])[0]
        query_vector = query_vector / (np.linalg.norm(query_vector) + 1e-10)

        similarities = np.dot(self.normalized_vectors, query_vector)

        if category_filter:
            mask = np.array([
                category_filter.lower() in (b.category.lower() if b.category else '')
                for b in self.book_db.books
            ])
            similarities = np.where(mask, similarities, -np.inf)

        # Топ-k результатов
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if similarities[idx] > -np.inf:
                results.append((self.book_db.books[idx], float(similarities[idx])))

        return results

