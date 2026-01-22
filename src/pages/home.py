"""Home page module."""

import streamlit as st
from src.utils import validate_input, format_number


def render():
    """Render the home page."""
    st.title("🚀 WELCOME TO MY STREAMLIT APP")

    st.markdown(
        """
        This is a minimal, production-ready Streamlit app template.
        
        **Features:**
        - Clean file structure (src/ folder for logic)
        - Secrets management ready
        - Testing setup included
        - Deployment-ready
        """
    )

    st.divider()

    # Example form with inputs
    st.subheader("INTERACTIVE EXAMPLE")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Your name:", placeholder="Enter your name")

    with col2:
        age = st.number_input("Your age:", min_value=0, max_value=120, value=25)

    # Example output
    if validate_input(name):
        st.success(f"✅ Hello, {name}! You are {age} years old.")
        st.info(f"Formatted age: {format_number(float(age))}")
    else:
        st.warning("👉 Please enter your name above.")

    st.divider()

    # Example: Using secrets
    st.subheader("SECRETS EXAMPLE")
    st.markdown(
        """
        To use secrets in production:
        
        1. In Streamlit Community Cloud, go to **App settings → Secrets**
        2. Add your secrets (e.g., `api_key = "your-key-here"`)
        3. Access in your app with `st.secrets["api_key"]`
        
        **Never commit real secrets to GitHub!**
        """
    )

    # Example of reading a secret (safely)
    try:
        example_secret = st.secrets.get("example_key", "No secret set")
        st.code(f'st.secrets.get("example_key") → {example_secret}', language="python")
    except Exception:
        st.info("💡 Secrets not configured. This is normal in local development.")
