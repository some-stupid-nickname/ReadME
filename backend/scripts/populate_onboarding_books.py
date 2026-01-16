"""
Script to populate onboarding_books table with real book IDs from SQLite.

This script searches for specific books in the SQLite database and updates
the PostgreSQL onboarding_books table with actual book IDs.

Usage:
    python backend/scripts/populate_onboarding_books.py
"""
import asyncio
import sqlite3
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.postgres_service import postgres_db


# Books to search for (title keywords, author keywords)
ONBOARDING_BOOKS = [
    # Classic (4 books)
    ("War and Peace", "Tolstoy"),
    ("1984", "Orwell"),
    ("Pride and Prejudice", "Austen"),
    ("Master and Margarita", "Bulgakov"),
    
    # Fantasy (4 books)
    ("Harry Potter", "Rowling"),
    ("Lord of the Rings", "Tolkien"),
    ("Hitchhiker", "Adams"),
    ("Dune", "Herbert"),
    
    # Thriller (4 books)
    ("Girl with the Dragon Tattoo", "Larsson"),
    ("Murder on the Orient Express", "Christie"),
    ("Silence of the Lambs", "Harris"),
    ("Sherlock Holmes", "Doyle"),
    
    # Modern (4 books)
    ("Little Life", "Yanagihara"),
    ("Three Comrades", "Remarque"),
    ("Hundred Years of Solitude", "Márquez"),
    ("Norwegian Wood", "Murakami"),
]


async def find_and_populate():
    """Main function to find books and populate onboarding table."""
    
    print("=" * 60)
    print("Populating Onboarding Books")
    print("=" * 60)
    
    # Connect to databases
    sqlite_path = backend_dir.parent / "data" / "storage.sqlite"
    if not sqlite_path.exists():
        print(f"ERROR: SQLite database not found at {sqlite_path}")
        return
    
    print(f"SQLite database: {sqlite_path}")
    
    sqlite_conn = sqlite3.connect(str(sqlite_path))
    cursor = sqlite_conn.cursor()
    
    await postgres_db.connect()
    print("PostgreSQL connected")
    
    # Clear existing onboarding books
    await postgres_db.execute("DELETE FROM onboarding_books")
    print("Cleared existing onboarding books")
    
    # Search and insert
    categories = ['classic', 'fantasy', 'thriller', 'modern']
    category_idx = 0
    display_order = 1
    found_count = 0
    
    for title_part, author_part in ONBOARDING_BOOKS:
        # Search in SQLite (using LIKE for fuzzy matching)
        cursor.execute("""
            SELECT id, point
            FROM points
            LIMIT 1000
        """)
        
        rows = cursor.fetchall()
        
        book_found = False
        for row in rows:
            try:
                import pickle
                point_data = pickle.loads(row[1])
                payload = point_data.payload
                
                title = payload.get('Title', '')
                authors = payload.get('Authors', '')
                
                # Check if title and author match
                if (title_part.lower() in title.lower() and 
                    author_part.lower() in authors.lower()):
                    
                    book_id = point_data.id
                    first_author = authors.split(',')[0].strip()
                    category = categories[category_idx // 4]
                    
                    # Insert into PostgreSQL
                    await postgres_db.execute("""
                        INSERT INTO onboarding_books 
                        (book_id, category, display_order, title, author)
                        VALUES ($1, $2, $3, $4, $5)
                    """, book_id, category, display_order, title, first_author)
                    
                    print(f"✓ [{category}] {title} by {first_author}")
                    
                    book_found = True
                    found_count += 1
                    display_order += 1
                    if display_order > 4:
                        display_order = 1
                        category_idx += 1
                    break
            
            except Exception as e:
                continue
        
        if not book_found:
            print(f"✗ NOT FOUND: {title_part} by {author_part}")
    
    sqlite_conn.close()
    await postgres_db.disconnect()
    
    print("=" * 60)
    print(f"Completed: {found_count}/{len(ONBOARDING_BOOKS)} books found")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(find_and_populate())
