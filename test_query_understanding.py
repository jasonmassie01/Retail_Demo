import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import json

PROJECT_ID = "alloydbtest-374215"
vertexai.init(project=PROJECT_ID, location="us-central1")

def test_query_understanding():
    model = GenerativeModel("gemini-1.5-flash-001")
    
    query = "Find me a red dress for under $50 returns dresses over $50"
    
    prompt = f"""
    You are a search query parser. Extract search parameters from the user's query.
    Return a JSON object with the following fields:
    - query: The core search text (remove price constraints).
    - min_price: The minimum price (null if not specified).
    - max_price: The maximum price (null if not specified).
    
    User Query: "{query}"
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(response_mime_type="application/json")
        )
        print(response.text)
        data = json.loads(response.text)
        print("Parsed JSON:", data)
    except Exception as e:
        print(f"Failed to generate or parse: {e}")

if __name__ == "__main__":
    test_query_understanding()
