"""
Quick test with a small sample of the dataset
"""

import pandas as pd
from setup_vector_db import VectorDBSetup

# Load just first 100 rows for quick testing
print("Loading sample of dataset...")
df = pd.read_csv("../data/processed/BooksDatasetClean.csv", nrows=100)

print(f"\nDataset sample loaded: {len(df)} rows")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst row:")
print(df.iloc[0])

# Save sample for testing
df.to_csv("../data/processed/BooksDatasetSample.csv", index=False)
print(f"\nSaved sample to BooksDatasetSample.csv")

# Run vector DB setup on sample
print("\n" + "="*60)
print("Running Vector DB setup on sample...")
print("="*60)

setup = VectorDBSetup(
    csv_path="../data/processed/BooksDatasetSample.csv",
    collection_name="books_sample",
    batch_size=10
)

setup.run()
