"""Book data model"""
import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class Book:
    """Book information storage"""
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

    def to_text(self) -> str:
        """Convert to text description"""
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

