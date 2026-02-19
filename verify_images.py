from google.cloud import spanner

PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"

def verify_images():
    spanner_client = spanner.Client(project=PROJECT_ID)
    instance = spanner_client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)

    with database.snapshot() as snapshot:
        results = snapshot.execute_sql("SELECT product_image_uri FROM products WHERE product_image_uri IS NOT NULL LIMIT 5")
        for row in results:
            print(row[0])

if __name__ == "__main__":
    verify_images()
