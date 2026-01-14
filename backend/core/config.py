"""Configuration settings for the application"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Mistral API
    mistral_api_key: Optional[str] = None
    
    # Database paths
    books_db_path: Optional[str] = None
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    
    # CORS settings
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_file_required = False
        extra = "ignore"  # Игнорировать дополнительные поля из .env
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
    
    # Try to find books.sqlite in common locations
    project_root = Path(__file__).parent.parent.parent
    
    # Check in frontend/ directory (where console_interface.py is)
    frontend_path = project_root / "frontend" / "books.sqlite"
    if frontend_path.exists():
        return str(frontend_path)
    
    # Check in backend/ directory
    backend_path = project_root / "backend" / "books.sqlite"
    if backend_path.exists():
        return str(backend_path)
    
    # Check in project root
    root_path = project_root / "books.sqlite"
    if root_path.exists():
        return str(root_path)
    
    # Default fallback
    return str(frontend_path)


# Global settings instance
settings = Settings()

