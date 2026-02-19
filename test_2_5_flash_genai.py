from google import genai
from google.genai import types
import os

PROJECT_ID = "alloydbtest-374215"
LOCATION = "us-central1"

print(f"Testing Gemini 2.5 Flash Lite with google-genai in {LOCATION}...")

try:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    
    # Try the short name first
    model = "gemini-2.5-flash-lite-preview-09-2025"
    
    print(f"Generating content with model: {model}")
    response = client.models.generate_content(
        model=model,
        contents="Hello",
        config=types.GenerateContentConfig(max_output_tokens=10)
    )
    
    print(f"SUCCESS: {response.text}")

except Exception as e:
    print(f"FAILURE: {e}")
