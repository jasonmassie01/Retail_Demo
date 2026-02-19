from google.cloud import spanner

PROJECT_ID = "alloydbtest-374215"
INSTANCE_DISPLAY_NAME = "Virtual Retail Spanner"
DATABASE_NAME = "catalog"

def verify_spanner():
    spanner_client = spanner.Client(project=PROJECT_ID)
    
    # List instances to find the one with the display name
    instance_id = None
    print("Listing instances...")
    for instance in spanner_client.list_instances():
        print(f"Found instance: {instance.name} (Display Name: {instance.display_name})")
        if instance.display_name == INSTANCE_DISPLAY_NAME:
            instance_id = instance.name.split('/')[-1]
            print(f"Matched Instance ID: {instance_id}")
            break
            
    if not instance_id:
        print(f"Error: Instance with display name '{INSTANCE_DISPLAY_NAME}' not found.")
        # Fallback to checking if 'virtual-retail-spanner' exists as ID
        instance_id = "virtual-retail-spanner" 
        print(f"Checking if instance ID '{instance_id}' exists directly...")
        instance = spanner_client.instance(instance_id)
        if not instance.exists():
            print(f"Instance {instance_id} does not exist.")
            return
        print(f"Instance {instance_id} exists.")

    instance = spanner_client.instance(instance_id)
    database = instance.database(DATABASE_NAME)
    
    if not database.exists():
        print(f"Error: Database '{DATABASE_NAME}' does not exist in instance '{instance_id}'.")
        # Try to list databases
        print("Listing databases in instance:")
        for db in instance.list_databases():
            print(f" - {db.name}")
    else:
        print(f"Database '{DATABASE_NAME}' exists verified.")
        
        # Check for tables
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            print("Tables found:")
            for row in results:
                print(f" - {row[0]}")

if __name__ == "__main__":
    verify_spanner()
