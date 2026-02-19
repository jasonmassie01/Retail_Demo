import time
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

PROJECT_ID = "alloydbtest-374215"
vertexai.init(project=PROJECT_ID, location="us-central1")

def benchmark_flash():
    print("Benchmarking Gemini 1.5 Flash for Reranking (50 items)...")
    model = GenerativeModel("gemini-1.5-flash-001")
    
    # Create 50 items
    items = []
    for i in range(50):
        items.append(f"ID: {i}, Title: Product {i}, Content: Nice product {i}")
    
    prompt = f"""
    You are a ranking assistant. Rank the following 50 items based on relevance to the query "nice product".
    Return the IDs of the top 10 items in order, comma separated.
    
    Items:
    {chr(10).join(items)}
    """
    
    try:
        start = time.time()
        response = model.generate_content(prompt)
        duration = time.time() - start
        
        print(f"Gemini 1.5 Flash call took {duration:.3f}s")
        print(response.text)
    except Exception as e:
        print(f"Gemini 1.5 Flash Failed: {e}")

if __name__ == "__main__":
    benchmark_flash()
