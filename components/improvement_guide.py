"""
Resume Improvement Guide Component
Provides tailored AI and rule-based advice:
- Professional summary rewrite
- Bullet point impact rewriter (action verbs & metric placeholders)
- STAR project structuring
- Achievement quantification formulas
- Authentic skill integration advice
"""

import streamlit as st
from modules.ai_assistant import (
    generate_improvement_suggestions,
    rule_based_summary_generation,
    rule_based_bullet_enhancement,
    rule_based_quantification_guide,
    rule_based_project_enhancement
)
from components.sidebar import PAGE_ANALYZE


def render_improvement_guide(settings: dict):
    """
    Renders the Resume Improvement Guide page.
    """
    st.markdown("## 💡 Resume Optimization & AI Assistant")
    st.caption("Transform your resume into a high-impact, ATS-optimized document adhering to strict truthfulness rules.")

    analysis = st.session_state.get("active_analysis")
    
    # Retrieve data from active analysis or defaults
    if analysis:
        resume_info = analysis.get("resume_info", {})
        job_info = analysis.get("jd_info", {})
        skills_match = analysis.get("skills_analysis", {})
        candidate_name = analysis.get("candidate_name", "Candidate")
        job_title = analysis.get("job_title", "Software Engineer")
    else:
        st.info("💡 Note: You can view universal resume improvement guides below, or analyze a resume to receive personalized recommendations.")
        resume_info = {
            "personal_info": {"name": "Candidate"},
            "technical_skills": ["Python", "JavaScript", "SQL", "React", "Docker"],
            "work_experience": "Developed web applications and worked on backend APIs.",
            "projects": "E-Commerce Web Application"
        }
        job_info = {"job_title": "Full Stack Engineer"}
        skills_match = {
            "missing_required": ["TypeScript", "PostgreSQL", "FastAPI"],
            "missing_preferred": ["AWS", "Kubernetes", "Redis"]
        }
        candidate_name = "Candidate"
        job_title = "Full Stack Engineer"

    # AI Provider Status Callout
    gemini_key = settings.get("gemini_key", "")
    provider_mode = "gemini" if gemini_key else "fallback"

    tab_summary, tab_bullets, tab_projects, tab_quantify, tab_skills = st.tabs([
        "📝 Summary Rewriter",
        "⚡ Bullet Point Enhancer",
        "🚀 STAR Projects",
        "📊 Quantifying Achievements",
        "🗺️ Skill Strategy"
    ])

    # ==========================================
    # Tab 1: Summary Rewriter
    # ==========================================
    with tab_summary:
        st.markdown("### Professional Summary Optimization")
        st.caption("A compelling professional summary captures recruiter attention in the first 6 seconds.")

        c_s1, c_s2 = st.columns([1, 1], gap="medium")
        with c_s1:
            st.markdown("#### Current Summary Detected")
            current_sum = resume_info.get("summary", "Not detected")
            st.text_area("Original Summary", current_sum, height=140, disabled=True)

        with c_s2:
            st.markdown("#### Recommended Tailored Summary")
            with st.spinner("Generating tailored summary..."):
                suggestions = generate_improvement_suggestions(
                    resume_info=resume_info,
                    job_info=job_info,
                    skills_match=skills_match,
                    provider=provider_mode,
                    custom_api_key=gemini_key
                )

            suggested_sum = suggestions.get("summary_recommendation")
            st.text_area("ATS-Optimized Summary", suggested_sum, height=140)
            st.caption(f"Engine: **{suggestions.get('provider_used')}**")

        st.markdown(
            """
            <div class="callout-box callout-info" style="margin-top: 1rem;">
                <b>Summary Best Practices:</b><br/>
                • State your core role identity and total relevant experience in the opening sentence.<br/>
                • Mention 3 to 4 top technical proficiencies that directly mirror the job posting.<br/>
                • Highlight your focus on scalability, clean code, and business impact.
            </div>
            """,
            unsafe_allow_html=True
        )

    # ==========================================
    # Tab 2: Bullet Point Enhancer
    # ==========================================
    with tab_bullets:
        st.markdown("### High-Impact Bullet Point Enhancer")
        st.caption("Transform passive duties into active accomplishment statements with quantifiable placeholders.")

        # Interactive rewriter tool
        st.markdown("#### 🛠️ Test Your Own Bullet Point")
        user_bullet = st.text_input(
            "Enter a weak bullet point to see the recommended enhancement:",
            value="Worked on developing backend APIs and fixing system bugs."
        )

        if user_bullet:
            enhanced = rule_based_bullet_enhancement(user_bullet)
            for item in enhanced:
                st.markdown(
                    f"""
                    <div class="content-card" style="margin-bottom: 0.75rem;">
                        <div style="font-size: 0.85rem; color: #EF4444; margin-bottom: 4px;">❌ <b>Original:</b> {item['original']}</div>
                        <div style="font-size: 0.95rem; color: #059669; font-weight: 600; margin-bottom: 4px;">✅ <b>High-Impact Rewrite:</b> {item['suggested']}</div>
                        <div style="font-size: 0.8rem; color: #64748B;">💡 <i>{item['rationale']}</i></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # General examples
        st.markdown("#### 🌟 Core Principles of Winning Bullet Points")
        st.markdown(
            """
            1. **Begin with a strong action verb** (e.g., *Engineered*, *Architected*, *Optimized*, *Spearheaded*).
            2. **Specify the tools and methods** (e.g., *leveraging Python, Docker, and PostgreSQL*).
            3. **End with measurable business impact** (e.g., *reducing API response times by 35%*).
            """
        )

    # ==========================================
    # Tab 3: STAR Projects Framework
    # ==========================================
    with tab_projects:
        st.markdown("### Structuring Projects using the STAR Framework")
        st.caption("Situation • Task • Action • Result")

        p_guide = rule_based_project_enhancement(
            resume_info.get("projects", "Flagship Project")[:30],
            resume_info.get("technical_skills", ["Python", "React"])
        )

        st.markdown(f"**Recommended Framework:** `{p_guide['framework']}`")
        st.info(p_guide["guidelines"])

        st.markdown("#### 📌 Example Project Formulation")
        st.code(p_guide["example_bullet"], language="text")

    # ==========================================
    # Tab 4: Quantifying Achievements
    # ==========================================
    with tab_quantify:
        st.markdown("### Actionable Quantification Formulas")
        st.caption("Recruiters and hiring managers remember numbers. Use these practical formulas to quantify your genuine work.")

        quant_items = rule_based_quantification_guide()
        for q in quant_items:
            with st.container():
                st.markdown(f"#### 📐 {q['category']}")
                st.markdown(f"**Formula:** `{q['formula']}`")
                st.markdown(f"**Example:** *\"{q['example']}\"*")
                st.divider()

    # ==========================================
    # Tab 5: Skill Strategy
    # ==========================================
    with tab_skills:
        st.markdown("### Ethical & Authentic Missing Skill Strategy")
        st.caption("How to close your ATS gap without fabricating experience.")

        missing_req = skills_match.get("missing_required", [])
        if missing_req:
            st.markdown(f"**Priority Skills to Address ({len(missing_req)}):**")
            st.markdown(" ".join([f"<span class='badge badge-danger'>{s}</span>" for s in missing_req]), unsafe_allow_html=True)
            
            st.markdown(
                """
                <div class="callout-box callout-warning" style="margin-top: 1rem;">
                    <b>Rules of Integrity:</b><br/>
                    • <b>If you already know the skill:</b> Add it explicitly into your Skills section and reference it in a project or job bullet point.<br/>
                    • <b>If you have related knowledge:</b> Mention your foundational familiarity (e.g. <i>"Familiar with PostgreSQL through MySQL database administration experience"</i>).<br/>
                    • <b>If you have not used it:</b> Build a weekend portfolio project demonstrating the technology, deploy it on GitHub, and document it under 'Key Projects'.
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.success("✓ You currently have no missing required skills detected!")
