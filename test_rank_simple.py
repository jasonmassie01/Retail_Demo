import os
from google.cloud import spanner

PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"

def test_rank():
    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)
    
    sql = """
    SELECT id, name, RANK() OVER (ORDER BY retail_price DESC) as price_rank
    FROM products
    LIMIT 5
    """
    
    print("Executing RANK query...")
    try:
        with database.snapshot() as snapshot:
            results = list(snapshot.execute_sql(sql))
            print(f"Found {len(results)} rows.")
            for row in results:
                print(row)
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    test_rank()
