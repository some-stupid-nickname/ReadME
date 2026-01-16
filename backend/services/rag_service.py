"""RAG service for book recommendations"""
from typing import List
from mistralai import Mistral
from services.search_service import VectorSearchEngine


class BookRAGAssistant:
    """RAG assistant for book recommendations"""

    SYSTEM_PROMPT = """- DO NOT use markdown (no **, ##, ```)
You are Alex, a passionate librarian with years of experience. You love recommending books and do it with genuine enthusiasm.

Your communication style:
- Talk like a friend sharing discoveries: "Oh, I've got something interesting for you!"
- Use lively, conversational language, feel free to joke around
- Share personal opinions: "I think you'll love this...", "This one's a real gem!"
- Show empathy: understand what the person is looking for, even if they're not sure themselves

CRITICAL RULES - ABSOLUTELY MANDATORY:
1. ⚠️ ONLY recommend books that appear in the context! Copy the EXACT title and author from the context!
2. ⚠️ DO NOT INVENT book titles or authors! Every book you mention MUST be in the context above!
3. ⚠️ When describing a book, use ONLY information from that book's context entry!
4. ⚠️ Recommend ALL books from the context! If there are 10 books, describe all 10!
5. Explain your choices in simple words, like chatting with a friend over coffee
6. If the user mentions a book they liked - recommend books of the SAME GENRE (Fiction → Fiction, mystery → mystery)
7. When recommending similar books, explain WHY they're similar: style, atmosphere, themes, era
8. Add interesting details: publication year, publisher, or brief summary - when appropriate
9. Respond in English, warmly and with enthusiasm
10. Don't repeat book titles you've already suggested
11. Pay most attention to the book's genre and recommend books of the same genre as in the user's request

FORMAT EXAMPLE (use EXACT titles from context):
1. "The Diamond Age" by Neal Stephenson
   [Your description of THIS SPECIFIC BOOK from the context]

2. "Neuromancer" by William Gibson  
   [Your description of THIS SPECIFIC BOOK from the context]

Genre connection examples:
- "War and Peace" → classic literary fiction, historical novels, epic works
- Agatha Christie mysteries → other mysteries and thrillers
- Science fiction → other sci-fi

Example response:
"Oh, healthy eating! Great topic!

Listen, I've got a few books that will definitely come in handy:

1. "Don't Eat Your Heart Out Cookbook" by Joseph Piscatella
   This is exactly what you're looking for! A book about cooking deliciously while taking care of your heart. Published by Workman - they always put out quality cookbooks.

2. "Title" by Author
   [Your lively description of why this is great]

If you want something more specific - just ask, I'll find more!"

CRITICALLY IMPORTANT - VARIETY IN DESCRIPTIONS:
Each book must be described UNIQUELY!

UNIQUENESS RULES:
1. In ONE response - all book descriptions must be different
2. THROUGHOUT THE ENTIRE DIALOGUE - don't repeat phrases from previous responses!
3. Look at the conversation history and DON'T use the same expressions you've already used

DO NOT repeat:
- Identical sentence beginnings and book descriptions
- Same book titles
- Phrases you've already used in this dialogue
- Template constructions like "This book is a great choice for those who..."

Examples of DIFFERENT phrasings (alternate them and come up with new ones!):
- "This is a real gem!"
- "Now this is what I call a find!"
- "You know what caught my attention?"
- "Here's something else interesting..."
- "I can't help but mention..."
- "Check this one out..."
- "This is a must-read!"
- "Here's another great book..."
- "Oh, and this one's good too!"

IMPORTANT RULES:
- Never say "sorry, nothing found"
- DO NOT use markdown (no **, ##, ```)
- Use quotation marks for titles"""

    def __init__(self, search_engine: VectorSearchEngine, api_key: str,
                 model: str = "mistral-small-latest"):
        self.search_engine = search_engine
        self.client = Mistral(api_key=api_key)
        self.model = model
        self.conversation_history = []
        self.query_history = []
        self.used_phrases = []

    def _enhance_query(self, query: str) -> str:
        """Enhance query with English keywords for search"""

        context_info = ""
        if self.query_history:
            context_info = f"""
Context of user's previous queries (consider them!):
{chr(10).join(f'- "{q}"' for q in self.query_history[-3:])}

If the current query is related to previous ones (words like "more", "something similar", "others") -
consider the topic of previous queries, but don't duplicate book titles already recommended.
"""
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": f"""Convert the user's query into English keywords for book search.
{context_info}
Current query: "{query}"

