import streamlit as st

st.set_page_config(page_title="Hello, Streamlit", layout="centered")

st.title("Hello, Streamlit 👋")
st.write("If you can see this, your GitHub → Streamlit deploy pipeline works.")

name = st.text_input("Your name")
if name:
    st.success(f"Nice to meet you, {name}!")
