"""
LLM-as-Judge Evaluation for RAG Book Recommendation System

This script evaluates the quality of book recommendations using LLM models
(Mistral or OpenAI) as automated judges. It measures relevance, diversity,
and overall recommendation quality.
"""

import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from tqdm import tqdm

from dotenv import load_dotenv

import re
from langchain.messages import AIMessage

from datasets import Dataset
from langchain_core.documents import Document

from langchain_mistralai import ChatMistralAI

from langchain_community.embeddings import HuggingFaceEmbeddings

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy
)

from services.rag_service import BookRAGAssistant
from services.search_service import VectorSearchEngine
from services.database_service import BookDatabase

# Import LLM clients conditionally
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Load environment variables
load_dotenv()

def safe_format_number(num: int) -> str:
    """Safely format number with thousands separator for Windows console compatibility"""
    try:
        return f"{num:,}"
    except (ValueError, UnicodeEncodeError):
        return str(num)

def strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


class SafeChatMistral(ChatMistralAI):
   
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        result = await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
        new_generations = []
        for gen in result.generations:
            raw = gen.message.content
            cleaned = strip_json_fences(raw)
            gen.message = AIMessage(content=cleaned)

            raw = gen.text
            cleaned = strip_json_fences(raw)
            gen.text = cleaned
            
            new_generations.append(gen)
        
        result.generations = new_generations

        return result

@dataclass
class RAGResult:
    query: str
    answer: str
    contexts: List[str]


class RAGASEvaluator:
    def __init__(
        self,
        search_engine: VectorSearchEngine,
        embedding_model: str = "all-MiniLM-L6-v2",
        judge_model: str = "mistral-small-latest",
        llm_provider: str = "mistral",
        api_key: Optional[str] = None,
        use_full_context: bool = True,
        context_lang: str = "ru"
    ):
        """
        Initialize RAGAS evaluator
        
        Args:
            search_engine: VectorSearchEngine instance for book search
            embedding_model: Embedding model name for RAGAS metrics
            judge_model: LLM model to use as judge
            llm_provider: LLM provider ('mistral' or 'openai')
            api_key: API key for LLM (or set via environment variable)
            use_full_context: If True, use book.to_text() (full info), 
                             if False, use only description
            context_lang: Language for context ('ru' or 'en')
        """
        self.search_engine = search_engine
        self.llm_provider = llm_provider.lower()
        self.use_full_context = use_full_context
        self.context_lang = context_lang

        # Initialize LLM client based on provider
        if self.llm_provider == "mistral":
            if not MISTRAL_AVAILABLE:
                raise ImportError("Mistral client not installed. Run: pip install mistralai")
            api_key = api_key or os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError("Mistral API key required. Set MISTRAL_API_KEY environment variable.")
            self.judge_model = SafeChatMistral(model=judge_model, api_key=api_key)
        else:
            raise ValueError("Only 'mistral' is available as llm_provider")

        # Initialize embedding model for RAGAS metrics
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = HuggingFaceEmbeddings(model_name=embedding_model)

        # Verify database connection
        num_books = len(search_engine.book_db.books)
        print(f"[OK] Connected to database with {safe_format_number(num_books)} books")
        
        # Log context settings
        context_mode = "full book info" if self.use_full_context else "description only"
        print(f"[CONFIG] Context mode: {context_mode} (language: {self.context_lang})")

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def search_books(self, query: str, top_k: int = 5) -> List[Document]:
        """Search books using VectorSearchEngine"""
        results = self.search_engine.search(query, top_k=top_k)
        
        docs = []
        for book, score in results:
            # FIXED: Use full context like RAG system does
            if self.use_full_context:
                # Use the same information that RAG assistant sees
                content = book.to_text(lang=self.context_lang)
            else:
                # Use only description (old behavior)
                content = book.description or ""
            
            title = book.title or "Unknown"
            
            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "title": title,
                        "score": score,
                    },
                )
            )
        
        return docs

    # ------------------------------------------------------------------
    # Build RAGAS dataset
    # ------------------------------------------------------------------
    def build_dataset(
        self,
        queries: List[str],
        responses: List[str],
        top_k: int = 5,
    ) -> Dataset:
        records = []

        for i, query in tqdm(enumerate(queries), desc="Running RAG pipeline"):
            docs = self.search_books(query, top_k=top_k)
            # answer = self.generate_answer(query, docs)

            records.append(
                {
                    "question": query,
                    "response": responses[i],
                    "retrieved_contexts": [d.page_content for d in docs],
                }
            )

        return Dataset.from_list(records)

    # ------------------------------------------------------------------
    # Evaluate with RAGAS
    # ------------------------------------------------------------------
    def ragas_evaluate(
        self,
        queries: List[str],
        responses: List[str],
        top_k: int = 5,
        output_file: Optional[str] = None,
    ) -> Dict:
        dataset = self.build_dataset(queries, responses=responses, top_k=top_k)

        print("\nRunning RAGAS evaluation...\n")

        answer_relevancy.embeddings = self.embedding_model
        faithfulness.llm = self.judge_model
        answer_relevancy.llm = self.judge_model

        results = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy
            ],
            allow_nest_asyncio=False
        )

        results_dict = results.to_pandas().to_dict(orient="list")

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results_dict, f, indent=2)
            print(f"[OK] Results saved to {output_file}")

        return results_dict


