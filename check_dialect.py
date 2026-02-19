from google.cloud import spanner

PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"

def check_dialect():
    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)
    
    # Reload database to get dialect
    database.reload()
    print(f"Dialect: {database.database_dialect}")

if __name__ == "__main__":
    check_dialect()
