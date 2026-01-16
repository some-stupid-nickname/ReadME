"""Message formatter for Telegram"""
import re
from typing import Optional
from utils.api_client import BookInfo


def format_intro_message(intro_text: str) -> str:
    """
    Format introduction message from LLM
    
    Args:
        intro_text: Introduction text from LLM
        
    Returns:
        Formatted message for Telegram
    """
    if not intro_text:
        return "Here's a selection of books for you:"
    
    # Clean up the text
    text = intro_text.strip()
    
    # Ensure it ends with punctuation
    if text and text[-1] not in '.!?':
        text += "."
    
    return text


def format_book_message(
    book: BookInfo,
    recommendation_text: str,
    current: int,
    total: int
) -> str:
    """
    Format book information message for Telegram
    
    Args:
        book: Book information
        recommendation_text: LLM recommendation text for this book
        current: Current book index (1-based)
        total: Total number of books
        
    Returns:
        Formatted message string
    """
    lines = []
    
    # Title
    lines.append(f"📚 <b>{escape_html(book.title)}</b>")
    
    # Author
    if book.author and book.author.strip() and book.author.strip() != "By":
        author = book.author.strip()
        if author.startswith("By "):
            author = author[3:].strip()
        lines.append(f"👤 Author: {escape_html(author)}")
    else:
        lines.append("👤 Author: Not specified")
    
    # Genres
    if book.genres and len(book.genres) > 0:
        genres_str = ", ".join(book.genres)
        lines.append(f"🏷️ Genres: {escape_html(genres_str)}")
    else:
        lines.append("🏷️ Genres: Not specified")
    
    # Description
    lines.append("")  # Empty line
    if book.description:
        # Truncate long descriptions
        desc = book.description
        if len(desc) > 500:
            desc = desc[:500] + "..."
        lines.append(f"📖 <i>{escape_html(desc)}</i>")
    else:
        lines.append("📖 <i>No description available</i>")
    
    # Recommendation
    if recommendation_text:
        lines.append("")  # Empty line
        lines.append("💬 <b>Recommendation:</b>")
        # Clean and format recommendation
        rec_clean = recommendation_text.strip()
        # Remove leading quotes if present
        rec_clean = re.sub(r'^[«"]\s*', '', rec_clean)
        rec_clean = re.sub(r'\s*[»"]\s*$', '', rec_clean)
        lines.append(escape_html(rec_clean))
    
    # Page indicator
    lines.append("")  # Empty line
    lines.append(f"📄 Book {current} of {total}")
    
    return "\n".join(lines)


def escape_html(text: str) -> str:
    """
    Escape HTML special characters for Telegram
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    if not text:
        return ""
    
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))
