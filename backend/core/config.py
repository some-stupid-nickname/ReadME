"""Configuration settings for the application"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Mistral API
    mistral_api_key: Optional[str] = None
    
    # Google Books API (Optional)
    google_books_api_key: Optional[str] = None
    
    # Database paths
    books_db_path: Optional[str] = None
    
    # PostgreSQL settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "rag_user"
    postgres_password: str = "rag_password"
    postgres_db: str = "rag_db"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    
    # CORS settings
    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_file_required=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Sanitization: strip quotes from API keys if present
        if self.mistral_api_key:
            self.mistral_api_key = self.mistral_api_key.strip("'\"")
        if self.google_books_api_key:
            self.google_books_api_key = self.google_books_api_key.strip("'\"")
            
        # Проверка обязательных полей после загрузки
        if not self.mistral_api_key:
            raise ValueError(
                "MISTRAL_API_KEY is required. "
                "Please set it in environment variable or .env file. "
                "Create .env file in backend/ or project root with: MISTRAL_API_KEY=your_key"
            )


def get_books_db_path() -> str:
    """Get path to books database file"""
    settings = Settings()
    
    # If explicitly set in env, use it
    if settings.books_db_path:
        return settings.books_db_path
    
    project_root = Path(__file__).parent.parent.parent
    
    # Priority: storage.sqlite (full 174k dataset) over books.sqlite (subset)
    # 1. Check for storage.sqlite in project root (FULL dataset)
    storage_path = project_root / "storage.sqlite"
    if storage_path.exists() and storage_path.stat().st_size > 100_000_000:  # >100MB = full DB
        return str(storage_path)
    
    # 2. Check in project root for books.sqlite
    root_books_path = project_root / "books.sqlite"
    if root_books_path.exists() and root_books_path.stat().st_size > 1000:
        return str(root_books_path)
    
    # 3. Check in data/ directory
    data_books_path = project_root / "data" / "books.sqlite"
    if data_books_path.exists() and data_books_path.stat().st_size > 1000:
        return str(data_books_path)
    
    # 4. Check in backend/ directory
    backend_path = project_root / "backend" / "books.sqlite"
    if backend_path.exists() and backend_path.stat().st_size > 1000:
        return str(backend_path)
    
    # Default fallback
    return str(root_books_path)


# Global settings instance
settings = Settings()

