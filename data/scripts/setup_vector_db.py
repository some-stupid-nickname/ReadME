"""
Vector Database Setup Script for Book Recommendation RAG System

This script:
1. Reads the cleaned books dataset
2. Creates embeddings using sentence-transformers
3. Stores the embeddings in Qdrant vector database
"""

import os
import pandas as pd
from typing import List, Dict
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VectorDBSetup:
    def __init__(
        self,
        excel_path: str = "../processed/book_data_prepared.xlsx",
        collection_name: str = "books",
        embedding_model: str = "all-MiniLM-L6-v2",
        qdrant_url: str = None,
        qdrant_api_key: str = None,
        batch_size: int = 100
    ):
        """
        Initialize the Vector DB Setup

        Args:
            csv_path: Path to the cleaned CSV file
            collection_name: Name of the Qdrant collection
            embedding_model: Sentence transformer model name
            qdrant_url: Qdrant server URL (default: local in-memory)
            qdrant_api_key: API key for Qdrant Cloud
            batch_size: Number of records to process at once
        """
        # Resolve path relative to script location if it's a relative path
        if not os.path.isabs(excel_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.excel_path = os.path.normpath(os.path.join(script_dir, excel_path))
        else:
            self.excel_path = excel_path
        self.collection_name = collection_name
        self.batch_size = batch_size

        # Initialize embedding model
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()

        # Initialize Qdrant client
        if qdrant_url:
            # Check if it's a local path (for persistent storage) or a URL
            if os.path.exists(qdrant_url) or not qdrant_url.startswith(('http://', 'https://')):
                print(f"Using persistent Qdrant storage at {qdrant_url}")
                self.client = QdrantClient(path=qdrant_url)
            else:
                print(f"Connecting to Qdrant at {qdrant_url}")
                self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            print("Using in-memory Qdrant instance")
            self.client = QdrantClient(":memory:")

    def load_data(self) -> pd.DataFrame:
        """Load the books dataset from CSV"""
        print(f"Loading data from {self.excel_path}")
        df = pd.read_excel(self.excel_path)
        print(f"Loaded {len(df)} books")
        print(f"Columns: {df.columns.tolist()}")
        return df

    def create_collection(self):
        """Create or recreate the Qdrant collection"""
        # Delete existing collection if it exists
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            print(f"Deleted existing collection: {self.collection_name}")
        except:
            pass

        # Create new collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.embedding_dim,
                distance=Distance.COSINE
            )
        )
        print(f"Created collection: {self.collection_name} with dimension {self.embedding_dim}")

    def prepare_text_for_embedding(self, row: pd.Series) -> str:
        """
        Prepare text from a book record for embedding

        Combines relevant fields into a single text string
        """
        # Common book dataset fields - adjust based on actual columns
        fields = []

        # Title and author are typically most important
        if 'title' in row and pd.notna(row['title']):
            fields.append(f"Title: {row['title']}")
        elif 'Title' in row and pd.notna(row['Title']):
            fields.append(f"Title: {row['Title']}")

        if 'author' in row and pd.notna(row['author']):
            fields.append(f"Author: {row['author']}")
        elif 'Author' in row and pd.notna(row['Author']):
            fields.append(f"Author: {row['Author']}")
        elif 'authors' in row and pd.notna(row['authors']):
            fields.append(f"Author: {row['authors']}")

        # Description/summary
        if 'description' in row and pd.notna(row['description']):
            fields.append(f"Description: {row['description']}")
        elif 'Description' in row and pd.notna(row['Description']):
            fields.append(f"Description: {row['Description']}")
        elif 'summary' in row and pd.notna(row['summary']):
            fields.append(f"Summary: {row['summary']}")

        # Genre/categories
        if 'genres' in row and pd.notna(row['genres']):
            fields.append(f"Genres: {row['genres']}")
        elif 'genre' in row and pd.notna(row['genre']):
            fields.append(f"Genre: {row['genre']}")
        elif 'categories' in row and pd.notna(row['categories']):
            fields.append(f"Categories: {row['categories']}")

        return " | ".join(fields)

    def embed_and_upload(self, df: pd.DataFrame):
        """
        Create embeddings for all books and upload to Qdrant
        """
        points = []

        print(f"\nProcessing {len(df)} books in batches of {self.batch_size}")

        for idx in tqdm(range(0, len(df), self.batch_size), desc="Embedding batches"):
            batch_df = df.iloc[idx:idx + self.batch_size]

            # Prepare texts for embedding
            texts = [self.prepare_text_for_embedding(row) for _, row in batch_df.iterrows()]

            # Create embeddings
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)

            # Create points for Qdrant
            for i, (_, row) in enumerate(batch_df.iterrows()):
                # Map Excel columns to expected database fields (matching database_service.py expectations)
                title = row.get('Title') or row.get('title') or 'Unknown'
                author = row.get('Authors') or row.get('author') or 'Unknown'
                description = row.get('Description') or row.get('description') or None
                genre = row.get('Category') or row.get('genre') or 'Unknown'
                publisher = row.get('Publisher') or None
                price = row.get('Price Starting With ($)') or 0.0
                pub_month = row.get('Publish Date (Month)') or None

                # Handle publication year/date with robust parsing
                pub_date = row.get('Publish Date (Year)') or row.get('publication_date')
                pub_year = None
                if pub_date and pd.notna(pub_date):
                    pub_date_str = str(pub_date)
                    # Extract year from date strings like '1945-08-17' or handle edge cases like '2000*'
                    if '-' in pub_date_str:
                        pub_year = int(pub_date_str.split('-')[0])
                    else:
                        # Remove any non-numeric characters (e.g., '2000*' -> '2000')
                        clean_year = ''.join(c for c in pub_date_str if c.isdigit())
                        if clean_year:
                            pub_year = int(clean_year)

                # Create payload with capitalized field names (matching Book model expectations)
                payload = {
                    'Title': title,
                    'Authors': author,
                    'Description': description,
                    'Category': genre,
                    'Publisher': publisher,
                    'Price Starting With ($)': price,
                    'Publish Date (Month)': pub_month,
                    'Publish Date (Year)': pub_year
                }

                point = PointStruct(
                    id=idx + i,
                    vector=embeddings[i].tolist(),
                    payload=payload
                )
                points.append(point)

            # Upload batch to Qdrant
            if len(points) >= self.batch_size:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                points = []

        # Upload remaining points
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

        print(f"\n✓ Successfully embedded and uploaded {len(df)} books to Qdrant")

    def verify_upload(self):
        """Verify that data was uploaded correctly"""
        collection_info = self.client.get_collection(collection_name=self.collection_name)
        print(f"\nCollection Info:")
        print(f"  Name: {collection_info.config.params.vectors.size}")
        print(f"  Points count: {collection_info.points_count}")
        print(f"  Vector dimension: {collection_info.config.params.vectors.size}")

    def run(self):
        """Execute the full pipeline"""
        print("=" * 60)
        print("Starting Vector Database Setup")
        print("=" * 60)

        # Load data
        df = self.load_data()

        # Create collection
        self.create_collection()

        # Embed and upload
        self.embed_and_upload(df)

        # Verify
        self.verify_upload()

        print("\n" + "=" * 60)
        print("Vector Database Setup Complete!")
        print("=" * 60)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Build vector database for book recommendations')
    parser.add_argument('--data', default='../processed/book_data_prepared.xlsx',
                      help='Path to Excel file with book data')
    parser.add_argument('--collection', default='books',
                      help='Name of the Qdrant collection')
    parser.add_argument('--qdrant-url', default=None,
                      help='Qdrant server URL or path for persistent storage')
    parser.add_argument('--batch-size', type=int, default=100,
                      help='Batch size for processing')

    args = parser.parse_args()

    # Default to persistent storage in backend/qdrant_storage if no URL specified
    qdrant_path = args.qdrant_url
    if not qdrant_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        qdrant_path = os.path.join(script_dir, "../../backend/qdrant_storage")
        qdrant_path = os.path.normpath(qdrant_path)

    # You can customize these parameters
    # Path will be resolved relative to script location
    setup = VectorDBSetup(
        excel_path=args.data if args.data else "../processed/book_data_prepared.xlsx",
        collection_name=args.collection,
        qdrant_url=qdrant_path,
        embedding_model="all-MiniLM-L6-v2",  # Fast and efficient model
        batch_size=args.batch_size
    )

    setup.run()


if __name__ == "__main__":
    main()
