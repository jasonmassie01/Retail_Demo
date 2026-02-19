from google.cloud import alloydb_v1

PROJECT_ID = "alloydbtest-374215"
REGION = "us-central1"
CLUSTER = "hybridsearch"

def list_instances():
    client = alloydb_v1.AlloyDBAdminClient()
    parent = f"projects/{PROJECT_ID}/locations/{REGION}/clusters/{CLUSTER}"
    
    print(f"Listing instances in {parent}...")
    try:
        response = client.list_instances(parent=parent)
        for instance in response:
            print(f"Instance: {instance.name}")
            print(f"  State: {instance.state}")
            print(f"  IP Type: {instance.ip_config}")
            print(f"  Public IP Enabled: {instance.public_ip_enabled}") # Assuming this field exists or similar
            # Check detailed config
            print(f"  Config: {instance}")
    except Exception as e:
        print(f"Error listing instances: {e}")

if __name__ == "__main__":
    list_instances()
