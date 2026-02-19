import sys
import os
from unittest.mock import MagicMock

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock streamlit
mock_st = MagicMock()
sys.modules["streamlit"] = mock_st

class MockSessionState(dict):
    def __getattr__(self, key):
        if key in self:
            return self[key]
        # Return None or raise? Streamlit raises.
        # But for mocks, maybe we want forgiveness?
        # Actually app.py checks 'if "messages" not in ...' 
        raise AttributeError(key)
    def __setattr__(self, key, value):
        self[key] = value

mock_st.session_state = MockSessionState()
mock_st.query_params = {}
mock_st.secrets = {}

# Mock google.cloud
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.spanner"] = MagicMock()
sys.modules["google.cloud.spanner_v1.types"] = MagicMock()
sys.modules["vertexai"] = MagicMock()
sys.modules["vertexai.language_models"] = MagicMock()
sys.modules["vertexai.generative_models"] = MagicMock()

# Import app
try:
    import app
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_search_modes():
    print("Starting Test...")
    
    # Mock DB
    mock_db = MagicMock()
    app.get_spanner_database = MagicMock(return_value=mock_db)
    
    mock_snapshot = MagicMock()
    mock_db.snapshot.return_value.__enter__.return_value = mock_snapshot
    mock_snapshot.execute_sql.return_value = [] # Return empty list
    
    # Mock Embeddings
    mock_model = MagicMock()
    app.get_embedding_model = MagicMock(return_value=mock_model)
    mock_embedding = MagicMock()
    mock_embedding.values = [0.1, 0.2]
    mock_model.get_embeddings.return_value = [mock_embedding]

    # Test 1: Wildcard
    print("\n--- Testing Wildcard Mode ---")
    mock_st.session_state.search_mode = "SQL Wildcard (LIKE %...%)"
    app.search_products("red dress")
    # Verify SQL
    if mock_snapshot.execute_sql.call_args_list:
        calls = mock_snapshot.execute_sql.call_args_list
        # Check all calls for wildcards
        found = False
        for call in calls:
            sql_arg = call[0][0] if call[0] else ""
            if "LIKE" in sql_arg and "LOWER(name)" in sql_arg:
                found = True
                print("PASS: Wildcard SQL looks correct.")
                break
        if not found:
             print(f"FAIL: Wildcard SQL incorrect: {calls}")
    else:
        print("FAIL: No execute_sql calls")

    # Reset mocks
    mock_snapshot.execute_sql.reset_mock()

    # Test 2: Vector Only
    print("\n--- Testing Vector Only Mode ---")
    mock_st.session_state.search_mode = "Vector Only"
    app.search_products("red dress")
    if mock_snapshot.execute_sql.call_args_list:
        calls = mock_snapshot.execute_sql.call_args_list
        found = False
        for call in calls:
            sql_arg = call[0][0] if call[0] else ""
            if "APPROX_COSINE_DISTANCE" in sql_arg:
                found = True
                print("PASS: Vector SQL looks correct.")
                break
        if not found:
             print(f"FAIL: Vector SQL incorrect: {calls}")
    else:
         print("FAIL: No execute_sql calls")
    mock_snapshot.execute_sql.reset_mock()

    # Test 3: FTS Only
    print("\n--- Testing FTS Only Mode ---")
    mock_st.session_state.search_mode = "Full Text Search Only"
    app.search_products("red dress")
    if mock_snapshot.execute_sql.call_args_list:
        calls = mock_snapshot.execute_sql.call_args_list
        found = False
        for call in calls:
            sql_arg = call[0][0] if call[0] else ""
            if "SEARCH(description_tokens" in sql_arg:
                found = True
                print("PASS: FTS SQL looks correct.")
                break
        if not found:
             print(f"FAIL: FTS SQL incorrect: {calls}")
    else:
         print("FAIL: No execute_sql calls")
        
    print("\nDone.")

if __name__ == "__main__":
    test_search_modes()
