"""
Sidebar Navigation & Configuration Component
Provides navigation across the 6 core pages, API key configuration,
history recording toggles, and scoring weight controls.
"""

import streamlit as st
from typing import Tuple, Dict, Any
from config.settings import APP_NAME, APP_VERSION, DEFAULT_WEIGHTS, GEMINI_API_KEY


PAGE_HOME = "🏠 Home / Dashboard"
PAGE_ANALYZE = "🔍 Analyze Resume"
PAGE_RESULTS = "📊 Analysis Results"
PAGE_IMPROVE = "💡 Resume Improvement Guide"
PAGE_HISTORY = "📜 Analysis History"
PAGE_ABOUT = "ℹ️ About Project"

NAV_OPTIONS = [
    PAGE_HOME,
    PAGE_ANALYZE,
    PAGE_RESULTS,
    PAGE_IMPROVE,
    PAGE_HISTORY,
    PAGE_ABOUT
]


def render_sidebar() -> Tuple[str, Dict[str, Any]]:
    """
    Renders the sidebar navigation and app controls.
    Returns:
        (selected_page, settings_dict)
    """
    with st.sidebar:
        # App Branding Header
        st.markdown(
            f"""
            <div style="padding: 0.5rem 0 1rem 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="background: linear-gradient(135deg, #3B82F6, #6366F1); color: white; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: bold;">
                        ✓
                    </div>
                    <div>
                        <div style="font-weight: 800; font-size: 1.05rem; color: #0F172A; line-height: 1.2;">ResumeATS</div>
                        <div style="font-size: 0.75rem; color: #64748B;">v{APP_VERSION} • AI & NLP Powered</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Navigation
        st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;'>Navigation</p>", unsafe_allow_html=True)
        
        # Check if a page change was requested in session state
        if "target_page" in st.session_state and st.session_state["target_page"] in NAV_OPTIONS:
            st.session_state["nav_radio"] = st.session_state["target_page"]
            del st.session_state["target_page"]

        if "nav_radio" not in st.session_state or st.session_state["nav_radio"] not in NAV_OPTIONS:
            st.session_state["nav_radio"] = PAGE_HOME

        selected_page = st.radio(
            "Go to page",
            NAV_OPTIONS,
            key="nav_radio",
            label_visibility="collapsed"
        )

        st.markdown("<div style='margin-top: 1.5rem; border-top: 1px solid #E2E8F0; padding-top: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;'>Settings & Preferences</p>", unsafe_allow_html=True)

        # Privacy / History Toggle
        enable_history = st.checkbox(
            "Save analysis history",
            value=st.session_state.get("enable_history", True),
            help="Stores high-level scores and skills in local SQLite database. Original resumes are never saved."
        )
        st.session_state["enable_history"] = enable_history

        # Configurable Weights Expander
        with st.expander("⚙️ Scoring Weights", expanded=False):
            st.caption("Adjust weight distribution (must sum to 100%).")
            w_skills = st.slider("Skills Matching", 0, 100, int(DEFAULT_WEIGHTS["skills"] * 100), step=5)
            w_exp = st.slider("Work Experience", 0, 100, int(DEFAULT_WEIGHTS["experience"] * 100), step=5)
            w_edu = st.slider("Education", 0, 100, int(DEFAULT_WEIGHTS["education"] * 100), step=5)
            w_kw = st.slider("Keywords", 0, 100, int(DEFAULT_WEIGHTS["keywords"] * 100), step=5)
            w_fmt = st.slider("Formatting", 0, 100, int(DEFAULT_WEIGHTS["formatting"] * 100), step=5)

            total_w = w_skills + w_exp + w_edu + w_kw + w_fmt
            if total_w != 100:
                st.warning(f"Total is {total_w}%. Normalized automatically during scoring.")

            custom_weights = {
                "skills": w_skills / 100.0,
                "experience": w_exp / 100.0,
                "education": w_edu / 100.0,
                "keywords": w_kw / 100.0,
                "formatting": w_fmt / 100.0
            }

        # Optional AI Key configuration
        with st.expander("🤖 Optional AI API Key", expanded=False):
            st.caption("Works offline by default. Optionally enter a Gemini API key for dynamic suggestions.")
            user_gemini_key = st.text_input(
                "Gemini API Key",
                type="password",
                value=st.session_state.get("gemini_key", GEMINI_API_KEY),
                placeholder="AIzaSy..."
            )
            st.session_state["gemini_key"] = user_gemini_key

        # Privacy Badge
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.75rem; margin-top: 1rem;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #0F172A; display: flex; align-items: center; gap: 4px;">
                    🔒 Privacy Assured
                </div>
                <div style="font-size: 0.7rem; color: #64748B; margin-top: 2px;">
                    Uploaded documents are parsed in-memory and not retained permanently.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        settings = {
            "enable_history": enable_history,
            "weights": custom_weights,
            "gemini_key": st.session_state.get("gemini_key", "")
        }

        return selected_page, settings
