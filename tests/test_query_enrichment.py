#!/usr/bin/env python3
"""Test script for LLM query enrichment feature"""
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.query_enrichment_service import QueryEnrichmentService

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

def test_vagueness_detection():
    """Test vagueness detection"""
    print("=" * 60)
    print("TEST 1: Vagueness Detection")
    print("=" * 60)

    service = QueryEnrichmentService(api_key=MISTRAL_API_KEY)

    test_queries = [
        ("a book", True, "Very vague"),
        ("what to read", True, "Generic request"),
        ("recommend", True, "Too brief"),
        ("mystery", False, "Specific genre"),
        ("sci-fi about space", False, "Genre + topic"),
        ("something like War and Peace", False, "Specific reference"),
        ("light romantic comedy", False, "Multiple descriptors"),
    ]

    for query, expected_vague, description in test_queries:
        is_vague = service.is_query_vague(query)
        status = "✓" if is_vague == expected_vague else "✗"
        print(f"{status} '{query}' -> {'VAGUE' if is_vague else 'CLEAR'} ({description})")

    print()


def test_clarifying_questions():
    """Test clarifying questions generation"""
    print("=" * 60)
    print("TEST 2: Clarifying Questions Generation")
    print("=" * 60)

    service = QueryEnrichmentService(api_key=MISTRAL_API_KEY)

    test_queries = ["a book", "what to read", "recommend something"]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)
        questions = service.generate_clarifying_questions(query)
        print(questions)

    print()


def test_query_enrichment():
    """Test query enrichment with context"""
    print("=" * 60)
    print("TEST 3: Query Enrichment")
    print("=" * 60)

    service = QueryEnrichmentService(api_key=MISTRAL_API_KEY)

    test_cases = [
        ("a book", "mystery, something light"),
        ("what to read", "sci-fi about space, serious"),
        ("recommend", "classics, Russian literature, about war"),
        ("something", "romance, with humor, contemporary"),
    ]

    for original, context in test_cases:
        enriched = service.enrich_query_with_context(original, context)
        print(f"Original: '{original}'")
        print(f"Context:  '{context}'")
        print(f"Enriched: '{enriched}'")
        print("-" * 60)

    print()


def interactive_test():
    """Interactive testing mode"""
    print("=" * 60)
    print("INTERACTIVE TEST MODE")
    print("=" * 60)
    print("Type queries to test vagueness detection and enrichment.")
    print("Commands: /quit to exit, /questions <query> to test clarification")
    print()

    service = QueryEnrichmentService(api_key=MISTRAL_API_KEY)

    while True:
        try:
            user_input = input("Query: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "/quit":
                break

            if user_input.lower().startswith("/questions "):
                query = user_input[11:].strip()
                questions = service.generate_clarifying_questions(query)
                print(f"\nClarifying questions:\n{questions}\n")
                continue

            # Test vagueness
            is_vague = service.is_query_vague(user_input)
            print(f"Vagueness: {'VAGUE' if is_vague else 'CLEAR'}")

            if is_vague:
                questions = service.generate_clarifying_questions(user_input)
                print(f"\nQuestions:\n{questions}\n")

                context = input("Your context: ").strip()
                if context:
                    enriched = service.enrich_query_with_context(user_input, context)
                    print(f"Enriched: '{enriched}'\n")

            print()

        except KeyboardInterrupt:
            print("\nExiting...")
            break


def main():
    """Main test runner"""
    if not MISTRAL_API_KEY:
        print("Error: MISTRAL_API_KEY not set!")
        print("Please set it in backend/.env file")
        return

    print("\n🧪 LLM Query Enrichment Feature Tests\n")

    try:
        # Run automated tests
        test_vagueness_detection()
        test_clarifying_questions()
        test_query_enrichment()

        # Optional interactive mode
        print("Run interactive tests? (y/n): ", end="")
        choice = input().strip().lower()
        if choice == 'y':
            print()
            interactive_test()

        print("\n✓ All tests completed!")

    except Exception as e:
        print(f"\n✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
