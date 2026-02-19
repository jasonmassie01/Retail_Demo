import vertexai
from vertexai.generative_models import GenerativeModel
import os

PROJECT_ID = "alloydbtest-374215"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

def test_model(model_name):
    print(f"Testing {model_name}...")
    try:
        model = GenerativeModel(model_name)
        response = model.generate_content("Hello")
        print(f"SUCCESS: {model_name}")
        return True
    except Exception as e:
        print(f"FAILED: {model_name} - {e}")
        return False

models_to_test = [
    "gemini-1.5-flash-001",
    "gemini-1.5-flash",
    "gemini-1.5-pro-001",
    "gemini-1.5-pro",
    "gemini-1.0-pro-001",
    "gemini-1.0-pro",
    "gemini-pro"
]

print("Starting Model Diagnosis...")
for m in models_to_test:
    if test_model(m):
        break # Stop at first success
