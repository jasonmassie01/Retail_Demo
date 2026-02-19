from google.cloud import spanner
print(dir(spanner))
try:
    from google.cloud.spanner_v1 import ExecuteSqlMode
    print("Found in spanner_v1")
except ImportError:
    print("Not in spanner_v1")
