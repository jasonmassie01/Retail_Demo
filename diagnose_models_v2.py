import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextGenerationModel
import os

PROJECT_ID = "alloydbtest-374215"
LOCATION = "us-central1"

print(f"Initializing Vertex AI in {LOCATION}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

def test_gemini(model_name):
    print(f"Testing Gemini: {model_name}...")
    try:
        model = GenerativeModel(model_name)
        response = model.generate_content("Hello")
        print(f"SUCCESS: {model_name}")
        return True
    except Exception as e:
        print(f"FAILED: {model_name}")
        return False

def test_bison(model_name):
    print(f"Testing Bison: {model_name}...")
    try:
        model = TextGenerationModel.from_pretrained(model_name)
        response = model.predict("Hello")
        print(f"SUCCESS: {model_name}")
        return True
    except Exception as e:
        print(f"FAILED: {model_name}")
        return False

models_gemini = [
    "gemini-pro",
    "gemini-1.5-pro-001",
    "gemini-1.5-flash-001",
    "gemini-1.0-pro-001",
]

models_bison = [
    "text-bison",
    "text-bison@001",
    "text-bison@002",
    "text-bison-32k",
]

found = False
for m in models_gemini:
    if test_gemini(m):
        found = True
        break

if not found:
    for m in models_bison:
        if test_bison(m):
            found = True
            break
