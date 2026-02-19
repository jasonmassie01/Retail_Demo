from google.cloud import spanner

PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"

def check_indexes():
    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)
    
    with database.snapshot() as snapshot:
        print("Indexes on 'order_items':")
        results = snapshot.execute_sql(
            "SELECT index_name, index_type, is_unique FROM information_schema.indexes WHERE table_name = 'order_items'"
        )
        for row in results:
            print(f"- {row[0]} ({row[1]})")

if __name__ == "__main__":
    check_indexes()
