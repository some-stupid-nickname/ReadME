"""Configuration settings for Telegram bot"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Try multiple locations: current dir, telegram-bot dir, project root
env_paths = [
    Path(__file__).parent / ".env",  # telegram-bot/.env
    Path.cwd() / ".env",  # Current working directory
    Path(__file__).parent.parent / ".env",  # Project root
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break
else:
    # If no .env found, try loading from current directory anyway
    load_dotenv(override=False)

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TELEGRAM_BOT_TOKEN:
    TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN.strip("'\"")

# Backend API URL
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# Maximum books per page (always 1 for navigation)
MAX_BOOKS_PER_PAGE = 1

# Validate required settings
if not TELEGRAM_BOT_TOKEN:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN is required. "
        "Please set it in environment variable or .env file. "
        f"Looked for .env in: {[str(p) for p in env_paths]}"
    )

