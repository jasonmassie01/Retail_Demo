from app import search_products, get_embedding_model
import streamlit as st

# Mock session state
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []

# Patch st.error
def mock_error(msg):
    print(f"ERROR CAUGHT: {msg}")
st.error = mock_error

def test():
    query = "summer dress"
    print(f"Testing search for: '{query}'")
    results = search_products(query)
    print(f"Total Results: {len(results)}")
    for r in results:
        print(f"- {r[1]} (${r[3]}) - Score: {r[5]}")

if __name__ == "__main__":
    test()
