"""
LLM-as-Judge Evaluation for RAG Book Recommendation System

This script evaluates the quality of book recommendations using LLM models
(Mistral or OpenAI) as automated judges. It measures relevance, diversity,
and overall recommendation quality.
"""

import os
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np
from tqdm import tqdm

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

import re
from langchain.messages import AIMessage

from datasets import Dataset
from langchain_core.documents import Document

from langchain_mistralai import ChatMistralAI
from langchain_mistralai.chat_models import acompletion_with_retry

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
        collection_name: str = "books",
        embedding_model: str = "all-MiniLM-L6-v2",
        judge_model: str = "mistral-small-latest",
        llm_provider: str = "mistral",
        qdrant_path: str = "./qdrant_storage",
        api_key: Optional[str] = None
    ):
        """
        Initialize RAGAS evaluator
        """
        self.collection_name = collection_name
        self.llm_provider = llm_provider.lower()

        # Initialize LLM client based on provider
        if self.llm_provider == "mistral":
            if not MISTRAL_AVAILABLE:
                raise ImportError("Mistral client not installed. Run: pip install mistralai")
            api_key = api_key or os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError("Mistral API key required. Set MISTRAL_API_KEY environment variable.")
            self.judge_model = SafeChatMistral(model="mistral-small-latest", api_key=api_key)
        else:
            raise ValueError("Only 'mistral' is availble as llm_provider")

        # Initialize Qdrant and embedding model
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = HuggingFaceEmbeddings(model_name=embedding_model)

        # Qdrant
        print(f"Connecting to Qdrant at {qdrant_path}")
        self.qdrant = QdrantClient(path=qdrant_path)

        # Verify collection exists
        try:
            info = self.qdrant.get_collection(collection_name)
            print(f"✓ Connected to collection '{collection_name}' with {info.points_count:,} books")
        except Exception as e:
            raise ValueError(f"Could not connect to collection '{collection_name}': {e}")

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def search_books(self, query: str, top_k: int = 5) -> List[Document]:
        query_vector = self.embedding_model.embed_query(query)

        results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
        ).points

        docs = []
        for r in results:
            content = r.payload.get("Description") or r.payload.get("description") or ""
            title = r.payload.get("Title") or r.payload.get("title") or "Unknown"

            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "title": title,
                        "score": r.score,
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
            with open(output_file, "w") as f:
                json.dump(results_dict, f, indent=2)
            print(f"✓ Results saved to {output_file}")

        return results_dict


def load_test_queries(file_path: str = "test_queries.json") -> List[str]:
    """Load test queries from JSON file"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
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
    parser.add_argument("--qdrant-path", default="./qdrant_storage",
                        help="Path to qdrant sqlite file in a collection")
    parser.add_argument("--model",
                        help="LLM model to use (default: mistral-small-latest for Mistral, gpt-4o-mini for OpenAI)")

    args = parser.parse_args()

    # Set default model based on provider if not specified
    if not args.model:
        args.model = "mistral-small-latest" if args.provider == "mistral" else "gpt-4o-mini"

    # Initialize evaluator
    book_db = BookDatabase(args.collection_path + '/collection/books/storage.sqlite')
    search_engine = VectorSearchEngine(book_db)
    assistant = BookRAGAssistant(
        search_engine=search_engine,
        api_key=os.getenv("MISTRAL_API_KEY")
    )
    evaluator = RAGASEvaluator(judge_model="mistral-small-latest", qdrant_path=args.qdrant_path)

    if args.query:
        # Evaluate single query
        queries = [query]
        response = assistant.ask(args.query)
        responses.append(response)
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
        for query in tqdm(queries):
            response = assistant.ask(query)
            responses.append(response)

        evaluator.ragas_evaluate(
            queries=queries,
            responses=responses,
            top_k=5,
            output_file="output_file.json"
        )


if __name__ == "__main__":
    main()
