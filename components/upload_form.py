"""
Upload Form Component
Handles resume file upload (PDF/DOCX), text extraction preview,
information review, job description input (paste / TXT upload / sample),
and initiates full ATS evaluation.
"""

import os
import streamlit as st
from modules.resume_parser import extract_resume_text
from modules.information_extractor import extract_resume_information
from modules.job_description_parser import parse_job_description
from modules.skills_matcher import match_skills
from modules.experience_analyzer import evaluate_experience
from modules.education_analyzer import evaluate_education
from modules.keyword_analyzer import evaluate_keywords
from modules.formatting_analyzer import evaluate_formatting
from modules.ats_scorer import calculate_ats_score
from modules.database import save_analysis
from components.sidebar import PAGE_RESULTS


SAMPLE_JD = """Role: Senior Full Stack Python & AI Engineer
Company: CloudScale Innovations
Location: Remote

About the Role:
We are looking for an experienced Senior Full Stack Engineer to lead the design and development of our AI-driven SaaS platform. You will collaborate with product designers, data scientists, and DevOps teams to deliver resilient, high-performance web applications.

Requirements & Must Haves:
- 4+ years of professional software engineering experience.
- Bachelor's or Master's degree in Computer Science, Engineering, or related technical field.
- Strong proficiency in Python, JavaScript, and TypeScript.
- Deep expertise in React, Next.js, and Tailwind CSS on the frontend.
- Solid experience building backend services with FastAPI, Django, or Node.js.
- Practical experience with PostgreSQL, MongoDB, and Redis caching.
- Experience with Docker, Kubernetes, and CI/CD automation pipelines.
- Demonstrated ability with Git and Agile Scrum methodologies.

Preferred Qualifications & Nice to Have:
- Hands-on experience with Machine Learning, NLP, or Generative AI (LLMs, LangChain).
- Working knowledge of AWS (EC2, S3, Lambda) or Google Cloud Platform.
- Experience with scikit-learn or PyTorch.
- Familiarity with Microservices architecture and GraphQL APIs.

Responsibilities:
- Architect, build, and maintain scalable APIs and responsive user interfaces.
- Optimize database queries and background job queues for high throughput.
- Mentor junior engineers and conduct rigorous code reviews.
"""


