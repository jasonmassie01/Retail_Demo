from google import genai
from google.genai import types
import os

PROJECT_ID = "alloydbtest-374215"
LOCATION = "us-central1"

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

def test_model(model_name):
    print(f"\nTesting model: {model_name}")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Hello",
            config=types.GenerateContentConfig(max_output_tokens=10)
        )
        print(f"SUCCESS: {response.text}")
        return True
    except Exception as e:
        print(f"FAILURE: {e}")
        return False

# 1. Try Gemini 3 with full path
test_model("publishers/google/models/gemini-3-flash-preview")

# 2. Try Gemini 2.0 Flash (to confirm SDK works)
test_model("gemini-2.0-flash-001")
