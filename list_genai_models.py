from google import genai
import os

PROJECT_ID = "alloydbtest-374215"
LOCATION = "us-central1"

print(f"Listing models in {LOCATION}...")

try:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    
    for m in client.models.list():
        print(f"Found model: {m.name}")

except Exception as e:
    print(f"FAILURE: {e}")
