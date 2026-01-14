"""Book data model"""
import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class Book:
    """Хранение информации о книге"""
    id: int
    title: str
    authors: str
    description: Optional[str]
    category: Optional[str]
    publisher: Optional[str]
    price: float
    publish_month: Optional[str]
    publish_year: int
    vector: np.ndarray

    def to_text(self, lang: str = "ru") -> str:
        """Преобразование в текстовое описание
        
        Args:
            lang: Язык вывода ('ru' или 'en')
        """
        if lang == "en":
            # English version for RAGAS evaluation
            desc = f"Description: {self.description}" if self.description else ""
            category = self.category.strip() if self.category else "Unknown"
            publisher = self.publisher if self.publisher else "Unknown"
            return f"""Title: {self.title}
Author(s): {self.authors}
Category: {category}
Publisher: {publisher}
Price: ${self.price:.2f}
Publication Date: {self.publish_month or 'N/A'} {self.publish_year}
{desc}""".strip()
        else:
            # Russian version (default)
            desc = f"Описание: {self.description}" if self.description else ""
            category = self.category.strip() if self.category else "Без категории"
            publisher = self.publisher if self.publisher else "Неизвестно"
            return f"""Название: {self.title}
Автор(ы): {self.authors}
Категория: {category}
Издательство: {publisher}
Цена: ${self.price:.2f}
Дата публикации: {self.publish_month or 'N/A'} {self.publish_year}
{desc}""".strip()

