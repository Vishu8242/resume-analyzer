"""
History View Component
Displays historical resume evaluations from SQLite database.
Allows searching, viewing detailed breakdowns, deleting records,
and clearing history with clear privacy transparency.
"""

import streamlit as st
from modules.database import (
    get_all_analyses,
    delete_analysis,
    clear_all_analyses,
    get_database_statistics
)
from components.sidebar import PAGE_RESULTS, PAGE_ANALYZE


def render_history_view():
    """
    Renders the Analysis History page.
    """
    st.markdown("## 📜 Analysis History")
    st.caption("Review previous resume evaluations, track score progression over time, and manage stored records.")

    # Privacy notice callout
    st.markdown(
        """
        <div class="callout-box callout-info">
            <b>🔒 Data Privacy Guarantee:</b> Only high-level analysis metadata (scores, timestamp, job title, and skill names) 
            is stored locally in SQLite. Original resume documents and full resume text are never permanently saved.
        </div>
        """,
        unsafe_allow_html=True
    )

    stats = get_database_statistics()
    total_count = stats.get("total_analyses", 0)

    if total_count == 0:
        st.info("No analysis records found in the database. Perform your first evaluation to start tracking history!")
        if st.button("🚀 Analyze a Resume Now", type="primary"):
            st.session_state["target_page"] = PAGE_ANALYZE
            st.rerun()
        return

    # Top Bar: Stats & Controls
    c_stat1, c_stat2, c_stat3, c_action = st.columns([1, 1, 1, 1.5])
    with c_stat1:
        st.metric("Total Records", total_count)
    with c_stat2:
        st.metric("Average Score", f"{stats.get('average_score', 0):.1f}%")
    with c_stat3:
        st.metric("Highest Score", f"{stats.get('highest_score', 0):.1f}%")
    with c_action:
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear All History", type="secondary"):
            st.session_state["confirm_clear_all"] = True

    if st.session_state.get("confirm_clear_all", False):
        st.warning("⚠️ Are you sure you want to delete all historical analysis records? This cannot be undone.")
        col_yes, col_no = st.columns([1, 1])
        with col_yes:
            if st.button("Yes, Clear Everything", type="primary"):
                clear_all_analyses()
                st.session_state["confirm_clear_all"] = False
                st.success("All history records cleared.")
                st.rerun()
        with col_no:
            if st.button("Cancel"):
                st.session_state["confirm_clear_all"] = False
                st.rerun()

    # Search filter
    search_query = st.text_input("🔍 Search records by target job title:", placeholder="e.g. Python, Full Stack, Engineer...")

    records = get_all_analyses(limit=100)
    if search_query:
        records = [r for r in records if search_query.lower() in r.get("job_title", "").lower()]

    st.markdown(f"### Showing {len(records)} Evaluation{'s' if len(records) != 1 else ''}")

    for item in records:
        with st.expander(f"📌 #{item['id']} • {item['job_title']} — {item['overall_score']:.1f}% Match ({item['created_at']})", expanded=False):
            sc1, sc2 = st.columns([2, 1])
            with sc1:
                st.markdown(f"**Target Role:** `{item['job_title']}`")
                st.markdown(f"**Recorded On:** {item['created_at']}")
                st.markdown(f"**Executive Verdict:** {item['summary']}")

                # Component scores
                comp = item.get("component_scores", {})
                if comp:
                    st.markdown("**Pillar Scores:**")
                    pill_text = " • ".join([f"**{k.title()}**: {v:.0f}%" for k, v in comp.items() if v is not None])
                    st.caption(pill_text)

                # Skills breakdown
                matching = item.get("matching_skills", [])
                missing = item.get("missing_skills", [])
                if matching:
                    st.markdown(f"**Matching Skills ({len(matching)}):** " + ", ".join(matching[:15]))
                if missing:
                    st.markdown(f"**Missing Skills ({len(missing)}):** " + ", ".join(missing[:15]))

            with sc2:
                # Score Badge
                score = item['overall_score']
                color = "#10B981" if score >= 85 else ("#3B82F6" if score >= 70 else ("#F59E0B" if score >= 50 else "#EF4444"))
                st.markdown(
                    f"""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem; text-align: center; margin-bottom: 0.75rem;">
                        <div style="font-size: 2.2rem; font-weight: 800; color: {color};">{score:.1f}%</div>
                        <div style="font-size: 0.8rem; color: #64748B;">Overall ATS Compatibility</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button("📊 View Full Results Report", key=f"view_rec_{item['id']}", type="primary", use_container_width=True):
                    st.session_state["active_analysis"] = item
                    st.session_state["target_page"] = PAGE_RESULTS
                    st.rerun()

                if st.button("🗑️ Delete Record", key=f"del_rec_{item['id']}", use_container_width=True):
                    delete_analysis(item["id"])
                    st.success(f"Record #{item['id']} deleted.")
                    st.rerun()
