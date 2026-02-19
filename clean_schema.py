from google.cloud import spanner

PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"

def clean_schema():
    spanner_client = spanner.Client(project=PROJECT_ID)
    instance = spanner_client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)

    print(f"Cleaning schema in {DATABASE_ID}...")

    # Order matters: Graph -> Edges/Foreign Keys -> Tables
    statements = [
        "DROP PROPERTY GRAPH RetailGraph",
        "DROP INDEX ProductsFTS",
        "DROP INDEX ProductsVectorIndex",
        "DROP TABLE order_items",
        "DROP TABLE orders",
        "DROP TABLE products",
        "DROP TABLE users",
    ]
    
    # We need to run these one by one or in batch.
    # If a table doesn't exist, it will fail.
    # So we should run them individually and ignore "NotFound" errors.
    
    for stmt in statements:
        try:
            print(f"Executing: {stmt}")
            operation = database.update_ddl([stmt])
            operation.result(timeout=120)
            print("  Success")
        except Exception as e:
            if "NotFound" in str(e) or "does not exist" in str(e):
                print(f"  Skipped (Not Found): {e}")
            else:
                print(f"  Failed: {e}")

if __name__ == "__main__":
    clean_schema()
