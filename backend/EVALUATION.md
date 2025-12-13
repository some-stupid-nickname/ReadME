# LLM-as-Judge Evaluation System

This system uses Large Language Models (LLMs) to automatically evaluate the quality of book recommendations from the RAG system.

## Supported LLM Providers

### Mistral AI (Default - Free Tier Available!)

Mistral offers a **free tier** for their API, making it ideal for development and testing.

**Getting Started:**
1. Sign up at [https://console.mistral.ai/](https://console.mistral.ai/)
2. Create a free API key
3. Add to `backend/.env`:
   ```
   MISTRAL_API_KEY=your_mistral_key_here
   ```

**Available Models:**
- `mistral-small-latest` (default, free tier) - Best balance of quality and cost
- `mistral-medium-latest` - Higher quality, costs apply
- `mistral-large-latest` - Best quality, higher costs

### OpenAI (Alternative)

OpenAI offers more powerful models but requires payment.

**Setup:**
1. Get API key from [https://platform.openai.com/](https://platform.openai.com/)
2. Add to `backend/.env`:
   ```
   OPENAI_API_KEY=your_openai_key_here
   ```

**Available Models:**
- `gpt-4o-mini` (recommended) - Good quality, lower cost (~$0.15/1M tokens)
- `gpt-4o` - Higher quality, higher cost
- `gpt-3.5-turbo` - Fastest, cheapest

## Installation

```bash
cd backend
pip install mistralai openai  # Install both or just the one you need
```

Or install from requirements:
```bash
pip install -r requirements.txt
```

## Usage

### Test Your Setup

```bash
python test_mistral.py  # Check if Mistral is configured
```

### Evaluate a Single Query

**With Mistral (free):**
```bash
python evaluate_rag.py --query "fantasy books with magic" --provider mistral --top-k 5
```

**With OpenAI:**
```bash
python evaluate_rag.py --query "mystery thriller novels" --provider openai --top-k 5
```

### Batch Evaluation

Evaluate multiple queries from a file:

```bash
# With Mistral
python evaluate_rag.py --queries-file test_queries.json --provider mistral --output results.json

# With OpenAI
python evaluate_rag.py --queries-file test_queries.json --provider openai --output results.json
```

### Custom Models

```bash
# Use a specific Mistral model
python evaluate_rag.py --query "sci-fi space opera" --provider mistral --model mistral-medium-latest

# Use a specific OpenAI model
python evaluate_rag.py --query "historical fiction" --provider openai --model gpt-4o
```

## Command-Line Options

```
--query TEXT              Single query to evaluate
--queries-file PATH       JSON file with multiple queries (default: test_queries.json)
--top-k INT              Number of recommendations to evaluate (default: 5)
--provider {mistral,openai}  LLM provider to use (default: mistral)
--model TEXT             Specific model to use (optional)
--output PATH            Save results to JSON file
```

## Evaluation Metrics

The system provides:

1. **Per-Recommendation Scores** (0-5):
   - 0: Completely irrelevant
   - 1: Slightly related
   - 2: Somewhat related
   - 3: Moderately relevant
   - 4: Highly relevant
   - 5: Perfect match

2. **Aggregate Metrics**:
   - Average relevance across all recommendations
   - Top-1 relevance (quality of best recommendation)
   - Top-3 average (quality of top 3 recommendations)

3. **Reasoning**: Each score includes an explanation from the LLM judge

## Example Output

```
================================================================================
QUERY: fantasy books with magic
================================================================================
Searching for books... Found 5 results
Evaluating with Mistral (mistral-small-latest)...

Rank 1 | Score: 5/5 | Retrieval: 0.892
  Title: Harry Potter and the Sorcerer's Stone
  Author: J.K. Rowling
  Reasoning: Perfect match - classic fantasy with extensive magic system

Rank 2 | Score: 5/5 | Retrieval: 0.876
  Title: The Name of the Wind
  Author: Patrick Rothfuss
  Reasoning: Excellent fantasy novel centered on learning magic

...

METRICS:
  Average relevance: 4.60/5
  Top-1 relevance: 5.00/5
  Top-3 average: 4.67/5
```

## Test Queries

The `test_queries.json` file contains 20 diverse test queries across genres:
- Fantasy & Magic
- Mystery & Thriller
- Romance
- Business & Self-help
- Science Fiction
- Historical Fiction
- And more...

## Cost Comparison

**Mistral (Free Tier):**
- ✅ Free for limited usage
- ✅ Great for development and testing
- ✅ Good quality for most use cases
- Limits may apply for heavy usage

**OpenAI:**
- 💰 Pay-as-you-go pricing
- GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- Higher quality for complex evaluations
- Better for production at scale

## Tips

1. **Start with Mistral**: Use the free tier to develop and test your system
2. **Batch Evaluations**: More efficient than individual queries
3. **Save Results**: Use `--output` to save and analyze results later
4. **Monitor Costs**: Check your API usage regularly
5. **Quality vs Speed**: Smaller models are faster but may be less accurate

## Troubleshooting

**"API key required" error:**
- Check that your `.env` file exists and contains the correct key
- Verify the key format (no extra quotes or spaces)
- Make sure you're in the `backend/` directory

**Import errors:**
- Install required packages: `pip install mistralai openai`
- Check that you're using the correct Python environment

**No results found:**
- Ensure `qdrant_storage/` directory exists with the books collection
- Run `setup_vector_db.py` if the database hasn't been created yet
