from google.cloud import spanner

PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"

def verify_counts():
    spanner_client = spanner.Client(project=PROJECT_ID)
    instance = spanner_client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)

    with database.snapshot() as snapshot:
        # Check Products with Embeddings
        results = snapshot.execute_sql("SELECT count(*) FROM products WHERE embedding IS NOT NULL")
        product_count = list(results)[0][0]
        print(f"Products with Embeddings: {product_count}")

        # Check Users
        results = snapshot.execute_sql("SELECT count(*) FROM users")
        user_count = list(results)[0][0]
        print(f"Users: {user_count}")

        # Check Orders
        results = snapshot.execute_sql("SELECT count(*) FROM orders")
        order_count = list(results)[0][0]
        print(f"Orders: {order_count}")

        # Check Order Items (Graph Edges)
        results = snapshot.execute_sql("SELECT count(*) FROM order_items")
        item_count = list(results)[0][0]
        print(f"Order Items: {item_count}")

if __name__ == "__main__":
    verify_counts()
