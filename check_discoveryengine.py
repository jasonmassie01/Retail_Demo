try:
    from google.cloud import discoveryengine_v1beta as discoveryengine
    print("discoveryengine_v1beta imported successfully")
except ImportError:
    print("discoveryengine_v1beta not found")

try:
    from google.cloud import discoveryengine
    print("discoveryengine imported successfully")
except ImportError:
    print("discoveryengine not found")
