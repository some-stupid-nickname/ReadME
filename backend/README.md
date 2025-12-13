# Backend - Vector Database Setup

This directory contains the backend components for the RAG-based book recommendation system.

## Vector Database Setup

### Prerequisites

1. Python 3.10+
2. Virtual environment (already configured in project root)

### Installation

Install required packages:

```bash
pip install -r requirements.txt
```

### Running the Vector Database Setup

The setup script will:
1. Load the cleaned books dataset from CSV
2. Generate embeddings using sentence-transformers
3. Store embeddings in Qdrant vector database

#### Option 1: In-memory Qdrant (for testing)

```bash
python setup_vector_db.py
```

This uses an in-memory Qdrant instance. Data will be lost when the script exits.

#### Option 2: Persistent Qdrant (recommended)

First, start Qdrant using Docker:

```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

Then run the setup script with Qdrant URL:

```bash
# Edit .env file first
cp .env.example .env
# Update QDRANT_URL in .env

python setup_vector_db.py
```

### Testing the Vector Database

After setup, test the functionality:

```bash
python test_vector_db.py
```

This will:
- Verify connection to Qdrant
- Test semantic search with sample queries
- Test record retrieval

### Scripts

- `setup_vector_db.py` - Main script to embed and upload books to Qdrant
- `test_vector_db.py` - Test script to verify vector DB functionality
- `inspect_data.py` - Utility to inspect the dataset structure

### Configuration

Key parameters in `setup_vector_db.py`:

- `csv_path`: Path to the cleaned CSV file
- `collection_name`: Name of the Qdrant collection (default: "books")
- `embedding_model`: Sentence-transformers model (default: "all-MiniLM-L6-v2")
- `batch_size`: Number of records to process at once (default: 100)

### Embedding Model

We use `all-MiniLM-L6-v2` by default:
- Fast and efficient
- 384-dimensional embeddings
- Good balance between speed and quality

Alternative models you can try:
- `all-mpnet-base-v2` - Higher quality, slower
- `multi-qa-MiniLM-L6-cos-v1` - Optimized for Q&A
- `paraphrase-multilingual-MiniLM-L12-v2` - Multilingual support

### RAG System Evaluation

We use an LLM-as-Judge approach to evaluate recommendation quality:

```bash
# Evaluate with Mistral (free tier)
python evaluate_rag.py --queries-file test_queries.json --provider mistral --top-k 5 --output results.json

# Evaluate with OpenAI (paid, faster)
python evaluate_rag.py --queries-file test_queries.json --provider openai --top-k 5 --output results.json
```

**Evaluation metrics:**
- Average relevance score (0-5 scale)
- Top-1 quality (first recommendation accuracy)
- Top-3 average (first 3 recommendations)
- Success rate (% of successful API calls)

**Test queries:**
- `test_queries.json` - 20 diverse queries across genres
- `test_queries_small.json` - 5 queries for quick testing

See `EVALUATION.md` for detailed documentation.

**Results:**
- Mistral: 3.13/5 average (100% success with rate limiting)
- OpenAI: 2.81/5 average (100% success, no delays needed)
- Best categories: Non-fiction (3.70/5), Specialized (3.38/5)
- Weakest: Fiction (2.33/5) - generic descriptions hurt matching

### Troubleshooting

**Large dataset loading issues:**
- Adjust `batch_size` parameter
- Use chunked reading with pandas

**Memory issues:**
- Reduce batch_size
- Use a smaller embedding model
- Process dataset in chunks

**Qdrant connection errors:**
- Verify Qdrant is running: `curl http://localhost:6333`
- Check QDRANT_URL in .env file

**Mistral rate limits:**
- Free tier: ~30 requests before hitting limits
- Script automatically adds 2-second delays
- Failed judgments are excluded from metrics
