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
            # Print available attributes to debug
            # print(dir(instance)) 
            # Check for public IP config
            # It might be in 'network_config' or similar?
            # Actually, AlloyDB instances have 'ip_address' (private) and 'public_ip_address' if enabled
            print(f"  IP Address (Private): {instance.ip_address}")
            print(f"  Public IP Address: {instance.public_ip_address}")
            # Check if public IP is enabled
            # instance.network_config might exist on Cluster, not Instance?
            # Instance has 'availability_type', 'gce_zone', etc.
    except Exception as e:
        print(f"Error listing instances: {e}")

if __name__ == "__main__":
    list_instances()
