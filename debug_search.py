import os
from google.cloud import spanner
from vertexai.language_models import TextEmbeddingModel
import time

# Configuration
PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"
EMBEDDING_MODEL_NAME = "text-embedding-005"

def test_search():
    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)
    
    print("Generating embedding...")
    model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)
    query_text = "summer dress"
    vector = model.get_embeddings([query_text])[0].values
    print(f"Embedding generated. Length: {len(vector)}")
    
    sql = """
    SELECT id, name, product_description, retail_price, product_image_uri,
           APPROX_COSINE_DISTANCE(embedding, @query_vector, options => JSON '{"num_leaves_to_search": 20}') as distance
    FROM products@{FORCE_INDEX=ProductsVectorIndex}
    WHERE embedding IS NOT NULL
    ORDER BY distance
    LIMIT 10
    """
    
    params = {"query_vector": vector}
    param_types = {
        "query_vector": spanner.param_types.Array(spanner.param_types.FLOAT64)
    }

    print("Executing query...")
    try:
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                sql,
                params=params,
                param_types=param_types
            )
            rows = list(results)
            print(f"Found {len(rows)} rows.")
            for row in rows:
                print(row)
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    test_search()
