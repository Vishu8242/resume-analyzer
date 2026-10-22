"""
Dashboard Component
Home page featuring real metrics, quick-start workflow actions,
system instructions, and recent analysis history table.
"""

import streamlit as st
from modules.database import get_database_statistics, get_all_analyses
from components.sidebar import PAGE_ANALYZE, PAGE_RESULTS, PAGE_HISTORY


def render_dashboard():
    """
    Renders the Home / Dashboard page.
    """
    # 1. Hero Banner
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title">AI Resume Analyzer & ATS Score Checker</div>
            <div class="hero-subtitle">
                Evaluate your resume against target job descriptions with transparent scoring,
                deep skill gap identification, and actionable NLP-driven recommendations.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Action Buttons Row
    c1, c2, _ = st.columns([1.5, 1.5, 4])
    with c1:
        if st.button("🚀 Upload & Analyze Resume", type="primary", use_container_width=True):
            st.session_state["target_page"] = PAGE_ANALYZE
            st.rerun()
    with c2:
        if st.button("📜 View Analysis History", use_container_width=True):
            st.session_state["target_page"] = PAGE_HISTORY
            st.rerun()

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 2. Real Metrics Cards (From SQLite Database)
    stats = get_database_statistics()
    total_count = stats.get("total_analyses", 0)
    avg_score = stats.get("average_score", 0.0)
    max_score = stats.get("highest_score", 0.0)
    latest = stats.get("latest_analysis")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Analyses</div>
                <div class="metric-value">{total_count}</div>
                <div class="metric-sub">Across all sessions</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m2:
        val_str = f"{avg_score:.1f}%" if total_count > 0 else "—"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Average Score</div>
                <div class="metric-value">{val_str}</div>
                <div class="metric-sub">Mean compatibility</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m3:
        top_str = f"{max_score:.1f}%" if total_count > 0 else "—"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Highest Score</div>
                <div class="metric-value">{top_str}</div>
                <div class="metric-sub">Peak match achieved</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m4:
        if latest:
            latest_val = f"{latest['overall_score']:.1f}%"
            latest_sub = f"{latest['job_title'][:20]}..." if len(latest.get('job_title', '')) > 20 else latest.get('job_title', '')
        else:
            latest_val = "—"
            latest_sub = "No analyses recorded"

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Latest Score</div>
                <div class="metric-value">{latest_val}</div>
                <div class="metric-sub">{latest_sub}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # 3. How It Works / Quick Instructions
    st.markdown("### 📋 How It Works")
    step1, step2, step3, step4 = st.columns(4)
    with step1:
        st.markdown(
            """
            <div class="content-card" style="height: 100%;">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📄</div>
                <div style="font-weight: 700; font-size: 1rem; color: #0F172A; margin-bottom: 0.25rem;">1. Upload Resume</div>
                <div style="font-size: 0.85rem; color: #64748B;">Upload your PDF or DOCX resume. Digital text and tables are securely parsed in-memory.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with step2:
        st.markdown(
            """
            <div class="content-card" style="height: 100%;">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🎯</div>
                <div style="font-weight: 700; font-size: 1rem; color: #0F172A; margin-bottom: 0.25rem;">2. Add Job Target</div>
                <div style="font-size: 0.85rem; color: #64748B;">Paste job description text or upload a TXT file to isolate required vs preferred skills.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with step3:
        st.markdown(
            """
            <div class="content-card" style="height: 100%;">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚙️</div>
                <div style="font-weight: 700; font-size: 1rem; color: #0F172A; margin-bottom: 0.25rem;">3. ATS Evaluation</div>
                <div style="font-size: 0.85rem; color: #64748B;">Weighted engine evaluates skills, tenure, degrees, keyword density, and formatting.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with step4:
        st.markdown(
            """
            <div class="content-card" style="height: 100%;">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📥</div>
                <div style="font-weight: 700; font-size: 1rem; color: #0F172A; margin-bottom: 0.25rem;">4. Insights & PDF</div>
                <div style="font-size: 0.85rem; color: #64748B;">Inspect missing skill gaps, receive AI bullet point advice, and download your PDF report.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 4. Recent Analysis Activity
    st.markdown("### 🕒 Recent Activity")
    recent = get_all_analyses(limit=5)
    if not recent:
        st.info("No resume analyses performed yet. Click **'Upload & Analyze Resume'** above to start your first evaluation.")
    else:
        for item in recent:
            with st.container():
                rc1, rc2, rc3, rc4 = st.columns([3, 2, 2, 2])
                with rc1:
                    st.markdown(f"**{item['job_title']}**")
                    st.caption(f"Date: {item['created_at']}")
                with rc2:
                    score = item['overall_score']
                    color = "#10B981" if score >= 85 else ("#3B82F6" if score >= 70 else ("#F59E0B" if score >= 50 else "#EF4444"))
                    st.markdown(f"<span style='font-size: 1.1rem; font-weight: 800; color: {color};'>{score:.1f}%</span> Match", unsafe_allow_html=True)
                with rc3:
                    matches = len(item.get("matching_skills", []))
                    missing = len(item.get("missing_skills", []))
                    st.caption(f"✓ {matches} Matched &nbsp;•&nbsp; ✕ {missing} Missing")
                with rc4:
                    if st.button("View Details", key=f"dash_view_{item['id']}"):
                        st.session_state["active_analysis"] = item
                        st.session_state["target_page"] = PAGE_RESULTS
                        st.rerun()
                st.divider()
