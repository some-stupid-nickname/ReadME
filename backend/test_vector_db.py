"""
Test script for Vector Database functionality

This script tests:
1. Connection to Qdrant
2. Searching for similar books
3. Retrieving book information
"""

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class VectorDBTester:
    def __init__(
        self,
        collection_name: str = "books",
        embedding_model: str = "all-MiniLM-L6-v2",
        qdrant_url: str = None
    ):
        """Initialize the tester"""
        print("Initializing Vector DB Tester...")

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize Qdrant client
        if qdrant_url:
            self.client = QdrantClient(url=qdrant_url)
        else:
            self.client = QdrantClient(":memory:")

        self.collection_name = collection_name

    def test_connection(self):
        """Test connection to Qdrant"""
        print("\n" + "=" * 60)
        print("TEST 1: Connection to Qdrant")
        print("=" * 60)

        try:
            collection_info = self.client.get_collection(collection_name=self.collection_name)
            print(f"✓ Successfully connected to collection: {self.collection_name}")
            print(f"  Points in collection: {collection_info.points_count}")
            print(f"  Vector dimension: {collection_info.config.params.vectors.size}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            return False

    def search_books(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for books similar to the query

        Args:
            query: Search query
            limit: Number of results to return

        Returns:
            List of search results
        """
        # Create embedding for the query
        query_vector = self.embedding_model.encode(query).tolist()

        # Search in Qdrant
        search_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit
        ).points

        return search_results

    def test_search(self):
        """Test search functionality with sample queries"""
        print("\n" + "=" * 60)
        print("TEST 2: Search Functionality")
        print("=" * 60)

        test_queries = [
            "fantasy book with magic and dragons",
            "mystery thriller detective novel",
            "romance love story",
            "science fiction space adventure",
            "historical fiction world war"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: '{query}'")
            print("-" * 60)

            try:
                results = self.search_books(query, limit=3)

                if not results:
                    print("  No results found")
                    continue

                for j, result in enumerate(results, 1):
                    score = result.score
                    payload = result.payload

                    # Try to extract title and author from payload
                    title = payload.get('title') or payload.get('Title') or 'Unknown Title'
                    author = payload.get('author') or payload.get('Author') or payload.get('authors') or 'Unknown Author'

                    print(f"  {j}. {title}")
                    print(f"     Author: {author}")
                    print(f"     Similarity Score: {score:.4f}")

            except Exception as e:
                print(f"  ✗ Search failed: {e}")

    def test_retrieval(self):
        """Test retrieving specific records by ID"""
        print("\n" + "=" * 60)
        print("TEST 3: Record Retrieval")
        print("=" * 60)

        try:
            # Retrieve first few records
            records = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[0, 1, 2]
            )

            print(f"Retrieved {len(records)} records:")
            for record in records:
                payload = record.payload
                title = payload.get('title') or payload.get('Title') or 'Unknown Title'
                print(f"  ID {record.id}: {title}")

            print("✓ Retrieval test passed")

        except Exception as e:
            print(f"✗ Retrieval test failed: {e}")

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 70)
        print(" VECTOR DATABASE TESTING SUITE")
        print("=" * 70)

        # Test 1: Connection
        if not self.test_connection():
            print("\n✗ Connection test failed. Aborting remaining tests.")
            return

        # Test 2: Search
        self.test_search()

        # Test 3: Retrieval
        self.test_retrieval()

        print("\n" + "=" * 70)
        print(" ALL TESTS COMPLETE")
        print("=" * 70)


def main():
    """Main entry point"""
    tester = VectorDBTester(
        collection_name="books",
        embedding_model="all-MiniLM-L6-v2"
    )

    tester.run_all_tests()


if __name__ == "__main__":
    main()
