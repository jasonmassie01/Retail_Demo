import os
import time
from google.cloud import discoveryengine_v1alpha as discoveryengine

PROJECT_ID = "alloydbtest-374215"

def benchmark_rerank():
    print("Benchmarking Vertex AI RankService with 50 items...")
    try:
        client = discoveryengine.RankServiceClient()
        ranking_config = client.ranking_config_path(
            project=PROJECT_ID,
            location="global",
            ranking_config="default_ranking_config"
        )
        
        # Create 50 dummy records
        records = []
        for i in range(50):
            records.append(discoveryengine.RankingRecord(
                id=str(i),
                title=f"Product {i} with a very long title to simulate real data",
                content=f"This is a description for product {i}. " * 50  # ~2000 chars
            ))
        
        request = discoveryengine.RankRequest(
            ranking_config=ranking_config,
            model="semantic-ranker-512@latest",
            top_n=10,
            query="nice product",
            records=records
        )
        
        print(f"Sending RankRequest with {len(records)} records...")
        start = time.time()
        response = client.rank(request=request)
        duration = time.time() - start
        
        print(f"RankService call took {duration:.3f}s")
        
    except Exception as e:
        print(f"RankService Failed: {e}")

if __name__ == "__main__":
    benchmark_rerank()
