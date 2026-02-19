import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "alloydbtest-374215"
vertexai.init(project=PROJECT_ID, location="us-central1")

def list_models():
    print("Attempting to use gemini-1.5-flash...")
    try:
        model = GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello")
        print(f"gemini-1.5-flash works! Response: {response.text}")
    except Exception as e:
        print(f"gemini-1.5-flash failed: {e}")

    print("\nAttempting to use gemini-1.0-pro...")
    try:
        model = GenerativeModel("gemini-1.0-pro")
        response = model.generate_content("Hello")
        print(f"gemini-1.0-pro works! Response: {response.text}")
    except Exception as e:
        print(f"gemini-1.0-pro failed: {e}")

if __name__ == "__main__":
    list_models()
