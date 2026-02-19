from google.cloud import spanner
client = spanner.Client(project="alloydbtest-374215")
instance = client.instance("virtual-retail-instance")
database = instance.database("catalog")
with database.snapshot() as snapshot:
    print(help(snapshot.execute_sql))
