"""Database service for loading books from SQLite"""
import sqlite3
import pickle
import numpy as np
from typing import List
from models.book import Book


class BookDatabase:
    """Класс для работы с базой данных"""
    def __init__(self, db_path: str = "books.sqlite"):
        self.db_path = db_path
        self.books: List[Book] = []
        self.vectors: np.ndarray = None
        self._load_database()

    def _load_database(self):
        """Загрузка данных из SQLite базы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, point FROM points")
        rows = cursor.fetchall()
        conn.close()

        vectors_list = []

        for row in rows:
            point_data = pickle.loads(row[1])

            # Извлечение данных 
            point_id = point_data.id
            vector = list(point_data.vector)
            payload = point_data.payload

            book = Book(
                id=point_id,
                title=payload.get('Title', 'Unknown'),
                authors=payload.get('Authors', 'Unknown'),
                description=payload.get('Description'),
                category=payload.get('Category', 'Unknown'),
                publisher=payload.get('Publisher', 'Unknown'),
                price=payload.get('Price Starting With ($)', 0.0),
                publish_month=payload.get('Publish Date (Month)', 'Unknown'),
                publish_year=payload.get('Publish Date (Year)', 0),
                vector=np.array(vector)
            )

            self.books.append(book)
            vectors_list.append(np.array(vector))

        self.vectors = np.array(vectors_list)

