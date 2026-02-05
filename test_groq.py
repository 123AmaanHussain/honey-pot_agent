"""
Test Groq integration capabilities.
"""
import logging
import sys
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()

def test_groq():
    print("=" * 60)
    print("TESTING GROQ INTEGRATION")
    print("=" * 60)
    
    # Check API key presence
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌ GROQ_API_KEY not found in environment!")
        return
        
    print(f"✅ GROQ_API_KEY found: {groq_key[:4]}...{groq_key[-4:]}")
    
    try:
        from agent import call_llm, groq_client
        
        if groq_client:
            print("✅ Groq client initialized in agent.py")
        else:
            print("❌ Groq client NOT initialized in agent.py")
            return

        print("\nSending test prompt to LLM (should use Groq)...")
        response = call_llm("Reply with exactly one word: 'Success'")
        
        print(f"\nResponse: {response}")
        
        if "Success" in response or "success" in response:
            print("\n✅ Groq Inference: WORKING")
        else:
            print(f"\n⚠️ Unexpected response: {response}")
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_groq()
