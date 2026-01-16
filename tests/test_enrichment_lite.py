#!/usr/bin/env python3
"""Lightweight test for query enrichment service (no heavy dependencies)"""
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

def test_enrichment_service_only():
    """Test ONLY the QueryEnrichmentService (no TensorFlow dependencies)"""
    print("\n" + "=" * 60)
    print("  Query Enrichment Service Test (Lightweight)")
    print("=" * 60)

    MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
    if not MISTRAL_API_KEY:
        print("❌ Error: MISTRAL_API_KEY not set")
        return False

    # Import only what we need (avoid TensorFlow)
    from services.query_enrichment_service import QueryEnrichmentService

    service = QueryEnrichmentService(api_key=MISTRAL_API_KEY)

    tests_passed = 0
    tests_total = 5

    # Test 1: Vague query detection
    print("\n1. Vague query detection (brief query)...")
    try:
        is_vague = service.is_query_vague("a book")
        print(f"   Result: {'VAGUE' if is_vague else 'CLEAR'}")
        if is_vague:
            print("   ✓ PASS")
            tests_passed += 1
        else:
            print("   ✗ FAIL (expected VAGUE)")
    except Exception as e:
        print(f"   ✗ FAIL: {str(e)}")

    # Test 2: Clear query detection
    print("\n2. Clear query detection (specific query)...")
    try:
        is_clear = not service.is_query_vague("sci-fi about space")
        print(f"   Result: {'CLEAR' if is_clear else 'VAGUE'}")
        if is_clear:
            print("   ✓ PASS")
            tests_passed += 1
        else:
            print("   ✗ FAIL (expected CLEAR)")
    except Exception as e:
        print(f"   ✗ FAIL: {str(e)}")

    # Test 3: Generate clarifying questions
    print("\n3. Clarifying questions generation...")
    try:
        questions = service.generate_clarifying_questions("a book")
        print(f"   Generated {len(questions)} characters")
        print(f"   Preview: {questions[:100]}...")
        if len(questions) > 50:
            print("   ✓ PASS")
            tests_passed += 1
        else:
            print("   ✗ FAIL (too short)")
    except Exception as e:
        print(f"   ✗ FAIL: {str(e)}")

    # Test 4: Query enrichment
    print("\n4. Query enrichment with context...")
    try:
        enriched = service.enrich_query_with_context(
            original_query="a book",
            user_context="mystery, something light"
        )
        print(f"   Original: 'a book'")
        print(f"   Context: 'mystery, something light'")
        print(f"   Enriched: '{enriched}'")
        if len(enriched) > 5 and "mystery" in enriched.lower():
            print("   ✓ PASS")
            tests_passed += 1
        else:
            print("   ✗ FAIL")
    except Exception as e:
        print(f"   ✗ FAIL: {str(e)}")

    # Test 5: Schema imports
    print("\n5. Schema definitions...")
    try:
        from models.schemas import (
            ClarificationRequest,
            ClarificationResponse,
            EnrichedSearchRequest
        )
        req = ClarificationRequest(query="test")
        print(f"   Imported and created: {type(req).__name__}")
        print("   ✓ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ FAIL: {str(e)}")

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {tests_passed}/{tests_total} tests passed")
    print("=" * 60)

    if tests_passed == tests_total:
        print("\n✅ ALL TESTS PASSED!")
        print("\nThe query enrichment feature is working correctly!")
        print("\nNext steps:")
        print("1. Start backend API to test endpoints")
        print("2. Test with Telegram bot")
        print("3. Test with console interface")
        return True
    else:
        print(f"\n⚠️  {tests_total - tests_passed} test(s) failed")
        return False


if __name__ == "__main__":
    try:
        success = test_enrichment_service_only()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
