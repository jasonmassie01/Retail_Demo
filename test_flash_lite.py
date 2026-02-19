import vertexai
from vertexai.generative_models import GenerativeModel
import os

PROJECT_ID = "alloydbtest-374215"
# Try us-central1 first
LOCATION = "us-central1"

print(f"Initializing Vertex AI in {LOCATION}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

model_id = "gemini-2.0-flash-lite-preview-02-05"

print(f"Testing model: {model_id}")

try:
    model = GenerativeModel(model_id)
    response = model.generate_content("Are you working?")
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAILURE: {e}")
