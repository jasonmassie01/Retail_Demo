import os
from google.cloud import spanner
from vertexai.language_models import TextEmbeddingModel
import time

# Configuration
PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"
EMBEDDING_MODEL_NAME = "text-embedding-005"

def test_rrf_query():
    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)
    
    print("Generating embedding...")
    model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)
    query_text = "summer dress"
    vector = model.get_embeddings([query_text])[0].values
    
    # RRF Query based on user request, adapted for Spanner
    # Note: Spanner Vector Search works best with ORDER BY ... LIMIT
    # We will use CTEs with LIMITs to ensure index usage.
    
    sql = """
    WITH 
      -- 1. FTS Search
      fts_candidates AS (
        SELECT
          id,
          SCORE(description_tokens, @query_text) AS score
        FROM products
        WHERE SEARCH(description_tokens, @query_text)
        ORDER BY score DESC
        LIMIT 60
      ),
      fts_ranked AS (
        SELECT id, score, RANK() OVER (ORDER BY score DESC) as fts_rank
        FROM fts_candidates
      ),
      
      -- 2. Vector Search
      vector_candidates AS (
        SELECT
          id,
          APPROX_COSINE_DISTANCE(embedding, @query_vector, options => JSON '{"num_leaves_to_search": 20}') AS distance
        FROM products@{FORCE_INDEX=ProductsVectorIndex}
        WHERE embedding IS NOT NULL
        ORDER BY distance
        LIMIT 60
      ),
      vector_ranked AS (
        SELECT id, distance, RANK() OVER (ORDER BY distance) as vector_rank
        FROM vector_candidates
      ),
      
      -- 3. Combine
      combined_results AS (
        SELECT
          p.id,
          p.name,
          p.product_image_uri,
          p.retail_price,
          COALESCE(1.0 / (60 + v.vector_rank), 0.0) +
          COALESCE(1.0 / (60 + f.fts_rank), 0.0) AS rrf_score
        FROM products p
        LEFT JOIN vector_ranked v ON p.id = v.id
        LEFT JOIN fts_ranked f ON p.id = f.id
        WHERE v.id IS NOT NULL OR f.id IS NOT NULL
      )
      
    SELECT *
    FROM combined_results
    ORDER BY rrf_score DESC
    LIMIT 60
    """
    
    params = {"query_vector": vector, "query_text": query_text}
    param_types = {
        "query_vector": spanner.param_types.Array(spanner.param_types.FLOAT64),
        "query_text": spanner.param_types.STRING
    }

    print("Executing RRF query...")
    try:
        with database.snapshot() as snapshot:
            results = list(snapshot.execute_sql(
                sql,
                params=params,
                param_types=param_types
            ))
            print(f"Found {len(results)} rows.")
            for row in results[:5]:
                print(row)
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    test_rrf_query()
