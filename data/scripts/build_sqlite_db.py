"""Build SQLite database with embeddings from Excel file

This script builds a vector database for the book recommendation system.
It reads book data from Excel, generates embeddings using sentence-transformers,
and stores everything in SQLite with pickled PointStruct objects.

Usage:
    # Build with 1000 books (default, for testing)
    python build_sqlite_db.py
    
    # Build with custom number of books
    python build_sqlite_db.py --max-books 5000
    
    # Build full database with all ~174k books
    python build_sqlite_db.py --full
    
    # Custom output location
    python build_sqlite_db.py --output /path/to/output.sqlite

Requirements:
    - book_data_prepared.xlsx must exist in data/processed/
    - Run with: PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python build_sqlite_db.py

Note:
    - Full database (~174k books) takes ~10-15 minutes and creates ~1.5GB file
    - Test database (1000 books) takes ~30 seconds and creates ~8MB file
"""
import os
import sys
import sqlite3
import pickle
import pandas as pd
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct

# Add backend to path for importing models
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, os.path.join(project_root, 'backend'))


def build_database(
    excel_path: str,
    output_db_path: str,
    max_books: int = None,
    embedding_model: str = "all-MiniLM-L6-v2"
):
    """
    Build SQLite database with book embeddings from Excel file

    Args:
        excel_path: Path to Excel file with book data
        output_db_path: Path for output SQLite database
        max_books: Maximum number of books to process (None = all)
        embedding_model: Sentence transformer model name
    """
    print(f"Loading embedding model: {embedding_model}")
    model = SentenceTransformer(embedding_model)

    print(f"Loading data from {excel_path}")
    df = pd.read_excel(excel_path)
    print(f"Loaded {len(df)} books")
    print(f"Columns: {df.columns.tolist()}")

    if max_books:
        df = df.head(max_books)
        print(f"Processing first {max_books} books")

    # Create SQLite database
    print(f"\nCreating database at {output_db_path}")
    if os.path.exists(output_db_path):
        os.remove(output_db_path)
        print(f"Removed existing database")

    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()

    # Create points table
    cursor.execute("""
        CREATE TABLE points (
            id INTEGER PRIMARY KEY,
            point BLOB
        )
    """)

    print("\nGenerating embeddings and inserting into database...")
    batch_size = 100

    for idx in tqdm(range(0, len(df), batch_size), desc="Processing batches"):
        batch_df = df.iloc[idx:idx + batch_size]

        # Create text for embedding
        texts = []
        for _, row in batch_df.iterrows():
            title = row.get('title', 'Unknown')
            author = row.get('author', 'Unknown')
            description = row.get('description', '')
            genre = row.get('genre', 'Unknown')

            # Combine fields for embedding
            text = f"{title} by {author}. {description} Genre: {genre}"
            texts.append(text)

        # Generate embeddings
        embeddings = model.encode(texts, show_progress_bar=False)

        # Insert into database
        for i, (_, row) in enumerate(batch_df.iterrows()):
            # Map Excel columns to expected database fields (matching database_service.py expectations)
            title = row['title'] if pd.notna(row['title']) else 'Unknown'
            author = row['author'] if pd.notna(row['author']) else 'Unknown'
            description = row['description'] if pd.notna(row['description']) else ''
            genre = row['genre'] if pd.notna(row['genre']) else 'Unknown'
            pub_date = row['publication_date'] if pd.notna(row['publication_date']) else None
            
            payload = {
                'Title': title,
                'Authors': author,
                'Description': description,
                'Category': genre,
                'Publisher': None,
                'Price Starting With ($)': 0.0,
                'Publish Date (Month)': None,
                'Publish Date (Year)': pub_date
            }

            # Remove NaN values
            payload = {k: (v if pd.notna(v) else None) for k, v in payload.items()}

            # Create PointStruct
            point = PointStruct(
                id=idx + i + 1,
                vector=embeddings[i].tolist(),
                payload=payload
            )

            # Pickle and insert
            point_blob = pickle.dumps(point)
            cursor.execute("INSERT INTO points (id, point) VALUES (?, ?)",
                         (idx + i + 1, point_blob))

        conn.commit()

    conn.close()

    # Verify
    print(f"\n✓ Database created successfully!")
    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(*) FROM points").fetchone()[0]
    print(f"  Total books: {count}")

    # Show sample
    sample = cursor.execute("SELECT id, point FROM points LIMIT 1").fetchone()
    if sample:
        point = pickle.loads(sample[1])
        print(f"\n  Sample book:")
        print(f"    ID: {point.id}")
        print(f"    Title: {point.payload.get('title')}")
        print(f"    Author: {point.payload.get('author')}")
        print(f"    Genre: {point.payload.get('genre')}")

    conn.close()

    db_size_mb = os.path.getsize(output_db_path) / (1024 * 1024)
    print(f"  Database size: {db_size_mb:.1f} MB")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Build SQLite database with book embeddings')
    parser.add_argument('--max-books', type=int, default=1000,
                      help='Maximum number of books to process (default: 1000, use 0 for all books)')
    parser.add_argument('--output', type=str, default=None,
                      help='Output database path (default: frontend/books.sqlite)')
    parser.add_argument('--full', action='store_true',
                      help='Build full database with all books (same as --max-books 0)')
    
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))

    excel_path = os.path.join(project_root, "data", "processed", "book_data_prepared.xlsx")
    
    if args.output:
        output_db_path = args.output if os.path.isabs(args.output) else os.path.join(project_root, args.output)
    else:
        output_db_path = os.path.join(project_root, "frontend", "books.sqlite")
    
    # Determine max_books
    max_books = None if (args.full or args.max_books == 0) else args.max_books
    
    if max_books:
        print(f"Building database with first {max_books} books...")
    else:
        print("Building FULL database with all books (this will take a while)...")
    
    build_database(
        excel_path=excel_path,
        output_db_path=output_db_path,
        max_books=max_books,
        embedding_model="all-MiniLM-L6-v2"
    )

    print("\n" + "="*60)
    print("Database ready at:", output_db_path)
    print("="*60)
    print("\nUsage examples:")
    print("  python build_sqlite_db.py                    # Build with 1000 books (default)")
    print("  python build_sqlite_db.py --max-books 5000   # Build with 5000 books")
    print("  python build_sqlite_db.py --full             # Build with ALL books (~174k)")
    print("  python build_sqlite_db.py --max-books 0      # Same as --full")


if __name__ == "__main__":
    main()