def render_upload_form(settings: dict):
    """
    Renders the interactive upload form and analysis trigger.
    """
    st.markdown("## 🔍 Analyze Resume & Job Fit")
    st.caption("Upload your resume and provide a target job description to compute compatibility.")

    col1, col2 = st.columns([1, 1], gap="large")

    # ==========================================
    # Column 1: Resume Upload & Extraction
    # ==========================================
    with col1:
        st.markdown("### 1. Upload Resume")
        
        # Quick Load Sample Resume Buttons
        st.markdown("<p style='margin-bottom: 0.35rem; font-size: 0.85rem; color: #64748B;'>Test immediately with an included sample resume:</p>", unsafe_allow_html=True)
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("📄 Load John Doe (PDF)", use_container_width=True):
                st.session_state["sample_resume_path"] = os.path.join("sample_resumes", "john_doe_senior_engineer.pdf")
                st.rerun()
        with col_s2:
            if st.button("📝 Load Jane Smith (DOCX)", use_container_width=True):
                st.session_state["sample_resume_path"] = os.path.join("sample_resumes", "jane_smith_frontend_developer.docx")
                st.rerun()

        sample_path = st.session_state.get("sample_resume_path")

        uploaded_file = st.file_uploader(
            "Or choose your own PDF or DOCX file:",
            type=["pdf", "docx"],
            help="Maximum file size: 10MB. Text must be selectable.",
            key="resume_file_uploader"
        )

        # Clear sample resume if user uploads their own file
        if uploaded_file is not None and sample_path:
            del st.session_state["sample_resume_path"]
            sample_path = None

        if sample_path and uploaded_file is None:
            c_sample_info, c_sample_clear = st.columns([3, 1])
            with c_sample_info:
                st.info(f"Loaded sample: `{os.path.basename(sample_path)}`")
            with c_sample_clear:
                if st.button("✖ Clear", use_container_width=True):
                    del st.session_state["sample_resume_path"]
                    if "parsed_resume" in st.session_state:
                        del st.session_state["parsed_resume"]
                    if "extracted_info" in st.session_state:
                        del st.session_state["extracted_info"]
                    st.rerun()

        parsed_resume = None
        extracted_info = None

        # Determine target to extract
        target_resume_source = uploaded_file or (sample_path if os.path.exists(sample_path or "") else None)

        if target_resume_source is not None:
            with st.spinner("Extracting and normalizing resume text..."):
                parsed_resume = extract_resume_text(target_resume_source)

            if not parsed_resume.get("success"):
                st.error(f"❌ {parsed_resume.get('error', 'Failed to parse resume.')}")
                if parsed_resume.get("is_scanned"):
                    st.warning("⚠️ Scanned Image Detected: The document contains images without digital text. Please convert it to text using OCR or upload an original digital copy.")
            else:
                st.success(f"✓ Successfully extracted {parsed_resume['word_count']} words from {parsed_resume['filename']}")
                
                # Metadata card
                c_size = f"{parsed_resume['file_size'] / 1024:.1f} KB"
                st.markdown(
                    f"""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.75rem 1rem; margin: 0.5rem 0 1rem 0; font-size: 0.85rem;">
                        <b>File:</b> {parsed_resume['filename']} &nbsp;|&nbsp; 
                        <b>Format:</b> {parsed_resume['file_type']} &nbsp;|&nbsp; 
                        <b>Size:</b> {c_size} &nbsp;|&nbsp; 
                        <b>Est. Pages:</b> {parsed_resume['page_count']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Extract information
                extracted_info = extract_resume_information(parsed_resume["text"])
                st.session_state["parsed_resume"] = parsed_resume
                st.session_state["extracted_info"] = extracted_info

                # Review extracted details expander
                with st.expander("👀 Review Extracted Candidate Information", expanded=True):
                    p_info = extracted_info["personal_info"]
                    st.markdown(f"**Identified Name:** `{p_info.get('name', 'Not detected')}`")
                    st.markdown(f"**Email:** `{p_info.get('email', 'Not detected')}` &nbsp;•&nbsp; **Phone:** `{p_info.get('phone', 'Not detected')}`")
                    st.markdown(f"**LinkedIn:** `{p_info.get('linkedin', 'Not detected')}`")
                    st.markdown(f"**GitHub:** `{p_info.get('github', 'Not detected')}`")
                    st.markdown(f"**Portfolio:** `{p_info.get('portfolio', 'Not detected')}`")

                    # Extracted Skills
                    skills_list = extracted_info.get("technical_skills", [])
                    st.markdown(f"**Detected Technical Skills ({len(skills_list)}):**")
                    if skills_list:
                        skills_html = " ".join([f"<span class='badge badge-primary'>{s}</span>" for s in skills_list[:25]])
                        st.markdown(skills_html, unsafe_allow_html=True)
                    else:
                        st.caption("No standard technical skills detected from the predefined dictionary.")

                # Raw Text Preview
                with st.expander("📄 View Normalized Resume Text", expanded=False):
                    st.text_area("Extracted Text", parsed_resume["text"][:3000], height=200, disabled=True)
        else:
            st.info("Please upload your PDF or DOCX resume, or select a sample resume above.")

    # ==========================================
    # Column 2: Job Description Input (Optional)
    # ==========================================
    with col2:
        st.markdown("### 2. Target Job Description *(Optional)*")
        st.caption("Optional: Provide a target job posting to compare skill fit. Leave blank for a general resume audit.")
        
        tab_paste, tab_upload, tab_skip = st.tabs(["✍️ Paste Description", "📂 Upload TXT File", "⏭️ Skip / General Audit"])
        jd_input_text = ""

        with tab_paste:
            c_btn1, c_btn2 = st.columns([1, 1])
            with c_btn1:
                if st.button("📋 Load Sample Software Engineer JD", use_container_width=True):
                    st.session_state["jd_text_input"] = SAMPLE_JD
                    st.rerun()
            with c_btn2:
                if st.button("🗑️ Clear Description", use_container_width=True):
                    st.session_state["jd_text_input"] = ""
                    st.rerun()

            jd_input_text = st.text_area(
                "Paste the job posting requirements below (or leave blank for general audit):",
                height=260,
                placeholder="Optional: Paste the target job description here to check role-specific skill alignment...",
                key="jd_text_input"
            )

        with tab_upload:
            uploaded_jd_file = st.file_uploader("Upload job description .txt file", type=["txt"], key="jd_file_uploader")
            if uploaded_jd_file is not None:
                try:
                    jd_input_text = uploaded_jd_file.read().decode("utf-8")
                    st.success("✓ Job description loaded from text file.")
                except Exception as e:
                    st.error(f"Error reading TXT file: {str(e)}")

        with tab_skip:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.25rem; margin-top: 0.5rem;">
                    <div style="font-weight: 700; color: #0F172A; font-size: 0.95rem; margin-bottom: 0.5rem;">
                        💡 General ATS Readiness & Quality Audit Mode
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.5;">
                        You don't need a specific job posting to analyze your resume! If you leave the job description empty:
                        <ul style="margin-top: 0.5rem; margin-bottom: 0.5rem; padding-left: 1.25rem;">
                            <li><b>Document Structure:</b> Verifies ATS section headers, contact completeness, length & action verbs.</li>
                            <li><b>Skills Inventory:</b> Extracts and categorizes all technical & soft skills found in your resume.</li>
                            <li><b>Experience & Education:</b> Evaluates chronological tenure and academic degree qualifications.</li>
                        </ul>
                        Simply click the <b>Analyze Resume</b> button below once your resume is uploaded.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        has_jd = bool(jd_input_text and jd_input_text.strip())
        parsed_jd = None

        if has_jd:
            parsed_jd = parse_job_description(jd_input_text)
            st.session_state["parsed_jd"] = parsed_jd
            st.session_state["jd_raw_text"] = jd_input_text

            # Display parsed JD highlights
            with st.expander("🎯 Target Job Requirements Preview", expanded=True):
                st.markdown(f"**Target Role:** `{parsed_jd['job_title']}`")
                st.markdown(f"**Required Experience:** `{parsed_jd['experience']['summary']}`")
                
                req_skills = parsed_jd.get("required_skills", [])
                pref_skills = parsed_jd.get("preferred_skills", [])
                
                st.markdown(f"**Required Skills ({len(req_skills)}):**")
                if req_skills:
                    req_html = " ".join([f"<span class='badge badge-danger'>{s}</span>" for s in req_skills])
                    st.markdown(req_html, unsafe_allow_html=True)
                else:
                    st.caption("No explicit required skills isolated.")

                if pref_skills:
                    st.markdown(f"**Preferred / Bonus Skills ({len(pref_skills)}):**")
                    pref_html = " ".join([f"<span class='badge badge-warning'>{s}</span>" for s in pref_skills])
                    st.markdown(pref_html, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Target job description is optional. Leave blank for a general audit, or paste requirements above for role-specific matching.")

    # ==========================================
    # Action Button: Run ATS Analysis
    # ==========================================
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    ready_to_analyze = (
        parsed_resume is not None
        and parsed_resume.get("success")
    )

    btn_label = "🚀 Calculate Estimated ATS Score & Job Fit Analysis" if has_jd else "🚀 Analyze Resume (General ATS & Skills Audit)"

    if st.button(btn_label, type="primary", use_container_width=True, disabled=not ready_to_analyze):
        with st.spinner("Analyzing skills alignment, experience depth, education hierarchy, and document formatting..."):
            resume_text = parsed_resume["text"]
            jd_text = jd_input_text if has_jd else ""

            # 1. Skills Matching Engine
            cand_skills = extracted_info.get("skills", {})
            tech_skills = extracted_info.get("technical_skills", [])
            soft_skills = extracted_info.get("soft_skills", [])

            if has_jd:
                skills_res = match_skills(
                    cand_skills,
                    parsed_jd.get("required_skills", []),
                    parsed_jd.get("preferred_skills", [])
                )
            else:
                # General Skills Inventory mode
                total_tech = len(tech_skills)
                if total_tech >= 10:
                    s_score = 95.0
                elif total_tech >= 6:
                    s_score = 88.0
                elif total_tech >= 3:
                    s_score = 75.0
                elif total_tech >= 1:
                    s_score = 65.0
                else:
                    s_score = 45.0

                skills_res = {
                    "matching_skills": tech_skills,
                    "matching_required": tech_skills,
                    "matching_preferred": soft_skills,
                    "missing_required": [],
                    "missing_preferred": [],
                    "additional_skills": [],
                    "match_percentage": 100.0 if total_tech > 0 else 0.0,
                    "score": s_score,
                    "score_explanation": (
                        f"General Skills Inventory: {total_tech} technical skills detected. "
                        "Provide a target job description to measure exact missing required skills."
                    ),
                    "categorized_matches": {},
                    "categorized_missing": {},
                    "stats": {
                        "total_job_skills": total_tech,
                        "total_matching": total_tech,
                        "total_missing_required": 0,
                        "total_missing_preferred": 0,
                        "total_candidate_skills": len(tech_skills) + len(soft_skills)
                    }
                }
                parsed_jd = {
                    "success": True,
                    "job_title": "General Professional Profile",
                    "required_skills": [],
                    "preferred_skills": [],
                    "all_skills": [],
                    "experience": {"min_years": 0, "summary": "General Evaluation (No minimum specified)"},
                    "education": {"required_degrees": ["Open / Not specified"], "has_strict_requirement": False},
                    "keywords": [],
                    "word_count": 0
                }

            # 2. Experience Engine
            exp_res = evaluate_experience(
                resume_text,
                parsed_jd.get("experience", {}).get("min_years", 0),
                extracted_info.get("work_experience", "")
            )

            # 3. Education Engine
            edu_res = evaluate_education(
                extracted_info.get("education", []),
                resume_text,
                parsed_jd.get("education", {}),
                jd_text
            )

            # 4. Keyword Engine
            if has_jd:
                kw_res = evaluate_keywords(
                    resume_text,
                    parsed_jd.get("keywords", []),
                    jd_text
                )
            else:
                kw_res = {
                    "score": None,
                    "matching_keywords": [],
                    "missing_keywords": [],
                    "match_ratio": 0.0,
                    "semantic_similarity": 0.0,
                    "explanation": "Target job description was omitted; role-specific keyword analysis not applied."
                }

            # 5. Formatting Engine
            fmt_res = evaluate_formatting(
                resume_text,
                extracted_info.get("personal_info", {}),
                extracted_info.get("raw_sections", {})
            )

            # 6. Overall Weighted ATS Score Engine (with Dual-Score Separation)
            custom_weights = settings.get("weights")
            scoring_res = calculate_ats_score(
                skills_score=skills_res["score"],
                experience_score=exp_res["score"],
                education_score=edu_res["score"],
                keyword_score=kw_res["score"] if has_jd else None,
                formatting_score=fmt_res["score"],
                weights=custom_weights,
                has_jd=has_jd,
                formatting_details=fmt_res
            )

            # Compile strategic recommendations
            recommendations = []
            if has_jd:
                if skills_res.get("missing_required"):
                    top_miss = ", ".join(skills_res["missing_required"][:4])
                    recommendations.append(f"High Priority: Add missing required skills if experienced with them: {top_miss}.")
                if kw_res.get("missing_keywords"):
                    top_kw = ", ".join(kw_res["missing_keywords"][:5])
                    recommendations.append(f"Incorporate target keywords naturally into project summaries: {top_kw}.")
            else:
                recommendations.append("Role Targeting: Paste a target job description to see tailored keyword and skill gap analysis.")
                if len(tech_skills) < 5:
                    recommendations.append("Expand Technical Skills section with specific tools, frameworks, and programming languages.")

            if exp_res.get("insufficient_information"):
                recommendations.append("Format work experience with explicit employment dates (Month Year – Month Year) to assist ATS tenure parsing.")
            if fmt_res.get("suggestions"):
                recommendations.extend(fmt_res["suggestions"][:2])

            # Assemble complete analysis bundle with Dual-Score structure
            analysis_bundle = {
                "overall_score": scoring_res["overall_score"],
                "job_match_score": scoring_res.get("job_match_score"),
                "resume_quality_score": scoring_res.get("resume_quality_score"),
                "grade": scoring_res["grade"],
                "job_match_grade": scoring_res.get("job_match_grade"),
                "resume_quality_grade": scoring_res.get("resume_quality_grade"),
                "color": scoring_res["color"],
                "job_match_color": scoring_res.get("job_match_color"),
                "resume_quality_color": scoring_res.get("resume_quality_color"),
                "verdict": scoring_res["verdict"],
                "job_match_verdict": scoring_res.get("job_match_verdict"),
                "resume_quality_verdict": scoring_res.get("resume_quality_verdict"),
                "component_scores": scoring_res["component_scores"],
                "effective_weights": scoring_res["effective_weights"],
                "excluded_components": scoring_res["excluded_components"],
                "missing_policy_applied": scoring_res["missing_policy_applied"],
                "score_breakdown": scoring_res.get("score_breakdown", {}),
                "has_jd": has_jd,
                "job_title": parsed_jd.get("job_title", "Software Engineer"),
                "candidate_name": extracted_info.get("personal_info", {}).get("name", "Candidate"),
                "skills_analysis": skills_res,
                "experience_analysis": exp_res,
                "education_analysis": edu_res,
                "keyword_analysis": kw_res,
                "formatting_analysis": fmt_res,
                "recommendations": recommendations,
                "resume_info": extracted_info,
                "jd_info": parsed_jd,
                "disclaimer": scoring_res["disclaimer"]
            }

            # Save to SQLite database if enabled
            if settings.get("enable_history", True):
                try:
                    record_id = save_analysis(
                        overall_score=scoring_res["overall_score"],
                        component_scores=scoring_res["component_scores"],
                        job_title=parsed_jd.get("job_title", "Software Engineer"),
                        matching_skills=skills_res.get("matching_skills", []),
                        missing_skills=skills_res.get("missing_required", []) + skills_res.get("missing_preferred", []),
                        summary=scoring_res["verdict"],
                        full_data=analysis_bundle
                    )
                    analysis_bundle["db_id"] = record_id
                except Exception as e:
                    st.warning(f"Note: Could not save to database history: {str(e)}")

            # Store active analysis in session state and switch to Results page
            st.session_state["active_analysis"] = analysis_bundle
            st.session_state["target_page"] = PAGE_RESULTS
            st.rerun()
