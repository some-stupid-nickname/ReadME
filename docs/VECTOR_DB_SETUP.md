# Vector Database Setup Guide

This document describes the vector database implementation for the RAG-based book recommendation system.

## Overview

The vector database stores book embeddings that enable semantic search. Users can find books similar to their queries even when they don't use exact keywords.

### Architecture

```
CSV Dataset → Embedding Model → Vector Database (Qdrant)
                    ↓
            Semantic Search & RAG Pipeline
```

## Components

### 1. Embedding Model

- **Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Dimensions**: 384
- **Speed**: ~14k sentences/second
- **Quality**: Optimized for semantic similarity

### 2. Vector Database

- **Database**: Qdrant
- **Distance Metric**: Cosine similarity
- **Collection**: `books`

### 3. Data Processing

The setup script processes the books CSV by:
1. Loading the cleaned dataset
2. Creating text representations (title + author + description + genre)
3. Generating embeddings for each book
4. Uploading to Qdrant in batches

## Setup Instructions

### Prerequisites

- Python 3.10+
- Virtual environment activated
- Cleaned books dataset in `data/processed/BooksDatasetClean.csv`

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env if using remote Qdrant
```

### Step 3: Choose Deployment Mode

#### Option A: In-Memory (Development/Testing)

```bash
python setup_vector_db.py
```

**Pros**: No additional setup
**Cons**: Data is lost when script exits

#### Option B: Docker Qdrant (Recommended)

Start Qdrant:
```bash
docker run -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

Update `.env`:
```
QDRANT_URL=http://localhost:6333
```

Run setup:
```bash
python setup_vector_db.py
```

**Pros**: Persistent storage, production-ready
**Cons**: Requires Docker

#### Option C: Qdrant Cloud

1. Create account at https://cloud.qdrant.io
2. Create a cluster
3. Get API key and URL
4. Update `.env`:
```
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
```

Run setup:
```bash
python setup_vector_db.py
```

**Pros**: Managed service, scalable
**Cons**: Costs money for large datasets

### Step 4: Run Setup

```bash
python setup_vector_db.py
```

Expected output:
```
============================================================
Starting Vector Database Setup
============================================================
Loading embedding model: all-MiniLM-L6-v2
Loading data from ../data/processed/BooksDatasetClean.csv
Loaded XXXXX books
...
✓ Successfully embedded and uploaded XXXXX books to Qdrant
============================================================
Vector Database Setup Complete!
============================================================
```

### Step 5: Verify Setup

```bash
python test_vector_db.py
```

This runs several tests:
1. Connection to Qdrant
2. Semantic search with sample queries
3. Record retrieval by ID

## Usage Examples

### Basic Search

```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Initialize
client = QdrantClient(":memory:")  # or your Qdrant URL
model = SentenceTransformer('all-MiniLM-L6-v2')

# Search
query = "fantasy book with magic"
query_vector = model.encode(query).tolist()

results = client.search(
    collection_name="books",
    query_vector=query_vector,
    limit=5
)

for result in results:
    print(f"{result.payload['title']} - Score: {result.score}")
```

### Advanced Search with Filters

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Search with genre filter
results = client.search(
    collection_name="books",
    query_vector=query_vector,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="genre",
                match=MatchValue(value="Fantasy")
            )
        ]
    ),
    limit=5
)
```

## Monitoring

### Check Collection Status

```bash
curl http://localhost:6333/collections/books
```

### View Collection Info

```python
from qdrant_client import QdrantClient

client = QdrantClient("http://localhost:6333")
info = client.get_collection("books")
print(f"Points: {info.points_count}")
print(f"Vectors: {info.config.params.vectors.size}")
```

## Troubleshooting

### Issue: Out of Memory

**Solution**: Reduce batch size in `setup_vector_db.py`:
```python
setup = VectorDBSetup(batch_size=50)  # Default is 100
```

### Issue: Slow Embedding

**Solution**:
- Use GPU if available (automatically detected)
- Use smaller model: `paraphrase-MiniLM-L3-v2`
- Process in chunks

### Issue: Qdrant Connection Failed

**Solution**:
1. Check if Qdrant is running: `curl http://localhost:6333`
2. Verify URL in `.env`
3. Check firewall/network settings

### Issue: Dataset Too Large

**Solution**: Process in chunks:
```python
# Modify setup_vector_db.py
df = pd.read_csv(csv_path, chunksize=10000)
for chunk in df:
    setup.embed_and_upload(chunk)
```

## Performance

### Metrics (estimated for typical dataset)

| Dataset Size | Embedding Time | Upload Time | Total Time |
|-------------|----------------|-------------|------------|
| 1,000 books | ~30s           | ~5s         | ~35s       |
| 10,000 books| ~5min          | ~30s        | ~5.5min    |
| 100,000 books| ~50min        | ~5min       | ~55min     |

*Times are approximate and depend on hardware*

### Optimization Tips

1. **Use GPU**: 10-50x faster embedding
2. **Batch Processing**: Larger batches (100-500) are more efficient
3. **Parallel Processing**: Embed multiple batches concurrently
4. **Index Optimization**: Configure Qdrant HNSW parameters

## Next Steps

1. ✅ Vector database setup complete
2. 🔄 Integrate with LangChain RAG pipeline
3. 🔄 Build FastAPI endpoints
4. 🔄 Add query rewriting
5. 🔄 Implement reranking
6. 🔄 Add caching layer

## References

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Sentence Transformers](https://www.sbert.net/)
- [Vector Search Best Practices](https://qdrant.tech/documentation/guides/optimization/)
