import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Synthetic Panels — NHSE",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- Load NHS styling ---
css_path = Path(__file__).parent / "style" / "nhs.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# --- NHS Header ---
st.markdown("""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
    <div style="background-color: #005EB8; padding: 8px 16px; border-radius: 4px;">
        <span style="color: white; font-weight: 700; font-size: 1.4rem; letter-spacing: -0.02em;">NHS</span>
    </div>
    <div>
        <h1 style="margin: 0; padding: 0; font-size: 1.8rem;">Synthetic Panels</h1>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("Synthetic Panels tool for Behavioural Science Research. Configure parameters, run the pipeline, and explore results.")

st.markdown("""
### Pages

1. **Setup** — Define your research context, message variants, and sample demographics
2. **Run** — Execute the pipeline with current settings
3. **Results** — Explore outputs with interactive charts and tables
""")

if "results" in st.session_state and st.session_state.results is not None:
    st.success(f"Last run completed. Results in: {st.session_state.results['run_dir']}")
