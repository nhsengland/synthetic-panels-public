import streamlit as st
from pathlib import Path


def apply_nhs_style():
    css_path = Path(__file__).parent / "nhs.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def require_configuration():
    """Stop the page with a friendly message if Configuration hasn't been visited."""
    if "params" not in st.session_state:
        st.warning("⚙️ Please open the **Configuration** page first to load settings, then return here.")
        st.stop()
