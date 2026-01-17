"""Query enrichment service for detecting vague queries and generating clarifying questions"""
from typing import Optional, List
from mistralai import Mistral


class QueryEnrichmentService:
    """Service for analyzing user queries and generating clarifying questions"""

    VAGUENESS_DETECTION_PROMPT = """You are a query analyzer for a BOOK recommendation service.
Your task is to determine if a user's query is specific enough to recommend BOOKS.

IMPORTANT: This is a BOOK recommendation system. Users are looking for books to read, not video games, movies, or other media.

CRITERIA FOR INSUFFICIENT SPECIFICITY (VAGUE):
1. Query is too short (1-3 words without context)
2. Query is too general: "a book", "recommend something", "what to read"
3. No mention of genre, theme, or mood
4. No information about user preferences
5. Single word that could refer to books OR other media (e.g., "games", "sports", "travel")

CRITERIA FOR SUFFICIENT SPECIFICITY (CLEAR - does NOT need clarification):
1. Specific book genre mentioned: mystery, sci-fi, romance, thriller
2. Book theme mentioned: about animals, about war, about love, space exploration
3. Mood mentioned: something light, serious, funny, dark
4. Author or specific book mentioned for finding similar books
5. Preferences specified: short stories, classics, contemporary literature

User query: "{query}"

Respond with ONLY one word:
- "VAGUE" - if the query is not specific enough and needs clarifying questions
- "CLEAR" - if the query is specific enough for book recommendations

Your answer:"""

    CLARIFICATION_GENERATION_PROMPT = """You are Alex, a friendly librarian helping someone find BOOKS to read. The user asked: "{query}"

This query is too general. Your task is to ask 2-3 friendly clarifying questions to better understand what BOOKS they're looking for RELATED TO THEIR QUERY.

IMPORTANT:
1. You are recommending BOOKS (literature to read), not video games, movies, podcasts, or other media
2. Your questions MUST be relevant to their query topic (e.g., if they said "games", ask about books about games, game design, gaming culture, etc.)
3. If their query is ambiguous, acknowledge their interest and ask what kind of BOOKS about that topic they want

RULES:
1. Speak warmly and casually, like a friend
2. Reference their query topic in your questions
3. Ask 2-3 short questions (each on a new line)
4. Focus on: genre, mood, theme, type of book about their topic
5. DO NOT use markdown (no **, ##, ``)
6. Use emojis for friendliness (but moderately)
7. Number the questions for convenience

Examples:
Query: "games"
"I can help you find great books about games! 📚

1. What aspect interests you? (Game design, gaming history, esports, specific games like chess or poker?)
2. Fiction or non-fiction? (Novels set in gaming worlds, or books about game development?)
3. What level? (Beginner guides, advanced strategy, or cultural analysis?)"

Query: "a book"
"Let me help you find the perfect book! 📚

1. What genre are you in the mood for? (mystery, sci-fi, romance, literary fiction?)
2. What's the vibe? Something light and fun or something more serious?
3. Any favorite authors or books you've enjoyed recently?"

Your clarifying questions:"""

    CONTEXT_INTEGRATION_PROMPT = """You are a helper for enriching BOOK search queries.

Original query: "{original_query}"
Additional context from user: "{user_context}"

Your task is to combine the original query and additional context into ONE clear search query for finding BOOKS.

IMPORTANT: This is for searching BOOKS (literature to read), not video games, movies, or other media.

RULES:
1. Preserve all important details from both texts
2. Remove filler words like "I want", "I need"
3. Make the query as specific as possible for finding books
4. Include genre, theme, mood - everything that's there
5. If the topic is ambiguous (e.g., "games"), add "books about" to clarify
6. DO NOT add anything on your own beyond necessary clarification
7. Respond with ONLY the final query, no explanations

Examples:
- Original: "a book", Context: "mystery, something light" → "light mystery"
- Original: "what to read", Context: "sci-fi about space" → "sci-fi about space"
- Original: "recommend", Context: "classics, Russian literature, about war" → "Russian classics about war"
- Original: "games", Context: "strategy, history" → "books about strategy games and history"

Final enriched query:"""

    def __init__(self, api_key: str, model: str = "mistral-small-latest"):
        """Initialize query enrichment service"""
        self.client = Mistral(api_key=api_key)
        self.model = model

    async def is_query_vague(self, query: str) -> bool:
        """
        Determine if a query is too vague and needs clarification

        Args:
            query: User's search query

        Returns:
            True if query is vague, False if it's clear enough
        """
        if not query or len(query.strip()) == 0:
            return True

        # Quick heuristic checks before calling LLM
        query_lower = query.lower().strip()

        # Very short queries (1-2 words) are likely vague unless they're specific genres
        words = query_lower.split()
        if len(words) <= 2:
            # Check if it's a specific genre or author
            specific_terms = [
                'mystery', 'thriller', 'horror', 'romance', 'fantasy',
                'sci-fi', 'science fiction', 'classics', 'poetry', 'drama',
                'comedy', 'biography', 'memoir', 'adventure', 'history'
            ]
            if not any(term in query_lower for term in specific_terms):
                return True

        # Common vague phrases
        vague_phrases = [
            'a book', 'recommend', 'what to read', 'something',
            'anything', 'book recommendation', 'suggest a book'
        ]
        if any(phrase in query_lower for phrase in vague_phrases):
            # Use LLM for final decision
            return await self._llm_vagueness_check(query)

        # If query has some length and specificity, it's probably clear
        if len(words) >= 3:
            return False

        # Use LLM for borderline cases
        return await self._llm_vagueness_check(query)

    async def _llm_vagueness_check(self, query: str) -> bool:
        """Use LLM to determine if query is vague"""
        try:
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": self.VAGUENESS_DETECTION_PROMPT.format(query=query)
                }],
                temperature=0.3,
                max_tokens=10
            )

            result = response.choices[0].message.content.strip().upper()
            return "VAGUE" in result
        except Exception:
            # If LLM fails, assume query is clear to avoid blocking user
            return False

    async def generate_clarifying_questions(self, query: str) -> str:
        """
        Generate friendly clarifying questions for a vague query

        Args:
            query: User's vague search query

        Returns:
            String with 2-3 clarifying questions
        """
        try:
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": self.CLARIFICATION_GENERATION_PROMPT.format(query=query)
                }],
                temperature=0.8,
                max_tokens=300
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback generic questions
            return """Let me help you find the perfect book! 📚

1. What genre interests you?
2. What's the mood? Something light or more serious?
3. Any favorite authors?"""

    async def enrich_query_with_context(self, original_query: str, user_context: str) -> str:
        """
        Combine original query with user's additional context

        Args:
            original_query: User's initial query
            user_context: Additional context provided by user

        Returns:
            Enriched query combining both
        """
        try:
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": self.CONTEXT_INTEGRATION_PROMPT.format(
                        original_query=original_query,
                        user_context=user_context
                    )
                }],
                temperature=0.3,
                max_tokens=100
            )

            enriched = response.choices[0].message.content.strip()

            # Remove quotes if LLM added them
            enriched = enriched.strip('"').strip("'")

            return enriched
        except Exception:
            # Fallback: simple concatenation
            return f"{original_query} {user_context}".strip()
