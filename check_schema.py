from google.cloud import spanner

PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"

def check_indexes():
    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)
    
    with database.snapshot() as snapshot:
        print("Indexes on 'products':")
    with database.snapshot(multi_use=True) as snapshot:
        results = snapshot.execute_sql(
            "SELECT index_name, index_type, is_unique FROM information_schema.indexes WHERE table_name = 'products'"
        )
        for row in results:
            print(f"- {row[0]} ({row[1]})")
            
        print("\nIndex Columns:")
        results = snapshot.execute_sql(
            "SELECT index_name, column_name FROM information_schema.index_columns WHERE table_name = 'products' ORDER BY index_name, ordinal_position"
        )
        for row in results:
            print(f"- {row[0]}: {row[1]}")

if __name__ == "__main__":
    check_indexes()
