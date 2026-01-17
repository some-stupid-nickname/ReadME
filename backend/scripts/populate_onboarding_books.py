"""
Script to populate onboarding_books table with curated popular books.

Usage:
    python backend/scripts/populate_onboarding_books.py
"""
import asyncio
import sqlite3
import pickle
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.postgres_service import postgres_db


# Curated list of famous books by category (using IDs from storage.sqlite - 174k books)
# Original selection from first version, with verified IDs
FAMOUS_BOOKS = {
    'classic': [
        # Классика
        (376, "War and Peace", "Leo Tolstoy"),
        (1, "Animal Farm", "George Orwell"),
        (63, "Pride and Prejudice", "Jane Austen"),
        (771, "The Master and Margarita", "Mikhail Bulgakov"),
    ],
    'fantasy': [
        # Фэнтези и Sci-Fi
        (140, "Harry Potter and the Philosopher's Stone", "J. K. Rowling"),
        (74, "The Lord of the Rings", "J. R. R. Tolkien"),
        (1026, "The Hitchhiker's Guide to the Galaxy", "Douglas Adams"),
        (21, "Children of Dune", "Frank Herbert"),
    ],
    'thriller': [
        # Триллер и Детектив
        (10502, "The Girl with the Dragon Tattoo", "Stieg Larsson"),
        (425, "Murder on the Orient Express", "Agatha Christie"),
        (5214, "The Silence of the Lambs", "Thomas Harris"),
        (38652, "Mysteries of Sherlock Holmes", "Arthur Conan Doyle"),
    ],
    'modern': [
        # Современная литература
        (719, "Three Comrades", "Erich Maria Remarque"),
        (1293, "One Hundred Years of Solitude", "Gabriel García Márquez"),
        (96131, "Norwegian Wood", "Haruki Murakami"),
        (78, "The Shining", "Stephen King"),
    ],
}


async def find_and_populate():
    """Main function to populate onboarding table with curated famous books."""
    
    print("=" * 60)
    print("Populating Onboarding Books with Famous Titles")
    print("=" * 60)
    
    # Find SQLite database to verify books exist
    possible_paths = [
        backend_dir.parent / "storage.sqlite",
        backend_dir.parent / "data" / "storage.sqlite",
        backend_dir / "storage.sqlite",
    ]
    sqlite_path = None
    for p in possible_paths:
        if p.exists():
            sqlite_path = p
            break
    
    if not sqlite_path:
        print(f"ERROR: SQLite database not found in any of: {possible_paths}")
        return
    
    print(f"SQLite database: {sqlite_path}")
    
    # Verify books exist in SQLite
    sqlite_conn = sqlite3.connect(str(sqlite_path))
    cursor = sqlite_conn.cursor()
    
    # Build lookup of all book IDs
    cursor.execute("SELECT id, point FROM points")
    existing_ids = set()
    for row in cursor.fetchall():
        point_data = pickle.loads(row[1])
        existing_ids.add(point_data.id)
    
    print(f"Loaded {len(existing_ids)} book IDs from SQLite")
    
    await postgres_db.connect()
    print("PostgreSQL connected")
    
    # Clear existing onboarding books
    await postgres_db.execute("DELETE FROM onboarding_books")
    print("Cleared existing onboarding books")
    
    # Insert curated books
    total_inserted = 0
    
    for category, books in FAMOUS_BOOKS.items():
        print(f"\n{category.upper()}:")
        display_order = 1
        
        for book_id, title, author in books:
            if book_id not in existing_ids:
                print(f"  ✗ [{book_id}] {title} — NOT FOUND")
                continue
            
            await postgres_db.execute("""
                INSERT INTO onboarding_books 
                (book_id, category, display_order, title, author)
                VALUES ($1, $2, $3, $4, $5)
            """, str(book_id), category, display_order, title, author)
            
            print(f"  ✓ [{book_id}] {title}")
            display_order += 1
            total_inserted += 1
    
    sqlite_conn.close()
    await postgres_db.disconnect()
    
    print("\n" + "=" * 60)
    print(f"Completed: {total_inserted} famous books inserted")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(find_and_populate())
