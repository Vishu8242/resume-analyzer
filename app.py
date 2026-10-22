"""
Main Application Entry Point
AI Resume Analyzer and ATS Score Checker
"""

import os
import streamlit as st
from pathlib import Path

# Set Streamlit Page Configuration as first Streamlit call
st.set_page_config(
    page_title="AI Resume Analyzer & ATS Score Checker",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

from config.settings import APP_NAME, APP_VERSION, STYLES_DIR
from modules.database import init_db
from components.sidebar import (
    render_sidebar,
    PAGE_HOME,
    PAGE_ANALYZE,
    PAGE_RESULTS,
    PAGE_IMPROVE,
    PAGE_HISTORY,
    PAGE_ABOUT
)
from components.dashboard import render_dashboard
from components.upload_form import render_upload_form
from components.results_view import render_results_view
from components.improvement_guide import render_improvement_guide
from components.history_view import render_history_view
from components.about_view import render_about_view


def load_custom_css():
    """
    Loads custom CSS styles from styles/main.css.
    """
    css_file = STYLES_DIR / "main.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def main():
    # 1. Initialize local SQLite database
    init_db()

    # 2. Inject custom CSS styling
    load_custom_css()

    # 3. Render sidebar navigation and capture user settings
    selected_page, settings = render_sidebar()

    # 4. Route to selected view
    if selected_page == PAGE_HOME:
        render_dashboard()
    elif selected_page == PAGE_ANALYZE:
        render_upload_form(settings)
    elif selected_page == PAGE_RESULTS:
        render_results_view()
    elif selected_page == PAGE_IMPROVE:
        render_improvement_guide(settings)
    elif selected_page == PAGE_HISTORY:
        render_history_view()
    elif selected_page == PAGE_ABOUT:
        render_about_view()

    # 5. Footer
    st.markdown("<div style='margin-top: 3rem; border-top: 1px solid #E2E8F0; padding-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="text-align: center; font-size: 0.8rem; color: #94A3B8; padding-bottom: 2rem;">
            {APP_NAME} v{APP_VERSION} • Built with Streamlit, NLP & ReportLab • 
            <a href="javascript:void(0);" style="color: #64748B; text-decoration: none;">Privacy Assured</a>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
