import streamlit as st
import time
import uuid
import json
import logging
import requests
import datetime
import random
import pandas as pd

# --- NUCLEAR HACK: Disable Spanner Metrics Exporter (Module Level) ---
import sys
from unittest.mock import MagicMock

# Create a mock module
mock_metrics = MagicMock()
# Ensure MetricsExporter class exists and does nothing
class MockMetricsExporter:
    def __init__(self, *args, **kwargs): pass
    def export(self): pass

mock_metrics.MetricsExporter = MockMetricsExporter
# Inject into sys.modules to intercept ALL imports of this module
sys.modules["google.cloud.spanner_v1.metrics.metrics_exporter"] = mock_metrics
print("NUCLEAR PATCH: Spanner MetricsExporter module has been mocked out.")
# ---------------------------------------------------------------------

from google.cloud import spanner
from google.cloud import aiplatform

from google.cloud.spanner_v1.types import ExecuteSqlRequest
from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel, GenerationConfig

# --- Configuration ---
PROJECT_ID = "alloydbtest-374215"
INSTANCE_ID = "virtual-retail-instance"
DATABASE_ID = "catalog"
EMBEDDING_MODEL_NAME = "text-embedding-005"
LOCATION = "us-central1"

# --- Setup & State ---
st.set_page_config(page_title="Retail AI Assistant", layout="wide", initial_sidebar_state="expanded")

