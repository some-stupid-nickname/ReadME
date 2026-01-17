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
    """Get path to books.sqlite database file"""
    settings = Settings()
    
    # If explicitly set in env, use it
    if settings.books_db_path:
        return settings.books_db_path
    
    # Try to find books.sqlite or storage.sqlite in common locations
    project_root = Path(__file__).parent.parent.parent
    
    # 1. Check in data/ directory (primary location for storage.sqlite)
    data_storage_path = project_root / "data" / "storage.sqlite"
    if data_storage_path.exists():
        return str(data_storage_path)
    
    # 2. Check in data/ directory for books.sqlite
    data_books_path = project_root / "data" / "books.sqlite"
    if data_books_path.exists():
        return str(data_books_path)
    
    # 3. Check in backend/ directory
    backend_path = project_root / "backend" / "books.sqlite"
    if backend_path.exists():
        return str(backend_path)
        
    # 4. Check in frontend/ directory (where console_interface.py is)
    frontend_path = project_root / "frontend" / "books.sqlite"
    if frontend_path.exists():
        return str(frontend_path)
    
    # 5. Check in project root
    root_path = project_root / "books.sqlite"
    if root_path.exists():
        return str(root_path)
    
    # Default fallback
    return str(data_storage_path)


# Global settings instance
settings = Settings()

