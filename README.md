# Gemini & Spanner Retail Demo

A multimodal retail search and recommendation application powered by **Google Cloud Spanner**, **Vertex AI (Gemini)**, and **Streamlit**.

## Features

-   **Multimodal Search**: Search by text, vector (semantic), or hybrid (text + vector).
-   **Native Spanner Enhancements**: Uses Spanner's built-in `SEARCH(..., enhance_query=>true)` for automatic query expansion (synonyms, spell correction).
-   **Generative AI Integration**:
    -   **Gemini 1.5 Flash**: Analyzing user queries and generating personalized responses.
    -   **Vector Search**: Using Vertex AI web-gecko text embeddings for semantic retrieval.
-   **Graph-Based Recommendations**: leveraging Spanner Graph (SQL/PGQ) to recommend related products based on purchase history (e.g., "People who bought THIS also bought...").
-   **Resilient Architecture**:
    -   Systemd service for automatic restarts.
    -   Robust error handling and "Nuclear Patch" for known client-side metric issues.

## Tech Stack

-   **Frontend**: Streamlit
-   **Database**: Google Cloud Spanner (Graph + Vector + Search)
-   **AI/ML**: Vertex AI (Gemini 1.5 Flash, Text Embeddings)
-   **Infrastructure**: Google Compute Engine (Debian 11)

## Setup & Deployment

See `DEPLOY_INSTRUCTIONS.md` for detailed deployment steps.

## Usage

1.  **Search**: Use the sidebar to switch between "Hybrid", "Vector Only", "Full Text Search", etc.
2.  **Debug**: Enable the "Debug Panel" to view raw SQL queries, execution times, and graph traversals.
3.  **Recommendations**: Click on any product to see "People who bought this also bought..." recommendations driven by Spanner Graph.
