import vertexai
from vertexai.generative_models import GenerativeModel
import os

PROJECT_ID = "alloydbtest-374215"
LOCATION = "us-central1"

print(f"Testing Gemini 2.5 Flash Lite in {LOCATION}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Try both short and full names
models_to_test = [
    "gemini-2.5-flash-lite-preview-09-2025",
    "publishers/google/models/gemini-2.5-flash-lite-preview-09-2025"
]

for model_id in models_to_test:
    print(f"\nTesting model ID: {model_id}")
    try:
        model = GenerativeModel(model_id)
        response = model.generate_content("Hello")
        print(f"SUCCESS: {response.text}")
        break
    except Exception as e:
        print(f"FAILURE: {e}")
