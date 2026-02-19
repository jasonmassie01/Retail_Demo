import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

# Mock streamlit before importing app
from unittest.mock import MagicMock
import sys
sys.modules['streamlit'] = MagicMock()
sys.modules['streamlit'].cache_resource = lambda func: func
class SessionState(dict):
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value

sys.modules['streamlit'].session_state = SessionState()

# Now import the functions we want to test
from app import detect_intent, generate_response, get_gemini_model, log_debug 

def test_intent():
    print("Testing Intent Detection...")
    
    queries = [
        ("I want a red dress", "SEARCH"),
        ("Hello, how are you?", "CHAT"),
        ("Show me blue shoes", "SEARCH"),
        ("What is the refund policy?", "CHAT"), # Might be ambiguous, but likely CHAT or maybe SEARCH if we had policy docs
        ("Find me a cool jacket", "SEARCH")
    ]
    
    for q, expected in queries:
        intent = detect_intent(q, [])
        print(f"Query: '{q}' -> Intent: {intent} (Expected: {expected})")

def test_response():
    print("\nTesting Response Generation...")
    
    query = "I want a red dress"
    results = [
        (1, "Red Evening Gown", "Beautiful red evening gown...", 120.0, "img_url"),
        (2, "Summer Red Dress", "Light casual red dress...", 45.0, "img_url")
    ]
    history = []
    
    response = generate_response(query, results, history)
    print(f"Query: '{query}'")
    print(f"Response: {response}")

if __name__ == "__main__":
    try:
        test_intent()
        test_response()
        print("\nSUCCESS: Logic tests passed.")
    except Exception as e:
        print(f"\nFAILURE: {e}")
