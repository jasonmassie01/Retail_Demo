from google import genai
from google.genai import types
import os

PROJECT_ID = "alloydbtest-374215"
LOCATION = "us-central1"

print(f"Testing Gemini 2.0 Flash Lite with google-genai in {LOCATION}...")

try:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    
    # model = "gemini-2.0-flash-lite-preview-02-05"
    # Also trying the non-preview if specific one fails? No, stick to specific first.
    model = "gemini-2.0-flash-lite-preview-02-05"
    
    print(f"Generating content with model: {model}")
    response = client.models.generate_content(
        model=model,
        contents="Hello",
        config=types.GenerateContentConfig(max_output_tokens=10)
    )
    
    print(f"SUCCESS: {response.text}")

except Exception as e:
    print(f"FAILURE: {e}")
