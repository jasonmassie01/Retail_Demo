from google.cloud import spanner
client = spanner.Client(project="alloydbtest-374215")
instance = client.instance("virtual-retail-instance")
database = instance.database("catalog")
print(help(database.snapshot))