Rules:
1. Identify the TOPIC of the query (not country, not language - the topic itself)
2. If the query is like "more", "others", "similar" - use the topic from previous queries
3. Return 5-10 English words for searching books on this topic
4. Only words separated by spaces, no explanations

Examples:
- "dogs" → dogs pets animals training care veterinary canine
- "more about dogs" → dogs pets animals breeds puppy canine training
- "mysteries" → mystery detective crime thriller fiction investigation

Your answer (only English keywords):"""
                }],
                temperature=0.3,
                max_tokens=50
            )
            keywords = response.choices[0].message.content.strip()
            keywords = keywords.replace('"', '').replace("'", "").replace("-", " ")
            return keywords
        except Exception:
            return query

    def _build_context(self, books: List[tuple]) -> str:
        """Build context from search results"""
        if not books:
            return "Search returned no results, but you should still help the user."

        context_parts = [
            "=== BOOKS TO RECOMMEND ===",
            "⚠️ YOU MUST ONLY RECOMMEND THESE BOOKS BELOW!",
            "⚠️ USE EXACT TITLES AND AUTHORS FROM THIS LIST!",
            f"⚠️ TOTAL: {len(books)} BOOKS AVAILABLE",
            ""
        ]
        
        for i, (book, score) in enumerate(books, 1):
            context_parts.append(f"--- Book {i} ---")
            context_parts.append(book.to_text())
            context_parts.append("")

        context_parts.append("=== END OF BOOK LIST ===")
        context_parts.append("Remember: ONLY recommend books from the list above!")
        
        return "\n".join(context_parts)

    def ask(self, user_query: str, top_k: int = 10, category_filter: str = None) -> tuple[str, List[tuple]]:
        """
        Ask the assistant a question
        
        Returns:
            tuple[str, List[tuple]]: (assistant response, list of found books with scores)
        """
        # Save query to history 
        self.query_history.append(user_query)
        # Keep last 3 queries
        if len(self.query_history) > 3:
            self.query_history = self.query_history[-3:]

        enhanced_query = self._enhance_query(user_query)

        # Search 
        search_results = self.search_engine.search(
            query=enhanced_query,
            top_k=top_k,
            category_filter=category_filter
        )

        context = self._build_context(search_results)

        # Build list of banned phrases to avoid repetition
        banned_phrases_text = ""
        if self.used_phrases:
            banned_phrases_text = f"""

Banned phrases (you've already used these, don't repeat):
{chr(10).join(f'- "{phrase}"' for phrase in self.used_phrases[-15:])}

Come up with new phrasings"""

        augmented_query = f"""Context with book information:
{context}
{banned_phrases_text}

User's question: {user_query}

IMPORTANT: Describe the books IN THE EXACT ORDER they appear in the context above!
- Book 1: Describe the first book from the list
- Book 2: Describe the second book from the list
- Book 3: Describe the third book from the list
And so on...

Use the EXACT title and author from each book's entry in the context!"""

        # Query Mistral
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *self.conversation_history,
            {"role": "user", "content": augmented_query}
        ]

        response = self.client.chat.complete(
            model=self.model,
            messages=messages,
            temperature=0.85,  
            max_tokens=1024
        )

        assistant_response = response.choices[0].message.content

        self._extract_used_phrases(assistant_response)

        self.conversation_history.append({"role": "user", "content": user_query})
        self.conversation_history.append({"role": "assistant", "content": assistant_response})

        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

        return assistant_response, search_results

    def _extract_used_phrases(self, response: str):
        """Extract characteristic phrases from response to prevent repetition"""
        common_patterns = [
            "this is a real gem",
            "what caught my attention",
            "check this one out",
            "a real find",
            "this book has everything",
            "will definitely come in handy",
            "must-read",
            "can't help but mention",
            "here's another great",
        ]

        for pattern in common_patterns:
            if pattern.lower() in response.lower():
                if pattern not in self.used_phrases:
                    self.used_phrases.append(pattern)

        if len(self.used_phrases) > 20:
            self.used_phrases = self.used_phrases[-20:]

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.query_history = []
        self.used_phrases = []
