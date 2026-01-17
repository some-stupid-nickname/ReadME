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


@dataclass
class JudgmentResult:
    """Result from LLM judge for a single book recommendation"""
    score: int  # 0-5
    reasoning: str
    book_title: str
    book_author: str
    retrieval_score: float
    rank: int
    is_error: bool = False  # Track if this judgment failed due to API error


class RAGEvaluator:
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
        Initialize the RAG evaluator

        Args:
            collection_name: Name of the Qdrant collection
            embedding_model: Sentence transformer model for retrieval
            judge_model: LLM model to use as judge
                - Mistral: 'mistral-small-latest' (free tier), 'mistral-medium-latest', 'mistral-large-latest'
                - OpenAI: 'gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'
            llm_provider: 'mistral' or 'openai'
            qdrant_path: Path to Qdrant storage
            api_key: API key (or set MISTRAL_API_KEY or OPENAI_API_KEY env var)
        """
        self.collection_name = collection_name
        self.judge_model = judge_model
        self.llm_provider = llm_provider.lower()

        # Initialize LLM client based on provider
        if self.llm_provider == "mistral":
            if not MISTRAL_AVAILABLE:
                raise ImportError("Mistral client not installed. Run: pip install mistralai")
            api_key = api_key or os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError("Mistral API key required. Set MISTRAL_API_KEY environment variable.")
            self.llm_client = Mistral(api_key=api_key)

        elif self.llm_provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI client not installed. Run: pip install openai")
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
            self.llm_client = OpenAI(api_key=api_key)

        else:
            raise ValueError(f"Unknown LLM provider: {llm_provider}. Use 'mistral' or 'openai'")

        # Initialize Qdrant and embedding model
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)

        print(f"Connecting to Qdrant at {qdrant_path}")
        self.qdrant_client = QdrantClient(path=qdrant_path)

        # Verify collection exists
        try:
            info = self.qdrant_client.get_collection(collection_name)
            print(f"✓ Connected to collection '{collection_name}' with {info.points_count:,} books")
        except Exception as e:
            raise ValueError(f"Could not connect to collection '{collection_name}': {e}")

    def search_books(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for books using the RAG system

        Args:
            query: User query
            top_k: Number of results to return

        Returns:
            List of book dictionaries with metadata and scores
        """
        # Create query embedding
        query_vector = self.embedding_model.encode(query).tolist()

        # Search in Qdrant
        results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k
        ).points

        # Format results
        books = []
        for result in results:
            book = result.payload.copy()
            book['retrieval_score'] = result.score
            books.append(book)

        return books

    def judge_relevance(self, query: str, book: Dict) -> JudgmentResult:
        """
        Use OpenAI LLM to judge how relevant a book is to a query

        Args:
            query: User query
            book: Book dictionary with metadata

        Returns:
            JudgmentResult with score and reasoning
        """
        # Extract book info (handle different column name formats)
        title = book.get('Title') or book.get('title') or 'Unknown'
        author = book.get('Authors') or book.get('Author') or book.get('authors') or 'Unknown'
        category = book.get('Category') or book.get('category') or 'Unknown'
        description = book.get('Description') or book.get('description') or ''

        # Truncate long descriptions
        if description and len(description) > 300:
            description = description[:300] + '...'

        prompt = f"""You are evaluating book recommendations for a user query.

User Query: "{query}"

Recommended Book:
- Title: {title}
- Author: {author}
- Category: {category}
- Description: {description if description else 'No description available'}

Task: Rate how relevant this book is to the user's query on a scale of 0-5:
- 0: Completely irrelevant (wrong genre, topic, or intent)
- 1: Slightly related but not useful
- 2: Somewhat related but not a good match
- 3: Moderately relevant, could be useful
- 4: Highly relevant, good match
- 5: Perfect match for the query

Consider:
- Does the book's genre/category match the query intent?
- Does the description align with what the user is looking for?
- Would this book satisfy the user's information need?

Respond ONLY with valid JSON in this exact format:
{{
  "score": <integer 0-5>,
  "reasoning": "<brief 1-2 sentence explanation>"
}}"""

        try:
            # Call appropriate LLM provider
            if self.llm_provider == "mistral":
                response = self.llm_client.chat.complete(
                    model=self.judge_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                result = json.loads(response.choices[0].message.content)

            else:  # openai
                response = self.llm_client.chat.completions.create(
                    model=self.judge_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                result = json.loads(response.choices[0].message.content)

            return JudgmentResult(
                score=result["score"],
                reasoning=result["reasoning"],
                book_title=title,
                book_author=author,
                retrieval_score=book.get('retrieval_score', 0.0),
                rank=book.get('rank', 0)
            )

        except Exception as e:
            error_msg = str(e)
            # Check if it's a rate limit error
            if "429" in error_msg or "Rate limit" in error_msg:
                print(f"⚠️  Rate limit hit for '{title[:40]}...'")
            else:
                print(f"Error judging book '{title}': {e}")

            return JudgmentResult(
                score=0,
                reasoning=f"Error: {error_msg}",
                book_title=title,
                book_author=author,
                retrieval_score=book.get('retrieval_score', 0.0),
                rank=book.get('rank', 0),
                is_error=True  # Mark as error so it's excluded from metrics
            )

    def evaluate_query(self, query: str, top_k: int = 5, verbose: bool = True) -> Dict:
        """
        Evaluate recommendations for a single query

        Args:
            query: User query to evaluate
            top_k: Number of recommendations to retrieve
            verbose: Print detailed results

        Returns:
            Dictionary with evaluation metrics and judgments
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"Query: '{query}'")
            print(f"{'='*80}")

        # Get recommendations
        books = self.search_books(query, top_k=top_k)

        # Judge each recommendation
        judgments = []
        for rank, book in enumerate(books, 1):
            book['rank'] = rank
            judgment = self.judge_relevance(query, book)

            if verbose:
                print(f"\n{rank}. {judgment.book_title[:60]}")
                print(f"   Author: {judgment.book_author}")
                print(f"   Retrieval Score: {judgment.retrieval_score:.3f}")
                if judgment.is_error:
                    print(f"   ⚠️  FAILED: {judgment.reasoning}")
                else:
                    print(f"   Relevance: {judgment.score}/5 - {judgment.reasoning}")

            judgments.append(judgment)

            # Add delay for Mistral to avoid rate limits
            if self.llm_provider == "mistral" and rank < len(books):
                time.sleep(2)  # 2 second delay between Mistral API calls

        # Calculate metrics - ONLY include successful judgments
        successful_judgments = [j for j in judgments if not j.is_error]
        failed_count = len([j for j in judgments if j.is_error])

        if not successful_judgments:
            # All judgments failed
            if verbose:
                print(f"\n⚠️  WARNING: All {len(judgments)} judgments failed (likely rate limits)")
            scores = []
        else:
            scores = [j.score for j in successful_judgments]
        # Calculate metrics only from successful judgments
        if scores:
            avg_score = np.mean(scores)
            top_1_score = scores[0] if scores else None
            top_3_avg = np.mean(scores[:3]) if len(scores) >= 3 else np.mean(scores)
        else:
            avg_score = None
            top_1_score = None
            top_3_avg = None

        metrics = {
            "query": query,
            "avg_relevance": float(avg_score) if avg_score is not None else None,
            "top_1_relevance": int(top_1_score) if top_1_score is not None else None,
            "top_3_avg_relevance": float(top_3_avg) if top_3_avg is not None else None,
            "successful_judgments": len(successful_judgments),
            "failed_judgments": failed_count,
            "total_judgments": len(judgments),
            "judgments": [
                {
                    "rank": j.rank,
                    "title": j.book_title,
                    "author": j.book_author,
                    "retrieval_score": j.retrieval_score,
                    "relevance_score": j.score if not j.is_error else None,
                    "reasoning": j.reasoning,
                    "is_error": j.is_error
                }
                for j in judgments
            ]
        }

        if verbose:
            print(f"\n{'─'*80}")
            print(f"Metrics:")
            if avg_score is not None:
                print(f"  Average Relevance: {avg_score:.2f}/5 (from {len(successful_judgments)} successful judgments)")
                if failed_count > 0:
                    print(f"  ⚠️  {failed_count} judgments failed (not counted in metrics)")
                if top_1_score is not None:
                    print(f"  Top-1 Relevance: {top_1_score}/5")
                if top_3_avg is not None:
                    print(f"  Top-3 Average: {top_3_avg:.2f}/5")
            else:
                print(f"  ⚠️  No successful judgments (all {failed_count} failed)")

        return metrics

    def evaluate_batch(
        self,
        queries: List[str],
        top_k: int = 5,
        output_file: Optional[str] = None
    ) -> Dict:
        """
        Evaluate multiple queries and aggregate results

        Args:
            queries: List of test queries
            top_k: Number of recommendations per query
            output_file: Optional JSON file to save results

        Returns:
            Dictionary with overall metrics and per-query results
        """
        print(f"\n{'='*80}")
        print(f"Starting batch evaluation on {len(queries)} queries")
        print(f"Judge model: {self.judge_model}")
        print(f"Top-K: {top_k}")
        print(f"{'='*80}\n")

        all_results = []

        for query in tqdm(queries, desc="Evaluating queries"):
            result = self.evaluate_query(query, top_k=top_k, verbose=False)
            all_results.append(result)

        # Aggregate metrics - filter out None values from failed queries
        avg_relevances = [r["avg_relevance"] for r in all_results if r["avg_relevance"] is not None]
        top_1_scores = [r["top_1_relevance"] for r in all_results if r["top_1_relevance"] is not None]
        top_3_avgs = [r["top_3_avg_relevance"] for r in all_results if r["top_3_avg_relevance"] is not None]

        # Count total successful and failed judgments
        total_successful = sum(r["successful_judgments"] for r in all_results)
        total_failed = sum(r["failed_judgments"] for r in all_results)
        total_judgments = sum(r["total_judgments"] for r in all_results)
        queries_with_all_failures = sum(1 for r in all_results if r["successful_judgments"] == 0)

        overall_metrics = {
            "num_queries": len(queries),
            "top_k": top_k,
            "judge_model": self.judge_model,
            "llm_provider": self.llm_provider,
            "total_judgments_attempted": total_judgments,
            "successful_judgments": total_successful,
            "failed_judgments": total_failed,
            "queries_with_all_failures": queries_with_all_failures,
            "overall_avg_relevance": float(np.mean(avg_relevances)) if avg_relevances else None,
            "overall_top1_avg": float(np.mean(top_1_scores)) if top_1_scores else None,
            "overall_top3_avg": float(np.mean(top_3_avgs)) if top_3_avgs else None,
            "std_relevance": float(np.std(avg_relevances)) if len(avg_relevances) > 1 else 0,
            "min_relevance": float(np.min(avg_relevances)) if avg_relevances else None,
            "max_relevance": float(np.max(avg_relevances)) if avg_relevances else None,
            "queries_with_perfect_top1": sum(1 for s in top_1_scores if s == 5),
            "queries_with_good_top1": sum(1 for s in top_1_scores if s >= 4),
        }

        results = {
            "overall": overall_metrics,
            "per_query": all_results
        }

        # Print summary
        print(f"\n{'='*80}")
        print("EVALUATION SUMMARY")
        print(f"{'='*80}")
        print(f"Queries evaluated: {overall_metrics['num_queries']}")
        print(f"\nJudgment Success Rate:")
        print(f"  Total judgments attempted: {total_judgments}")
        print(f"  Successful: {total_successful} ({total_successful/total_judgments*100:.1f}%)")
        print(f"  Failed: {total_failed} ({total_failed/total_judgments*100:.1f}%)")
        if queries_with_all_failures > 0:
            print(f"  ⚠️  Queries with all failures: {queries_with_all_failures}")

        if overall_metrics['overall_avg_relevance'] is not None:
            print(f"\nRelevance Metrics (based on {total_successful} successful judgments):")
            print(f"  Overall average relevance: {overall_metrics['overall_avg_relevance']:.2f}/5")
            print(f"  Top-1 average: {overall_metrics['overall_top1_avg']:.2f}/5")
            print(f"  Top-3 average: {overall_metrics['overall_top3_avg']:.2f}/5")
            print(f"  Queries with perfect top-1 (5/5): {overall_metrics['queries_with_perfect_top1']}")
            print(f"  Queries with good top-1 (≥4/5): {overall_metrics['queries_with_good_top1']}")
        else:
            print(f"\n⚠️  No successful judgments - cannot calculate relevance metrics")
        print(f"{'='*80}\n")

        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"✓ Results saved to {output_file}")

        return results


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
    parser.add_argument("--model",
                        help="LLM model to use (default: mistral-small-latest for Mistral, gpt-4o-mini for OpenAI)")

    args = parser.parse_args()

    # Set default model based on provider if not specified
    if not args.model:
        args.model = "mistral-small-latest" if args.provider == "mistral" else "gpt-4o-mini"

    # Initialize evaluator
    evaluator = RAGEvaluator(judge_model=args.model, llm_provider=args.provider)

    if args.query:
        # Evaluate single query
        evaluator.evaluate_query(args.query, top_k=args.top_k, verbose=True)
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

        evaluator.evaluate_batch(
            queries,
            top_k=args.top_k,
            output_file=args.output
        )


if __name__ == "__main__":
    main()
