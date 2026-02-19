from google import genai
from google.genai import types
import os

PROJECT_ID = "alloydbtest-374215"
LOCATION = "us-central1"

print(f"Testing Gemini 3 Flash Preview in {PROJECT_ID}...")

# Try to initialize with Vertex AI params since we are in a GCP environment
try:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    
    model = "gemini-3-flash-preview"
    
    print(f"Generating content with model: {model}")
    response = client.models.generate_content(
        model=model,
        contents="Hello, do you work?",
        config=types.GenerateContentConfig(
            temperature=1,
            max_output_tokens=100
        )
    )
    
    print(f"SUCCESS: {response.text}")

except Exception as e:
    print(f"FAILURE: {e}")