# Initialize Vertex AI
import vertexai
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Custom CSS for Gemini-like feel
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    .chat-container { max_width: 800px; margin: 0 auto; }
    .product-card {
        border-radius: 12px;
        padding: 16px;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        margin-bottom: 16px;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .product-title { font-weight: 600; font-size: 1.05rem; margin-bottom: 4px; color: #1a73e8; }
    .product-price { font-weight: 700; color: #1f1f1f; font-size: 1.1rem; }
    .debug-info { font-family: monospace; font-size: 0.85rem; color: #d63384; }
    .rec-section { background-color: #f1f3f4; padding: 20px; border-radius: 12px; margin-top: 24px; }
</style>
""", unsafe_allow_html=True)

# --- Resources ---
@st.cache_resource
def get_spanner_database():
    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    return instance.database(DATABASE_ID)

@st.cache_resource
def get_embedding_model():
    return TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)

@st.cache_resource
def get_rank_service_client():
    from google.cloud import discoveryengine_v1alpha as discoveryengine
    return discoveryengine.RankServiceClient()

@st.cache_resource
def get_gemini_model():
    from vertexai.generative_models import GenerativeModel
    return GenerativeModel("gemini-2.0-flash-001")

@st.cache_data(ttl=3600)
def validate_image_url(url):
    try:
        response = requests.head(url, timeout=1.0)
        return response.status_code == 200
    except:
        return False

def transform_image_uri(uri):
    fallback = "https://storage.googleapis.com/github-repo/img/gemini/retail/dress.jpg"
    if not uri: return fallback
    
    # GEDB Project Fix
    if "genwealth-gen-vid/product-images" in uri:
        filename = uri.split('/')[-1]
        public_url = f"https://storage.googleapis.com/pr-public-demo-data/alloydb-retail-demo/product-images-branded/{filename}"
        if validate_image_url(public_url): return public_url

    http_url = uri
    if uri.startswith("gs://"):
        http_url = uri.replace("gs://", "https://storage.googleapis.com/")
    
    if validate_image_url(http_url): return http_url
    return fallback

def log_debug(query, params=None, param_types=None, duration=0):
    display_params = params.copy() if params and isinstance(params, dict) else params
    if isinstance(display_params, dict):
        for k, v in display_params.items():
            if isinstance(v, list) and len(v) > 20:
                display_params[k] = f"VECTOR(len={len(v)})"

    st.session_state.debug_logs.insert(0, {
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "query": query,
        "params": str(display_params),
        "raw_params": params,
        "param_types": param_types,
        "duration": f"{duration*1000:.1f}ms"
    })

def explain_query(sql, params, param_types):
    db = get_spanner_database()
    try:
        with db.snapshot() as snapshot:
            results = snapshot.execute_sql(
                sql,
                params=params,
                param_types=param_types,
                query_mode=ExecuteSqlRequest.QueryMode.PROFILE
            )
            # Must consume results to get stats
            list(results)
            return results.stats
    except Exception as e:
        return {"error": str(e)}

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm Aria. What can I help you find today?"}]

# Handle Query Params for Navigation
query_params = st.query_params
if "product_id" in query_params:
    pid = query_params["product_id"]
    # Fetch product details if not selected
    # We need to fetch it to populate selected_product
    # But for now, let's just set the ID and let render_detail handle it? 
    # Actually render_detail expects selected_product tuple. 
    # We need a helper to fetch by ID.
    try:
         # Quick fetch helper
         db = get_spanner_database()
         with db.snapshot() as snapshot:
             res = snapshot.execute_sql(
                 "SELECT id, name, product_description, retail_price, product_image_uri FROM products WHERE id = @pid",
                 params={"pid": int(pid)},
                 param_types={"pid": spanner.param_types.INT64}
             )
             rows = list(res)
             if rows:
                 r = rows[0]
                 st.session_state.selected_product = (r[0], r[1], r[2], r[3], r[4], 0)
                 st.session_state.page = "detail"
                 # Clear param so we don't get stuck
                 st.query_params.clear()
    except Exception as e:
        print(f"Error fetching product {pid}: {e}")

if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []
if "show_debug" not in st.session_state:
    st.session_state.show_debug = True # Debug on by default, but hidden if empty
if "search_mode" not in st.session_state:
    st.session_state.search_mode = "Hybrid (Vector + FTS)"



# --- Logic ---
def query_understanding(query):
    try:
        model = get_gemini_model()
        prompt = f"""
        You are a search query parser. Extract search parameters from the user's query.
        Return a JSON object with the following fields:
        - query: The core search text (remove price constraints).
        - min_price: The minimum price (null if not specified).
        - max_price: The maximum price (null if not specified).
        - category: The category if specified (e.g. "dress", "shoes") otherwise null.
        
        User Query: "{query}"
        """
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        log_debug("Query Understanding Failed", {"error": str(e)}, None, 0)
        st.warning(f"Query Understanding (Gemini) failed: {e}. Falling back to keyword search.")
        return {"query": query, "min_price": None, "max_price": None, "category": None}

def enhance_query(query):
    """
    Uses Gemini to expand/rewrite the query for better FTS recall.
    """
    try:
        model = get_gemini_model()
        prompt = f"""
        You are a search query optimizer. Rewrite the following user query to improve retrieval in a full-text search engine.
        
        Rules:
        1.  You MUST expand the query with multiple synonyms to ensure broad recall.
        2.  Use the OR operator between ALL terms.
        3.  Example: "red dress" -> "red OR dress OR gown OR frock OR crimson".
        4.  Example: "shoes" -> "shoes OR sneakers OR boots OR footwear".
        5.  Do not use AND. Use OR to maximize results.
        6.  Return ONLY the query string.
        
        User Query: "{query}"
        Rewritten Query:
        """
        response = model.generate_content(prompt)
        enhanced = response.text.strip()
        
        # Fallback: If Gemini didn't add ORs, force it for multi-word queries
        if " OR " not in enhanced and " " in enhanced:
            # If it just returned the original or a phrase, split by space and join with OR
            enhanced = " OR ".join(enhanced.split())
            
        # Fallback if empty or too long
        if not enhanced or len(enhanced) > len(query) * 4:
            return " OR ".join(query.split()) # Simple OR expansion of original
            
        return enhanced
    except Exception as e:
        log_debug("Enhanced Query Failed", {"error": str(e)}, None, 0)
        return query

def analyze_request(query, history):
    """
    Combines Intent Detection and Query Understanding into a single LLM call.
    Returns: {
        "intent": "SEARCH" | "CHAT",
        "search_params": { ... } (if SEARCH)
    }
    """
    try:
        model = get_gemini_model()
        prompt = f"""
        You are a smart shopping assistant. Analyze the user's query and history.
        
        1. Determine Intent:
           - SEARCH: User wants to find products, filter items, or explicitly asks for "red dress".
           - CHAT: User is greeting, engaging in small talk, or asking clarification without new search criteria.
           
        2. Extract Search Parameters (if SEARCH):
           - query: The core product terms (e.g. "red dress")
           - min_price: number or null
           - max_price: number or null
           - category: string or null
        
        Last Query: "{query}"
        
        Return JSON: {{ "intent": "SEARCH" | "CHAT", "search_params": {{ "query": "...", "min_price": ..., "max_price": ..., "category": ... }} }}
        """
        
        t0 = time.time()
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(response_mime_type="application/json")
        )
        duration = time.time() - t0
        
        result = json.loads(response.text)
        log_debug("Analyze Request", result, None, duration)
        return result
    except Exception as e:
        log_debug("Analyze Request Failed", {"error": str(e)}, None, 0)
        # Fallback to simple SEARCH with no filters
        return {"intent": "SEARCH", "search_params": {"query": query, "min_price": None, "max_price": None, "category": None}}

# detect_intent is now deprecated/wrapped by analyze_request, but keeping generate_response separate
def generate_response(query, results, history):
    try:
        model = get_gemini_model()
        
        # Summarize products for context
        product_context = ""
        if results:
            for p in results[:5]: # Top 5 context
                product_context += f"- {p[1]} (${p[3]}): {p[2][:100]}...\n"
        
        prompt = f"""
        You are Aria, a helpful and stylish retail shopping assistant.
        
        User Query: "{query}"
        
        Found Products:
        {product_context}
        
        History:
        {history[-3:] if history else []}
        
        Task:
        1. If products were found, mention 1-2 key highlights or trends among them.
        2. If no products, suggest alternatives.
        3. Be concise (max 2 sentences).
        4. Encourage the user to click or ask more.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "I found these items for you!"

def search_products(user_query, parsed_query=None):
    mode = st.session_state.get("search_mode", "Hybrid (Vector + FTS)")
    t_start = time.time()
    
    # 0. Query Understanding (if not already done)
    if not parsed_query:
        parsed_query = query_understanding(user_query) # Fallback to old method if needed
    
    query_text = parsed_query.get("query", user_query)
    min_price = parsed_query.get("min_price")
    max_price = parsed_query.get("max_price")
    category = parsed_query.get("category")
    query_text = parsed_query.get("query", user_query)
    min_price = parsed_query.get("min_price")
    max_price = parsed_query.get("max_price")
    category = parsed_query.get("category")
    
    if min_price is not None: st.toast(f"Filter: Price >= ${min_price}", icon="💰")
    if max_price is not None: st.toast(f"Filter: Price <= ${max_price}", icon="💰")
    if category is not None: st.toast(f"Filter: Category = {category}", icon="🏷️")
    
    # DEBUG: Show parsed query in UI to confirm Gemini output
    if st.session_state.get("show_debug", False):
        st.info(f"Parsed Query: {parsed_query}")
        st.info(f"Search Mode: {mode}")

    db = get_spanner_database()
    final_results = []
    
    try:
        with db.snapshot(multi_use=True) as snapshot:
            
            # --- Retrieval Phase ---
            candidates = {} # Map ID -> Record tuple
            
            # 1. Wildcard Retrieval
            if mode == "SQL Wildcard (LIKE %...%)":
                wildcard_sql = """
                SELECT id, name, product_description, retail_price, product_image_uri, 0.0 as initial_score
                FROM products
                WHERE LOWER(name) LIKE @query OR LOWER(product_description) LIKE @query
                LIMIT 30
                """
                like_query = f"%{query_text.lower()}%"
                params = {"query": like_query}
                param_types = {"query": spanner.param_types.STRING}
                
                t0 = time.time()
                results = list(snapshot.execute_sql(wildcard_sql, params=params, param_types=param_types))
                t_wildcard = time.time() - t0
                log_debug(wildcard_sql, params, param_types, t_wildcard)
                st.session_state.last_timing = f"Wildcard: {t_wildcard*1000:.0f}ms"
                
                for r in results: candidates[r[0]] = (r[0], r[1], r[2], r[3], r[4], r[5])

            # 1.5 Enhanced Query (Pre-processing for FTS)
            # REPLACED by Spanner Native enhance_query=>true in step 3
            if mode == "Full Text Search + Enhanced Query":
                st.info(f"✨ Using Spanner Native Enhanced Query")

            # 2. Vector Retrieval
            if mode in ["Hybrid (Vector + FTS)", "Vector Only"]:
                model = get_embedding_model()
                embeddings = model.get_embeddings([query_text])
                vector = embeddings[0].values
    
                where_clause = "WHERE embedding IS NOT NULL"
                params = {"query_vector": vector}
                param_types = {"query_vector": spanner.param_types.Array(spanner.param_types.FLOAT64)}
                
                if min_price is not None:
                    where_clause += " AND (retail_price >= @min_price)"
                    params["min_price"] = float(min_price)
                    param_types["min_price"] = spanner.param_types.FLOAT64
                    
                if max_price is not None:
                    where_clause += " AND (retail_price <= @max_price)"
                    params["max_price"] = float(max_price)
                    param_types["max_price"] = spanner.param_types.FLOAT64
                
                sql_vector = f"""
                SELECT id, name, product_description, retail_price, product_image_uri,
                       APPROX_COSINE_DISTANCE(embedding, @query_vector, options => 'num_leaves_to_search: 30') as distance
                FROM products@{{FORCE_INDEX=ProductsVectorIndex}}
                {where_clause}
                ORDER BY distance
                LIMIT 30
                """
                
                t0 = time.time()
                results_v = list(snapshot.execute_sql(sql_vector, params=params, param_types=param_types))
                t_vector = time.time() - t0
                log_debug(sql_vector, params, param_types, t_vector)
                
                for r in results_v: candidates[r[0]] = (r[0], r[1], r[2], r[3], r[4], r[5])

            # 3. FTS Retrieval
            if mode in ["Hybrid (Vector + FTS)", "Full Text Search Only", "Full Text Search + Enhanced Query"]:
                # Default FTS
                search_operator = "SEARCH(description_tokens, @query_text)"
                
                # Spanner Native Enhanced Query
                if mode == "Full Text Search + Enhanced Query":
                    search_operator = "SEARCH(description_tokens, @query_text, enhance_query=>true)"

                fts_where = f"WHERE {search_operator}"
                fts_params = {"query_text": query_text}
                fts_param_types = {"query_text": spanner.param_types.STRING}
                
                if min_price is not None:
                    fts_where += " AND (retail_price >= @min_price)"
                    fts_params["min_price"] = float(min_price)
                    fts_param_types["min_price"] = spanner.param_types.FLOAT64
                    
                if max_price is not None:
                    fts_where += " AND (retail_price <= @max_price)"
                    fts_params["max_price"] = float(max_price)
                    fts_param_types["max_price"] = spanner.param_types.FLOAT64
    
                sql_fts = f"""
                SELECT id, name, product_description, retail_price, product_image_uri,
                       SCORE(description_tokens, @query_text) as score
                FROM products
                {fts_where}
                ORDER BY score DESC
                LIMIT 30
                """
                
                t0 = time.time()
                results_f = list(snapshot.execute_sql(sql_fts, params=fts_params, param_types=fts_param_types))
                t_fts = time.time() - t0
                log_debug(sql_fts, fts_params, fts_param_types, t_fts)
                
                for r in results_f: candidates[r[0]] = (r[0], r[1], r[2], r[3], r[4], r[5])

            # --- Ranking Phase ---
            unique_candidates = list(candidates.values())
            
            reranker_model = st.session_state.get("reranker_model", "Vertex AI Semantic Ranker")
            
            if reranker_model == "Vertex AI Semantic Ranker":
                # Vertex AI Reranking (Standard)
                from google.cloud import discoveryengine_v1alpha as discoveryengine
                
                model_id = "semantic-ranker-512@latest"
                
                t0 = time.time()
                
                # Limit candidates for Reranking (Cost/Latency optimization)
                rerank_candidates = {}
                # Take all unique candidates up to a limit (e.g., 50)
                # If we have too many, we might want to prioritize... but for now just take first 50
                limited_unique = unique_candidates[:50]
                for r in limited_unique: rerank_candidates[r[0]] = r

                # Prepare records for ranking
                records = []
                for row in limited_unique:
                    content = row[2] if row[2] else ""
                    if len(content) > 500: content = content[:500]
                        
                    records.append(discoveryengine.RankingRecord(
                        id=str(row[0]),
                        title=row[1],
                        content=content
                    ))
                
                if not records:
                    return []

                # Call Rank Service (Cached)
                client = get_rank_service_client()
                ranking_config = client.ranking_config_path(
                    project=PROJECT_ID,
                    location="global",
                    ranking_config="default_ranking_config"
                )
                
                request = discoveryengine.RankRequest(
                    ranking_config=ranking_config,
                    model=model_id,
                    top_n=9,
                    query=query_text,
                    records=records
                )
                
                try:
                    response = client.rank(request=request)
                    t_rerank = time.time() - t0
                    log_debug("Vertex AI Rerank", {"candidate_count": len(records), "model": model_id}, None, t_rerank)
                    st.session_state.last_timing = f"Rerank: {t_rerank*1000:.0f}ms"
                    
                    # Process Reranked Results
                    final_results = []
                    for r in response.records:
                        pid = int(r.id)
                        if pid in rerank_candidates:
                            row = rerank_candidates[pid]
                            final_results.append((
                                row[0], row[1], row[2], row[3], row[4], r.score
                            ))
                except Exception as e:
                    import traceback
                    st.error(f"Reranking failed: {e}")
                    # Log full traceback
                    print(traceback.format_exc())
                    log_debug("Vertex AI Rerank Failed", {"error": str(e), "traceback": traceback.format_exc()}, None, 0)
                    final_results = [] 
            else:
                # Python-side RRF (Simple fallback if selected)
                # Note: RRF usually requires multiple ranked lists. 
                # If we only have one list (e.g. Vector Only), RRF is just 1/rank.
                # If we have merged candidates without clear ranks (Wildcard), we might just default to original order or score.
                
                # For simplicity, if we have multiple lists (Hybrid), we do RRF. 
                # If single list, we just return the list sorted by initial score/distance?
                # Actually, user wants "comparable". 
                # We can't really make Wildcard "comparable" to Vector using just Python logic easily without a model.
                # But we can try our best.
                
                final_results = unique_candidates[:9] # Fallback
                st.session_state.last_timing = "No Rerank"

            total_duration = time.time() - t_start
            st.session_state.last_timing = f"Total: {total_duration*1000:.0f}ms"
            
            return final_results[:9]

    except Exception as e:
        st.error(f"Search failed: {e}")
        log_debug("Search Failed", {"error": str(e)}, None, 0)
        return []


def get_recommendations(product_id):
    db = get_spanner_database()
    start_time = time.time()
    
    sql = """
    GRAPH RetailGraph
    MATCH (p1:products)<-[:purchased]-(u:users)-[:purchased]->(p2:products)
    WHERE p1.id = @pid AND p2.id != @pid
    RETURN p2.id, p2.name, p2.retail_price, p2.product_image_uri, p2.product_description, count(*) as freq
    ORDER BY freq DESC
    LIMIT 4
    """
    
    params = {"pid": int(product_id)}
    param_types = {"pid": spanner.param_types.INT64}

    try:
        with db.snapshot() as snapshot:
            results = snapshot.execute_sql(
                sql,
                params=params,
                param_types=param_types
            )
            rows = list(results)
            
            # --- Graph Visualization Logic ---
            if rows:
                # Create DOT format string
                dot = 'digraph G {\n  rankdir=LR;\n  node [style=filled, fillcolor="#E8F0FE", shape=box, fontname="Arial"];\n  edge [color="#1A73E8", fontname="Arial"];\n'
                dot += f'  Current [label="Current Product\\n(ID: {product_id})", fillcolor="#FCE8E6", shape=ellipse];\n'
                
                for r in rows:
                    # r: p2.id, p2.name, price, img, desc, freq
                    rec_id = r[0]
                    rec_name = r[1].replace('"', '\\"')[:20] + "..." if len(r[1]) > 20 else r[1].replace('"', '\\"')
                    count = r[5]
                    width = max(1, count / 5) # Scale edge width
                    
                    dot += f'  "{rec_id}" [label="{rec_name}"];\n'
                    dot += f'  Current -> "{rec_id}" [label="{count} users", penwidth={width}];\n'
                
                dot += "}"
                st.session_state.debug_graph = dot
            else:
                st.session_state.debug_graph = None
            # ---------------------------------

            log_debug(sql, params, param_types, time.time() - start_time)
            return rows
    except Exception as e:
        log_debug(f"ERROR: {sql}", {"pid": product_id, "error": str(e)}, None, time.time() - start_time)
        return []

# --- UI Components ---



def render_debug_panel():
    if not st.session_state.get("show_debug", False): return
    if not st.session_state.debug_logs: return # Hide if empty

    st.divider()
    st.subheader("Debug Panel & Query Log")
    
    # Graph Visualization
    if "debug_graph" in st.session_state and st.session_state.debug_graph:
        st.markdown("#### 🕸️ Graph Traversal")
        st.graphviz_chart(st.session_state.debug_graph)
    
    for i, log in enumerate(st.session_state.debug_logs):
        with st.expander(f"{log['timestamp']} ({log['duration']}) - {log.get('query', '')[:50]}..."):
            st.code(log['query'], language="sql")
            st.json({"params": log['params']})
            
            if st.button("Explain (Profile)", key=f"explain_{i}"):
                with st.spinner("Running PROFILE..."):
                    stats = explain_query(log['query'], log['raw_params'], log['param_types'])
                    
                    # Display Profile Stats
                    if hasattr(stats, 'query_plan'):
                        st.write("### Query Plan")
                        st.write(stats) 
                    else:
                        st.json(stats)


def render_sidebar():
    with st.sidebar:
        st.title("Settings")
        st.session_state.show_debug = st.toggle("Show Debug Panel", value=st.session_state.show_debug)
        if st.button("Clear Debug Logs"):
            st.session_state.debug_logs = []
            st.rerun()

        st.session_state.search_mode = st.selectbox(
            "Search Mode",
            ["Hybrid (Vector + FTS)", "Vector Only", "Full Text Search Only", "Full Text Search + Enhanced Query", "SQL Wildcard (LIKE %...%)"],
            index=0
        )
        
        reranker_option = st.radio(
            "Reranker Model",
            ["Vertex AI Semantic Ranker", "None (Python RRF)"],
            index=0
        )
        st.session_state.reranker_model = reranker_option

        st.divider()
        if st.button("Quick Demo: Red Dress < $50"):
            st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm Aria. What can I help you find today?"}]
            st.session_state.messages.append({"role": "user", "content": "I would like a red dress for less than $50."})
            # Trigger search immediately? We need to handle this in render_home or rerun
            st.session_state.trigger_search = "I would like a red dress for less than $50."
            st.session_state.page = "home"
            st.rerun()
        
        if st.button("New Chat", type="primary"):
            st.session_state.messages = [{"role": "assistant", "content": "How can I help you regarding fashion today?"}]
            st.session_state.page = "home"
            st.rerun()

def render_home():
    st.markdown("<h1 style='text-align: center; color: #1a73e8;'>Gemini and Spanner Demo</h1>", unsafe_allow_html=True)
    
    # Chat History
    for msg_idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            # If assistant message has product results, show them FIRST
            if msg.get("results"):
                cols = st.columns(3) # 3 columns for cleaner grid
                for i, p in enumerate(msg["results"]):
                    # p: (id, name, desc, price, img, rrf_score)
                    with cols[i % 3]:
                        p_id = p[0]
                        img_url = transform_image_uri(p[4])
                        # Image with Link
                        st.markdown(f"""
                        <a href="?product_id={p_id}" target="_self" style="text-decoration:none; color:inherit;">
                            <div class="product-card">
                                <img src="{img_url}" style="width:100%; height:180px; object-fit:cover; border-radius:8px 8px 0 0;">
                                <div style="padding:10px;">
                                    <div class="product-title">{p[1]}</div>
                                    <div class="product-price">${p[3]:.2f}</div>
                                    <div style="font-size:0.85rem; color:#5f6368; margin-top:4px;">{p[2][:60]}...</div>
                                </div>
                            </div>
                        </a>
                        """, unsafe_allow_html=True)
            
            # Then show the text content
            st.markdown(msg["content"])

    # Input
    # Handle Input (Inline Form to allow Debug Panel below)
    with st.form("chat_input_form", clear_on_submit=True):
        cols = st.columns([0.85, 0.15])
        with cols[0]:
            user_input = st.text_input("Message", label_visibility="collapsed", placeholder="Search for products...")
        with cols[1]:
            submitted = st.form_submit_button("Send")

    trigger_input = st.session_state.pop("trigger_search", None)
    
    final_input = trigger_input if trigger_input else (user_input if submitted else None)
    
    if final_input:
        # If triggered via button, we already appended to messages? No, let's append here if not duplicates
        if not (st.session_state.messages and st.session_state.messages[-1]["content"] == final_input):
            st.session_state.messages.append({"role": "user", "content": final_input})
        
        with st.chat_message("user"):
            st.markdown(final_input)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # 1. Analyze Request (Intent + Filters combined)
                analysis = analyze_request(final_input, st.session_state.messages)
                intent = analysis.get("intent", "SEARCH")
                parsed_query = analysis.get("search_params")
                
                results = []
                response_text = ""
                
                if intent == "SEARCH" or trigger_input: # Force search for trigger
                    # Pass parsed_query to skip redundant Gemini call
                    results = search_products(final_input, parsed_query=parsed_query)
                    response_text = f"I found {len(results)} items."
                    if "last_timing" in st.session_state:
                        response_text += f" ({st.session_state.last_timing})"
                else:
                    # CHAT intent - maybe use previous results context?
                    pass
                
                # 2. Generate Conversational Response
                chat_response = generate_response(final_input, results, st.session_state.messages)
                
                if response_text:
                    full_response = f"{response_text}\n\n{chat_response}"
                else:
                    full_response = chat_response
                
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response, "results": results})
                st.rerun()

    # Debug Panel at the bottom
    if st.session_state.show_debug:
        render_debug_panel()

def render_detail():
    p = st.session_state.selected_product
    if not p:
        st.session_state.page = "home"
        st.rerun()
        return

    if st.button("← Back to Search"):
        st.session_state.page = "home"
        st.rerun()

    # Product Details
    img_url = transform_image_uri(p[4])
    
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.image(img_url, use_container_width=True)
    with c2:
        st.markdown(f"## {p[1]}")
        st.markdown(f"<div class='product-price' style='font-size: 1.5rem;'>${p[3]:.2f}</div>", unsafe_allow_html=True)
        st.write(p[2])
        st.button("Add to Cart (Demo)", type="primary")

    # Recommendations
    st.markdown("<div class='rec-section'>", unsafe_allow_html=True)
    st.subheader("Customers also bought (Graph Recommendations):")
    
    recs = get_recommendations(p[0])
    if recs:
        r_cols = st.columns(4)
        for i, r in enumerate(recs):
            # r: id, name, price, img, desc, freq
            with r_cols[i % 4]:
                r_img = transform_image_uri(r[3])
                st.image(r_img, use_container_width=True)
                st.markdown(f"**{r[1]}**")
                st.caption(f"${r[2]:.2f}")
                if st.button("View", key=f"rec_{r[0]}"):
                     st.session_state.selected_product = (r[0], r[1], r[4], r[2], r[3], 0) # conform to product tuple
                     st.rerun()
    else:
        st.info("No recommendations found for this item.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Debug Panel at the bottom of detail page too?
    if st.session_state.show_debug:
        render_debug_panel()

# --- Main App ---
render_sidebar()

if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "detail":
    render_detail()
