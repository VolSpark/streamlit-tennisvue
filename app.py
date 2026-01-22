"""
Minimal, production-ready Streamlit app.
Entrypoint: app.py (repo root)
"""

import streamlit as st
from src.config import PAGE_CONFIG
from src.pages import home, tennis

# Configure page
st.set_page_config(**PAGE_CONFIG)

# Load custom CSS
with open("src/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page:", ["Home", "Tennis Probability Engine"])

# Route pages
if page == "Home":
    home.render()
elif page == "Tennis Probability Engine":
    tennis.render()


