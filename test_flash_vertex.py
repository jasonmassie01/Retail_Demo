import vertexai
from vertexai.generative_models import GenerativeModel
import os

PROJECT_ID = "alloydbtest-374215"
LOCATION = "us-central1"

print(f"Testing Gemini 2.0 Flash with vertexai in {LOCATION}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

try:
    model = GenerativeModel("gemini-2.0-flash-001")
    response = model.generate_content("Hello")
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAILURE: {e}")
