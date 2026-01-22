git add -A && git commit -m "feat: add dark mode by default with theme toggle" && git push"""
Tennis Win Probability Engine - Streamlit App
Entrypoint: streamlit_app.py (deployed via Streamlit Cloud)
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

# Add theme toggle
st.sidebar.divider()
st.sidebar.title("⚙️ Settings")

# Initialize theme state
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'dark'

# Theme toggle button
theme_options = ["🌙 Dark Mode", "☀️ Light Mode"]
current_theme = theme_options[0] if st.session_state.theme_mode == 'dark' else theme_options[1]

if st.sidebar.button(f"Theme: {current_theme}"):
    st.session_state.theme_mode = 'light' if st.session_state.theme_mode == 'dark' else 'dark'
    st.rerun()

# Route pages
if page == "Home":
    home.render()
elif page == "Tennis Probability Engine":
    tennis.render()
