"""Configuration module for the Streamlit app."""

PAGE_CONFIG = {
    "page_title": "My Streamlit App",
    "page_icon": "🚀",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Example: API keys, database URLs, etc.
# Load from st.secrets in main app.py if needed
EXAMPLE_CONFIG = {
    "api_key": "load_from_secrets",
    "database_url": "load_from_secrets",
}
