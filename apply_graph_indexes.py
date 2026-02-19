from google.cloud import spanner

PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"

def apply_indexes():
    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)
    
    operation = database.update_ddl([
        "CREATE INDEX OrderItemsByProduct ON order_items(product_id) STORING (user_id)",
        "CREATE INDEX OrderItemsByUser ON order_items(user_id) STORING (product_id)"
    ])
    
    print("Waiting for operation to complete...")
    operation.result(timeout=120)
    print("Indexes created successfully.")

if __name__ == "__main__":
    apply_indexes()
