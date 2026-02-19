from google.cloud import spanner
from vertexai.language_models import TextEmbeddingModel
import vertexai

PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

def get_embedding():
    model = TextEmbeddingModel.from_pretrained("text-embedding-005")
    embeddings = model.get_embeddings(["test query"])
    return embeddings[0].values

def test_query():
    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)
    
    vector = get_embedding()
    
    # Test 1: APPROX_COSINE_DISTANCE without options (Expected Failure)
    sql1 = """
    SELECT id, APPROX_COSINE_DISTANCE(embedding, @query_vector) as distance
    FROM products@{FORCE_INDEX=ProductsVectorIndex}
    WHERE embedding IS NOT NULL
    ORDER BY distance
    LIMIT 1
    """
    
    # Test 2: APPROX_COSINE_DISTANCE WITH options (Expected Success)
    # Options for ScaNN are typically '{"num_leaves_to_search": 10}' BUT Spanner might want a string literal that parses as a proto?
    # Actually, let's try just empty options first or standard JSON if the error was just about the keys?
    # The error "Expected identifier, got: {" suggests it wants a proto text format, NOT JSON.
    # Proto text format: 'num_leaves_to_search: 10'
    
    sql2 = """
    SELECT id, APPROX_COSINE_DISTANCE(embedding, @query_vector, options => 'num_leaves_to_search: 10') as distance
    FROM products@{FORCE_INDEX=ProductsVectorIndex}
    WHERE embedding IS NOT NULL
    ORDER BY distance
    LIMIT 1
    """

    params = {"query_vector": vector}
    param_types = {"query_vector": spanner.param_types.Array(spanner.param_types.FLOAT64)}

    print("Testing SQL 1 (No options)...")
    try:
        with database.snapshot() as snapshot:
            results = list(snapshot.execute_sql(sql1, params=params, param_types=param_types))
            print("SQL 1 Success")
    except Exception as e:
        print(f"SQL 1 Failed: {e}")

    print("\nTesting SQL 2 (With options)...")
    try:
        with database.snapshot() as snapshot:
            results = list(snapshot.execute_sql(sql2, params=params, param_types=param_types))
            print("SQL 2 Success")
    except Exception as e:
        print(f"SQL 2 Failed: {e}")

if __name__ == "__main__":
    test_query()
