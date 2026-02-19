from google.cloud import spanner
import inspect

client = spanner.Client(project="alloydbtest-374215")
instance = client.instance("virtual-retail-instance")
database = instance.database("catalog")
with database.snapshot() as snapshot:
    print(inspect.signature(snapshot.execute_sql))
