"""
Results View Component
Displays the ATS evaluation results, component breakdowns,
interactive Plotly visualizations, skills matrix, and PDF download.
"""

import streamlit as st
from components.charts import (
    create_gauge_chart,
    create_radar_chart,
    create_horizontal_bar_chart,
    create_skills_donut_chart
)
from modules.report_generator import build_pdf_report
from components.sidebar import PAGE_ANALYZE, PAGE_IMPROVE


from config.settings import ATS_DISCLAIMER


def render_results_view():
    """
    Renders the comprehensive ATS Analysis Results page.
    """
    analysis = st.session_state.get("active_analysis")

    if not analysis:
        st.info("ℹ️ No active analysis found. Upload a resume and job description to generate your report.")
        if st.button("👉 Go to Resume Analyzer", type="primary"):
            st.session_state["target_page"] = PAGE_ANALYZE
            st.rerun()
        return

    # Header & metadata with full fallbacks
    overall_score = float(analysis.get("overall_score", 0.0))
    job_title = analysis.get("job_title", "Software Engineer")
    candidate_name = analysis.get("candidate_name", "Candidate")
    grade = analysis.get("grade") or (
        "Excellent Compatibility" if overall_score >= 85 else (
            "Strong Compatibility" if overall_score >= 70 else (
                "Moderate Compatibility" if overall_score >= 50 else "Low Compatibility"
            )
        )
    )
    color = analysis.get("color") or (
        "#10B981" if overall_score >= 85 else (
            "#3B82F6" if overall_score >= 70 else (
                "#F59E0B" if overall_score >= 50 else "#EF4444"
            )
        )
    )
    verdict = analysis.get("verdict") or analysis.get("summary") or "Evaluation completed using weighted multi-factor ATS engine."
    disclaimer = analysis.get("disclaimer") or ATS_DISCLAIMER

    is_general_audit = (job_title in ("General Candidate Profile", "General Professional Profile", "Not specified"))
    if is_general_audit:
        st.markdown(f"## 📊 Resume ATS & Health Results: {candidate_name}")
        st.caption(f"Profile: **General Professional Audit** • Calculated across formatting, skills, experience, and education (No target JD specified)")
    else:
        st.markdown(f"## 📊 ATS Compatibility Results: {job_title}")
        st.caption(f"Candidate: **{candidate_name}** • Calculated using weighted multi-factor analysis")

    # Disclaimer Alert
    st.markdown(
        f"""
        <div class="callout-box callout-info">
            <b>Disclaimer:</b> {disclaimer}
        </div>
        """,
        unsafe_allow_html=True
    )

    comp_scores = analysis.get("component_scores", {})
    weights = analysis.get("effective_weights", {})

    # ==========================================
    # 1. Dual Score Separation Display Cards
    # ==========================================
    job_match_score = analysis.get("job_match_score")
    resume_quality_score = analysis.get("resume_quality_score")
    if resume_quality_score is None:
        resume_quality_score = float(comp_scores.get("formatting") or 0.0)

    jm_col, rq_col = st.columns(2, gap="medium")
    with jm_col:
        if job_match_score is not None:
            jm_grade = analysis.get("job_match_grade") or ("Strong Match" if job_match_score >= 70 else "Moderate Match")
            jm_color = analysis.get("job_match_color") or ("#10B981" if job_match_score >= 85 else ("#3B82F6" if job_match_score >= 70 else "#F59E0B"))
            st.markdown(
                f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-left: 5px solid {jm_color}; border-radius: 8px; padding: 1.1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 1rem;">
                    <div style="font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B;">🎯 Job-Specific ATS Match Score</div>
                    <div style="display: flex; align-items: baseline; gap: 0.75rem; margin-top: 0.35rem;">
                        <span style="font-size: 2.2rem; font-weight: 800; color: {jm_color};">{job_match_score:.1f}%</span>
                        <span style="font-size: 0.95rem; font-weight: 600; color: #334155;">{jm_grade}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.35rem; line-height: 1.4;">
                        Evaluates role alignment against required & preferred skills, years of experience, education tier, and job keywords.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-left: 5px solid #94A3B8; border-radius: 8px; padding: 1.1rem; margin-bottom: 1rem;">
                    <div style="font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B;">🎯 Job-Specific ATS Match Score</div>
                    <div style="display: flex; align-items: baseline; gap: 0.75rem; margin-top: 0.35rem;">
                        <span style="font-size: 1.8rem; font-weight: 700; color: #64748B;">N/A</span>
                        <span style="font-size: 0.85rem; font-weight: 600; background: #E2E8F0; color: #475569; padding: 2px 8px; border-radius: 4px;">General Audit Mode</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.35rem; line-height: 1.4;">
                        Target job description was omitted. Submit a job description to calculate role-specific requirement alignment.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with rq_col:
        rq_grade = analysis.get("resume_quality_grade") or ("High Quality" if resume_quality_score >= 85 else ("Good Quality" if resume_quality_score >= 70 else "Moderate Quality"))
        rq_color = analysis.get("resume_quality_color") or ("#10B981" if resume_quality_score >= 85 else ("#3B82F6" if resume_quality_score >= 70 else "#F59E0B"))
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-left: 5px solid {rq_color}; border-radius: 8px; padding: 1.1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 1rem;">
                <div style="font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B;">📄 General Resume Quality Score</div>
                <div style="display: flex; align-items: baseline; gap: 0.75rem; margin-top: 0.35rem;">
                    <span style="font-size: 2.2rem; font-weight: 800; color: {rq_color};">{resume_quality_score:.1f}%</span>
                    <span style="font-size: 0.95rem; font-weight: 600; color: #334155;">{rq_grade}</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.35rem; line-height: 1.4;">
                    Evaluates intrinsic resume document health: ATS parsing safety, structure, contact completeness, action verbs, and readability.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ==========================================
    # 2. Executive Score & Chart Row
    # ==========================================
    top_c1, top_c2 = st.columns([1.2, 1.8], gap="medium")

    with top_c1:
        gauge_fig = create_gauge_chart(overall_score, grade)
        if gauge_fig:
            st.plotly_chart(gauge_fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown(
                f"""
                <div class="score-display-container">
                    <div style="font-size: 3.5rem; font-weight: 800; color: {analysis.get('color', '#3B82F6')};">{overall_score}%</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #0F172A;">{grade}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown(f"**Verdict:** {verdict}")

        # Download PDF Action Button
        try:
            pdf_bytes = build_pdf_report(
                analysis,
                candidate_name=candidate_name,
                job_title=job_title
            )
            st.download_button(
                label="📥 Download Full PDF Analysis Report",
                data=pdf_bytes,
                file_name=f"ATS_Report_{candidate_name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.warning(f"PDF generation unavailable: {str(e)}")

    with top_c2:
        st.markdown("#### ⚖️ Five-Pillar ATS Balance")
        radar_fig = create_radar_chart(comp_scores)
        if radar_fig:
            st.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar": False})
        else:
            bar_fig = create_horizontal_bar_chart(comp_scores)
            if bar_fig:
                st.plotly_chart(bar_fig, use_container_width=True, config={"displayModeBar": False})

    # ==========================================
    # 3. Transparent Breakdown Expander
    # ==========================================
    with st.expander("📐 Transparent Score Calculation & Mathematical Breakdown", expanded=False):
        st.markdown("#### 🧮 Multi-Pillar Deterministic Formulation")
        st.caption("All scores are computed deterministically. The same resume and job description will always produce the identical score.")

        breakdown = analysis.get("score_breakdown", {})
        overall_b = breakdown.get("overall", {})
        formula_str = overall_b.get("formula") or "Final Score = (Skills × 40%) + (Experience × 20%) + (Education × 15%) + (Keywords × 15%) + (Formatting × 10%)"
        st.code(formula_str, language="text")

        # Table of contributions
        table_rows = []
        table_rows.append("| ATS Pillar | Raw Score (0–100) | Effective Weight | Weighted Points | Match Rationale |")
        table_rows.append("| :--- | :---: | :---: | :---: | :--- |")

        pillars_info = [
            ("Skills Match", comp_scores.get("skills"), weights.get("skills", 0.40), "Technical & domain skill taxonomy overlap"),
            ("Experience Match", comp_scores.get("experience"), weights.get("experience", 0.20), "Chronological tenure vs minimum required years"),
            ("Education Match", comp_scores.get("education"), weights.get("education", 0.15), "Highest verified degree vs job education tier"),
            ("Keyword Coverage", comp_scores.get("keywords"), weights.get("keywords", 0.15), "Unique target keyword coverage + TF-IDF semantic alignment"),
            ("Resume Formatting", comp_scores.get("formatting"), weights.get("formatting", 0.10), "ATS document parsability, contact completeness, and readability")
        ]

        for name, p_score, p_wt, desc in pillars_info:
            if p_score is not None:
                pts = p_score * p_wt
                table_rows.append(f"| **{name}** | {p_score:.1f}% | {p_wt * 100:.1f}% | **{pts:.2f} pts** | {desc} |")
            else:
                table_rows.append(f"| **{name}** | *N/A (Excluded)* | 0.0% | 0.00 pts | Missing data re-normalized to remaining pillars |")

        table_rows.append(f"| **Total Composite Score** | — | **100.0%** | **{overall_score:.1f} pts** | **Grade: {grade}** |")
        st.markdown("\n".join(table_rows))

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            > **ℹ️ Why Dual Scoring Matters:**
            > - **General Resume Quality Score** tests if your resume is formatted correctly for ATS parsers (standard fonts, clear section headings, email/phone detected, impactful action verbs).
            > - **Job-Specific ATS Match Score** determines how closely your specific qualifications match a particular job description (skills, years of experience, required degree level).
            """
        )

    # ==========================================
    # 4. Component Scores Cards
    # ==========================================
    st.markdown("### 🔍 Pillar Scores Breakdown")

    b1, b2, b3, b4, b5 = st.columns(5)
    with b1:
        s_score = comp_scores.get("skills")
        s_str = f"{s_score:.1f}%" if s_score is not None else "N/A"
        s_weight = weights.get("skills", 0.40) * 100
        st.metric("Skills", s_str, f"{s_weight:.0f}% Weight")
    with b2:
        e_score = comp_scores.get("experience")
        e_str = f"{e_score:.1f}%" if e_score is not None else "N/A"
        e_weight = weights.get("experience", 0.20) * 100
        st.metric("Experience", e_str, f"{e_weight:.0f}% Weight")
    with b3:
        ed_score = comp_scores.get("education")
        ed_str = f"{ed_score:.1f}%" if ed_score is not None else "N/A"
        ed_weight = weights.get("education", 0.15) * 100
        st.metric("Education", ed_str, f"{ed_weight:.0f}% Weight")
    with b4:
        k_score = comp_scores.get("keywords")
        k_str = f"{k_score:.1f}%" if k_score is not None else "N/A"
        k_weight = weights.get("keywords", 0.15) * 100
        st.metric("Keywords", k_str, f"{k_weight:.0f}% Weight")
    with b5:
        f_score = comp_scores.get("formatting")
        f_str = f"{f_score:.1f}%" if f_score is not None else "N/A"
        f_weight = weights.get("formatting", 0.10) * 100
        st.metric("Formatting", f_str, f"{f_weight:.0f}% Weight")

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 3. Skills Comparison Matrix
    # ==========================================
    st.markdown("### 🎯 Skills Alignment Matrix")
    skills_data = analysis.get("skills_analysis") or {}
    matching = skills_data.get("matching_skills") or analysis.get("matching_skills", [])
    missing_req = skills_data.get("missing_required") or analysis.get("missing_skills", [])
    missing_pref = skills_data.get("missing_preferred", [])
    extra_skills = skills_data.get("additional_skills", [])

    stats = skills_data.get("stats") or {
        "total_job_skills": len(matching) + len(missing_req) + len(missing_pref),
        "total_matching": len(matching),
        "total_missing_required": len(missing_req),
        "total_missing_preferred": len(missing_pref),
        "total_candidate_skills": len(matching)
    }

    match_pct = skills_data.get("match_percentage")
    if match_pct is None:
        total_target = stats.get("total_job_skills", 0)
        match_pct = round((len(matching) / total_target * 100), 1) if total_target > 0 else 0.0

    sk_tab1, sk_tab2, sk_tab3 = st.tabs(["🏷️ Categorized Skills", "📊 Skills Breakdown Chart", "📋 Extracted Information"])

    with sk_tab1:
        c_req, c_pref = st.columns(2)
        with c_req:
            skill_header = "✅ Identified Skills" if is_general_audit else "✅ Matching Skills"
            st.markdown(f"#### {skill_header} ({len(matching)})")
            if matching:
                m_html = " ".join([f"<span class='badge badge-success'>✓ {s}</span>" for s in matching])
                st.markdown(m_html, unsafe_allow_html=True)
            else:
                st.caption("No technical skills detected.")

            if is_general_audit:
                st.markdown("#### 🎯 Role-Specific Skill Gaps")
                st.info("ℹ️ Target job description was omitted for this run. To identify specific missing skill gaps, provide a target job posting in the analyzer.")
            else:
                st.markdown(f"#### ❌ Missing Required Skills ({len(missing_req)})")
                if missing_req:
                    mr_html = " ".join([f"<span class='badge badge-danger'>✕ {s}</span>" for s in missing_req])
                    st.markdown(mr_html, unsafe_allow_html=True)
                    st.caption("Adding evidence for these skills will directly improve your ATS score.")
                else:
                    st.success("✓ Excellent! All explicitly required skills were identified in your resume.")

        with c_pref:
            if is_general_audit:
                st.markdown("#### 💡 Next Steps for Tailoring")
                st.markdown(
                    """
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.5;">
                        • Paste a job posting in the <b>Analyze Resume</b> page to check role-specific keywords.<br/>
                        • Use the <b>Resume Improvement Guide</b> to rephrase bullet points with quantifiable impact.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f"#### ⚠️ Missing Preferred / Bonus Skills ({len(missing_pref)})")
                if missing_pref:
                    mp_html = " ".join([f"<span class='badge badge-warning'>! {s}</span>" for s in missing_pref])
                    st.markdown(mp_html, unsafe_allow_html=True)
                else:
                    st.caption("No preferred skills were missing or specified.")

                st.markdown(f"#### 💡 Additional Resume Skills ({len(extra_skills)})")
                if extra_skills:
                    ex_html = " ".join([f"<span class='badge badge-neutral'>{s}</span>" for s in extra_skills[:20]])
                    st.markdown(ex_html, unsafe_allow_html=True)
                else:
                    st.caption("No extra skills beyond the job description.")

    with sk_tab2:
        sc1, sc2 = st.columns([1, 1])
        with sc1:
            donut_fig = create_skills_donut_chart(stats)
            if donut_fig:
                st.plotly_chart(donut_fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.caption("Not enough skill points to render distribution chart.")
        with sc2:
            st.markdown("#### Skills Coverage Metrics")
            st.write(f"- **Target Job Skills Identified:** {stats.get('total_job_skills', 0)}")
            st.write(f"- **Total Matching Skills:** {stats.get('total_matching', 0)}")
            st.write(f"- **Missing Required Skills:** {stats.get('total_missing_required', 0)}")
            st.write(f"- **Missing Preferred Skills:** {stats.get('total_missing_preferred', 0)}")
            st.write(f"- **Overall Skills Match Ratio:** {match_pct}%")

    with sk_tab3:
        r_info = analysis.get("resume_info", {})
        edu_list = r_info.get("education")
        if not edu_list or edu_list == ["Not detected"]:
            edu_anal = analysis.get("education_analysis", {})
            edu_list = edu_anal.get("candidate_degrees", ["None detected"])
        st.markdown("#### Documented Information Found in Resume")
        st.markdown(f"**Identified Education:** {', '.join(edu_list) if isinstance(edu_list, list) else str(edu_list)}")
        st.markdown(f"**Work Experience Section:** {r_info.get('work_experience', 'Historical record does not retain full experience text')[:300]}...")
        st.markdown(f"**Projects Identified:** {r_info.get('projects', 'Historical record does not retain raw projects text')[:300]}...")
        st.markdown(f"**Certifications Identified:** {r_info.get('certifications', 'Not detected')}")

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 4. Actionable Recommendations
    # ==========================================
    st.markdown("### 💡 Recommended Resume Optimizations")
    recs = analysis.get("recommendations", [])
    for idx, r in enumerate(recs, 1):
        st.markdown(f"**{idx}.** {r}")

    # Link to AI Assistant
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    if st.button("✨ Open AI Resume Improvement Assistant", type="secondary"):
        st.session_state["target_page"] = PAGE_IMPROVE
        st.rerun()
