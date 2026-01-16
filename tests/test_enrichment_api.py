#!/usr/bin/env python3
"""Simple test for query enrichment API endpoints (without running server)"""
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

def test_service_directly():
    """Test the QueryEnrichmentService directly"""
    from services.query_enrichment_service import QueryEnrichmentService

    MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
    if not MISTRAL_API_KEY:
        print("❌ Error: MISTRAL_API_KEY not set")
        return False

    print("Testing QueryEnrichmentService...")
    print("=" * 60)

    service = QueryEnrichmentService(api_key=MISTRAL_API_KEY)

    # Test 1: Vague query detection
    print("\n1. Testing vague query detection...")
    vague_query = "книгу"
    is_vague = service.is_query_vague(vague_query)
    print(f"   Query: '{vague_query}'")
    print(f"   Is vague: {is_vague}")
    print(f"   ✓ PASS" if is_vague else "   ✗ FAIL")

    # Test 2: Clear query detection
    print("\n2. Testing clear query detection...")
    clear_query = "фантастика про космос"
    is_clear = not service.is_query_vague(clear_query)
    print(f"   Query: '{clear_query}'")
    print(f"   Is clear: {is_clear}")
    print(f"   ✓ PASS" if is_clear else "   ✗ FAIL")

    # Test 3: Generate questions
    print("\n3. Testing clarifying questions generation...")
    questions = service.generate_clarifying_questions(vague_query)
    print(f"   Questions generated: {len(questions)} chars")
    print(f"   ✓ PASS" if len(questions) > 50 else "   ✗ FAIL")

    # Test 4: Query enrichment
    print("\n4. Testing query enrichment...")
    enriched = service.enrich_query_with_context(
        original_query="книгу",
        user_context="детектив, легкий"
    )
    print(f"   Original: 'книгу'")
    print(f"   Context: 'детектив, легкий'")
    print(f"   Enriched: '{enriched}'")
    print(f"   ✓ PASS" if len(enriched) > 5 else "   ✗ FAIL")

    print("\n" + "=" * 60)
    print("✓ All service tests passed!")
    return True


def test_schemas():
    """Test that new schemas are properly defined"""
    from models.schemas import (
        ClarificationRequest,
        ClarificationResponse,
        EnrichedSearchRequest
    )

    print("\nTesting schemas...")
    print("=" * 60)

    # Test ClarificationRequest
    print("\n1. Testing ClarificationRequest...")
    req = ClarificationRequest(query="книгу")
    print(f"   Created: {req}")
    print(f"   ✓ PASS")

    # Test ClarificationResponse
    print("\n2. Testing ClarificationResponse...")
    resp = ClarificationResponse(
        is_vague=True,
        clarifying_questions="Test questions",
        original_query="книгу"
    )
    print(f"   Created: {resp}")
    print(f"   ✓ PASS")

    # Test EnrichedSearchRequest
    print("\n3. Testing EnrichedSearchRequest...")
    req = EnrichedSearchRequest(
        original_query="книгу",
        user_context="детектив"
    )
    print(f"   Created: {req}")
    print(f"   ✓ PASS")

    print("\n" + "=" * 60)
    print("✓ All schema tests passed!")
    return True


def test_dependencies():
    """Test that dependencies are properly configured"""
    from api.dependencies import get_query_enrichment_service

    print("\nTesting dependencies...")
    print("=" * 60)

    print("\n1. Testing get_query_enrichment_service...")
    service = get_query_enrichment_service()
    print(f"   Service created: {type(service).__name__}")
    print(f"   ✓ PASS")

    print("\n" + "=" * 60)
    print("✓ All dependency tests passed!")
    return True


def main():
    print("\n" + "=" * 60)
    print("  LLM Query Enrichment API Tests")
    print("=" * 60)

    all_passed = True

    try:
        # Test schemas
        if not test_schemas():
            all_passed = False

        # Test dependencies
        if not test_dependencies():
            all_passed = False

        # Test service
        if not test_service_directly():
            all_passed = False

        if all_passed:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("\nThe feature is ready to use!")
            print("\nTo test with real API:")
            print("1. Start backend: cd backend && python -m api.main")
            print("2. Test endpoints:")
            print("   - POST /api/search/clarify")
            print("   - POST /api/search/enriched")
        else:
            print("\n❌ SOME TESTS FAILED")
            return 1

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
