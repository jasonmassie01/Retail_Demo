from google.cloud import spanner
from google.api_core.exceptions import GoogleAPICallError

PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance" # Confirmed via verify_spanner.py
DATABASE_ID = "catalog"

def apply_schema():
    spanner_client = spanner.Client(project=PROJECT_ID)
    instance = spanner_client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)

    print(f"Applying schema to {DATABASE_ID} on {INSTANCE_ID}...")

    # Read schema file
    with open("spanner_schema.sql", "r") as f:
        schema_sql = f.read()

    # Split into statements
    # Simple split by semicolon, assuming no semicolons in strings for this simple schema
    statements = [s.strip() for s in schema_sql.split(";") if s.strip()]

    operation = database.update_ddl(statements)
    
    print("Waiting for operation to complete...")
    try:
        operation.result(timeout=600) # 10 minutes timeout
        print("Schema applied successfully.")
    except Exception as e:
        print(f"Error applying schema: {e}")
        # Print individual errors if possible, but update_ddl usually fails as a batch or stops on first error
        print("Check if tables already exist or syntax error.")

if __name__ == "__main__":
    apply_schema()
