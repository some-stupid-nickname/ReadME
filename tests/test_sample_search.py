"""
Quick test of the sample vector DB
"""

from test_vector_db import VectorDBTester

# Test the sample collection
tester = VectorDBTester(
    collection_name="books_sample",
    embedding_model="all-MiniLM-L6-v2"
)

tester.run_all_tests()
