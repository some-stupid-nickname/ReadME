"""
Quick test script to verify Mistral API setup
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Check if Mistral is installed
try:
    from mistralai import Mistral
    print("✓ Mistral package installed")
except ImportError:
    print("✗ Mistral package not installed. Run: pip install mistralai")
    exit(1)

# Check for API key
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key or api_key == "your_mistral_api_key_here":
    print("\n⚠ MISTRAL_API_KEY not set in .env file")
    print("Get your free API key from: https://console.mistral.ai/")
    print("\nUpdate backend/.env with:")
    print("MISTRAL_API_KEY=your_actual_key_here")
else:
    print(f"✓ Mistral API key found (length: {len(api_key)})")

    # Try to initialize client
    try:
        client = Mistral(api_key=api_key)
        print("✓ Mistral client initialized successfully")
        print("\nYou're ready to use Mistral for evaluation!")
        print("\nExample usage:")
        print('  python evaluate_rag.py --query "fantasy books with magic" --provider mistral')
    except Exception as e:
        print(f"✗ Error initializing Mistral client: {e}")
