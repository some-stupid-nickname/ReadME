"""Quick script to inspect the books dataset structure."""

import pandas as pd

# Read the CSV file
df = pd.read_csv('../data/processed/BooksDatasetClean.csv')

# Display basic information
print("Dataset Shape:", df.shape)
print("\nColumn Names:")
print(df.columns.tolist())
print("\nFirst few rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nNull values:")
print(df.isnull().sum())
