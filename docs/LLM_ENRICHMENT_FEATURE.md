# LLM Query Enrichment Feature

## Overview

The LLM Query Enrichment feature uses Mistral AI to detect vague user queries and ask clarifying questions to improve book recommendation quality. When a user makes a brief or unclear request like "a book" or "what to read", the system automatically generates friendly questions to understand their preferences better.

## How It Works

### 1. **Vagueness Detection**
The system analyzes incoming queries using:
- Quick heuristic checks (query length, common vague phrases)
- LLM-based analysis for borderline cases
- Genre and topic detection

**Vague queries:**
- "a book"
- "what to read"
- "recommend"
- "something interesting"

**Clear queries:**
- "mystery about doctors"
- "sci-fi about space"
- "something like War and Peace"
- "light romantic comedy"

### 2. **Clarifying Questions Generation**
For vague queries, Mistral generates 2-3 friendly questions about:
- Genre preferences (mystery, sci-fi, romance, etc.)
- Mood/tone (light, serious, funny, dramatic)
- Themes or topics of interest
- Favorite authors or books

Example questions:
```
Let me help you find the perfect book! 📚

1. What genre are you in the mood for? (mystery, sci-fi, romance, literary fiction?)
2. What's the vibe? Something light and fun or something more serious?
3. Any favorite authors or books you've enjoyed recently?
```

### 3. **Query Enrichment**
User responses are combined with the original query using LLM to create an enriched search query:
- Original: "a book"
- User context: "mystery, something light"
- Enriched: "light mystery"

### 4. **Enhanced Search**
The enriched query is used for book recommendations, resulting in more relevant results.

## API Endpoints

### POST `/api/search/clarify`
Check if a query needs clarification and get questions.

**Request:**
```json
{
  "query": "a book"
}
```

**Response:**
```json
{
  "is_vague": true,
  "clarifying_questions": "Let me help you find...",
  "original_query": "a book"
}
```

### POST `/api/search/enriched`
Search with enriched query (original + user context).

**Request:**
```json
{
  "original_query": "a book",
  "user_context": "mystery, something light"
}
```

**Response:**
```json
{
  "response": "LLM recommendation text...",
  "books": [...],
  "message_id": null
}
```

## Telegram Bot Flow

### Normal Flow (Clear Query)
1. User: "mystery about doctors"
2. Bot: [Direct book recommendations]

### Clarification Flow (Vague Query)
1. User: "a book"
2. Bot: "Let me help you find the perfect book! 📚\n1. What genre?.."
3. User: "mystery, something light"
4. Bot: [Book recommendations based on enriched query]

## Implementation Details

### Backend Components

**`QueryEnrichmentService`** (`backend/services/query_enrichment_service.py`)
- `is_query_vague(query: str) -> bool` - Detect vague queries
- `generate_clarifying_questions(query: str) -> str` - Generate questions
- `enrich_query_with_context(original: str, context: str) -> str` - Enrich query

**API Routes** (`backend/api/routes/search.py`)
- `/api/search/clarify` - Vagueness check + question generation
- `/api/search/enriched` - Enriched search endpoint

**Schemas** (`backend/models/schemas.py`)
- `ClarificationRequest`
- `ClarificationResponse`
- `EnrichedSearchRequest`

### Telegram Bot Components

**State Management** (`telegram-bot/state.py`)
- `awaiting_clarification: bool` - Clarification state flag
- `original_vague_query: str` - Store original query
- `clarification_questions: str` - Store generated questions

**Handlers** (`telegram-bot/handlers/search.py`)
- `handle_search()` - Main handler with clarification logic
- `handle_clarification_response()` - Process user's clarification answers

**API Client** (`telegram-bot/utils/api_client.py`)
- `clarify_query()` - Call clarification endpoint
- `enriched_search()` - Call enriched search endpoint

## Configuration

No additional configuration required. The feature uses the existing `MISTRAL_API_KEY` from your `.env` file.

## Testing

### Test Vague Queries
```bash
# Using curl
curl -X POST http://localhost:8000/api/search/clarify \
  -H "Content-Type: application/json" \
  -d '{"query": "a book"}'
```

### Test Enriched Search
```bash
curl -X POST http://localhost:8000/api/search/enriched \
  -H "Content-Type: application/json" \
  -d '{
    "original_query": "a book",
    "user_context": "mystery, light, contemporary"
  }'
```

### Telegram Bot Testing
1. Start bot: `/start`
2. Send vague query: "a book"
3. Bot should ask clarifying questions
4. Reply with preferences: "mystery, something light"
5. Bot should provide relevant recommendations

## Benefits

1. **Better Recommendations** - More context leads to more relevant book suggestions
2. **User Engagement** - Interactive conversation feels more natural
3. **Reduced Frustration** - Users don't need to guess what format to use
4. **Learning Opportunity** - Users learn what information helps get better results

## Future Enhancements

- Multi-turn clarification (follow-up questions)
- Remember user preferences across sessions
- Suggest popular genres/topics based on trends
- Language detection and bilingual support
- Personalized question generation based on user history