def load_test_queries(file_path: str = "test_queries.json") -> List[str]:
    """Load test queries from JSON file"""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as f:
            data = json.load(f)
            return data.get("queries", [])
    return []


def main():
    """Main entry point for evaluation"""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate RAG book recommendation system")
    parser.add_argument("--queries-file", default="test_queries.json", help="JSON file with test queries")
    parser.add_argument("--query", type=str, help="Evaluate a single query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of recommendations to evaluate")
    parser.add_argument("--output", type=str, help="Output JSON file for results")
    parser.add_argument("--provider", default="mistral", choices=["mistral", "openai"],
                        help="LLM provider to use (default: mistral)")
    parser.add_argument("--db-path", default="books.sqlite",
                        help="Path to SQLite database file")
    parser.add_argument("--model",
                        help="LLM model to use (default: mistral-small-latest for Mistral, gpt-4o-mini for OpenAI)")
    parser.add_argument("--use-description-only", action="store_true",
                        help="Use only book description for context (old behavior). Default: use full book info")
    parser.add_argument("--context-lang", default="ru", choices=["ru", "en"],
                        help="Language for context formatting (default: ru for Russian)")

    args = parser.parse_args()

    # Set default model based on provider if not specified
    if not args.model:
        args.model = "mistral-small-latest" if args.provider == "mistral" else "gpt-4o-mini"

    # Initialize database and search engine
    print(f"Loading database from {args.db_path}")
    book_db = BookDatabase(args.db_path)
    search_engine = VectorSearchEngine(book_db)
    
    assistant = BookRAGAssistant(
        search_engine=search_engine,
        api_key=os.getenv("MISTRAL_API_KEY")
    )
    
    # Initialize evaluator with search engine
    evaluator = RAGASEvaluator(
        search_engine=search_engine,
        judge_model=args.model,
        llm_provider=args.provider,
        use_full_context=not args.use_description_only,
        context_lang=args.context_lang
    )

    if args.query:
        # Evaluate single query
        queries = [args.query]
        response, _ = assistant.ask(args.query)
        responses = [response]
        
        evaluator.ragas_evaluate(
            queries=queries,
            responses=responses,
            top_k=args.top_k,
            output_file=args.output
        )
    else:
        # Load and evaluate batch
        queries = load_test_queries(args.queries_file)

        if not queries:
            print(f"No queries found in {args.queries_file}. Using default queries.")
            queries = [
                "fantasy book with dragons and magic",
                "mystery thriller detective novel",
                "business book about startups",
                "science fiction space adventure",
                "historical fiction world war"
            ]

        responses = []
        for query in tqdm(queries, desc="Generating responses"):
            response, _ = assistant.ask(query)
            responses.append(response)

        evaluator.ragas_evaluate(
            queries=queries,
            responses=responses,
            top_k=args.top_k,
            output_file=args.output
        )


if __name__ == "__main__":
    main()
