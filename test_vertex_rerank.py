import os
import time
from google.cloud import discoveryengine_v1alpha as discoveryengine

PROJECT_ID = "alloydbtest-374215"

def test_vertex_rerank():
    print("Testing Vertex AI RankService...")
    try:
        client = discoveryengine.RankServiceClient()
        ranking_config = client.ranking_config_path(
            project=PROJECT_ID,
            location="global",
            ranking_config="default_ranking_config"
        )
        
        # Create dummy records
        records = [
            discoveryengine.RankingRecord(id="1", title="Red Summer Dress", content="A beautiful red dress for summer."),
            discoveryengine.RankingRecord(id="2", title="Blue Winter Coat", content="Warm coat for winter."),
            discoveryengine.RankingRecord(id="3", title="Summer Floral Dress", content="Floral print dress perfect for sunny days.")
        ]
        
        request = discoveryengine.RankRequest(
            ranking_config=ranking_config,
            model="semantic-ranker-512@latest",
            top_n=3,
            query="summer dress",
            records=records
        )
        
        print("Sending RankRequest...")
        start = time.time()
        response = client.rank(request=request)
        duration = time.time() - start
        
        print(f"RankService call took {duration:.3f}s")
        for r in response.records:
            print(f"ID: {r.id}, Score: {r.score}")
            
    except Exception as e:
        print(f"RankService Failed: {e}")

if __name__ == "__main__":
    test_vertex_rerank()
