"""
About Project Component
Documents the project objective, technical architecture, scoring methodology,
ATS myths vs facts, and privacy disclosures.
"""

import streamlit as st
from config.settings import APP_NAME, APP_VERSION, APP_SUBTITLE, DEFAULT_WEIGHTS, ATS_DISCLAIMER


def render_about_view():
    """
    Renders the About Project page.
    """
    st.markdown(f"## ℹ️ About {APP_NAME}")
    st.caption(f"Version {APP_VERSION} • {APP_SUBTITLE}")

    # Project Overview Card
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title">Engineering Project Overview</div>
            <div class="hero-subtitle">
                A production-style AI Resume Analyzer and ATS Score Checker designed to empower candidates
                with transparent algorithmic insights into recruitment automation and keyword alignment.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    t1, t2, t3, t4 = st.tabs([
        "📐 Scoring Methodology",
        "⚙️ Technology Stack",
        "💡 ATS Myths vs Facts",
        "🔒 Security & Privacy"
    ])

    # ==========================================
    # Tab 1: Scoring Methodology
    # ==========================================
    with t1:
        st.markdown("### Transparent Weighted Scoring Engine")
        st.markdown(
            """
            Applicant Tracking Systems (ATS) score and filter resumes through algorithmic feature matching.
            This application uses a transparent, deterministic weighted scoring formula:
            """
        )

        st.code(
            """Final Score = (Skills Match × 0.40)
            + (Relevant Experience × 0.20)
            + (Education Match × 0.15)
            + (Job Keywords × 0.15)
            + (Formatting & Structure × 0.10)""",
            language="text"
        )

        st.markdown("#### Weight Distribution & Rationale")
        table_html = """
        <table class="clean-table">
            <thead>
                <tr>
                    <th>Component</th>
                    <th>Default Weight</th>
                    <th>What It Measures</th>
                    <th>Missing Data Policy</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>Skills Matching</b></td>
                    <td>40%</td>
                    <td>Exact & alias-normalized matching of required vs preferred technical proficiencies.</td>
                    <td>Default 100% if no skills specified in JD.</td>
                </tr>
                <tr>
                    <td><b>Relevant Experience</b></td>
                    <td>20%</td>
                    <td>Chronological tenure and explicit years of experience vs job requirements.</td>
                    <td>Re-normalizes over remaining weights if dates absent.</td>
                </tr>
                <tr>
                    <td><b>Education Matching</b></td>
                    <td>15%</td>
                    <td>Academic tier alignment (Bachelor's, Master's, Doctorate) vs job prerequisites.</td>
                    <td>Satisfied if JD does not mandate a degree.</td>
                </tr>
                <tr>
                    <td><b>Job Keywords</b></td>
                    <td>15%</td>
                    <td>Frequency and presence of meaningful domain terms, with TF-IDF cosine alignment.</td>
                    <td>Calculated over extracted unique keywords.</td>
                </tr>
                <tr>
                    <td><b>Formatting & Readability</b></td>
                    <td>10%</td>
                    <td>Contact completeness, standard section headings, document length, and active verbs.</td>
                    <td>Always evaluated on extracted document structure.</td>
                </tr>
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    # ==========================================
    # Tab 2: Technology Stack
    # ==========================================
    with t2:
        st.markdown("### Architecture & Technology Stack")
        st.markdown(
            """
            - **Frontend Framework:** Streamlit with custom CSS design system inspired by Linear and Notion.
            - **Document Parsing:**
                - `PyMuPDF` (`fitz`): High-speed vector PDF text extraction and scanned document detection.
                - `python-docx`: Body paragraph and multi-column table extraction from DOCX resumes.
            - **Natural Language Processing (NLP):**
                - `scikit-learn`: TF-IDF vectorization and cosine similarity calculation.
                - Regular Expressions & Boundary Matchers: Substring-safe skills matching and contact isolation.
            - **AI Improvement Engine:**
                - Optional Google Gemini & Hugging Face REST APIs.
                - Robust offline rule-based fallback engine (zero paid API dependencies).
            - **Visualizations:** Plotly interactive gauge, radar, bar, and donut charts.
            - **Report Generation:** ReportLab dynamic PDF generation with custom two-pass page numbering.
            - **Database:** Local SQLite with parameterized SQL and JSON serialization.
            - **Testing Suite:** `pytest` test suite with automated edge case verification.
            """
        )

    # ==========================================
    # Tab 3: ATS Myths vs Facts
    # ==========================================
    with t3:
        st.markdown("### Demystifying Applicant Tracking Systems")
        
        myths = [
            (
                "Myth 1: An ATS automatically rejects every resume with tables or columns.",
                "Fact: Modern enterprise ATS (Workday, Greenhouse, Lever, Taleo) easily parse clean table structures. However, multi-column designs with floating text boxes can scramble the reading sequence. Simple single-column layouts remain the safest."
            ),
            (
                "Myth 2: 'White font' keyword stuffing will fool the ATS into giving you 100%.",
                "Fact: ATS extract text and strip styling, rendering invisible white text fully visible to the human recruiter. Doing this will result in immediate disqualification."
            ),
            (
                "Myth 3: An ATS score guarantees an interview callback.",
                "Fact: The ATS is a search and ranking tool for human recruiters. Final hiring decisions and interview invitations are always evaluated by human hiring teams."
            )
        ]

        for myth, fact in myths:
            st.markdown(
                f"""
                <div class="content-card" style="margin-bottom: 1rem;">
                    <div style="font-weight: 700; color: #EF4444; margin-bottom: 0.25rem;">❌ {myth}</div>
                    <div style="color: #059669; font-size: 0.9rem; line-height: 1.4;">✅ <b>{fact}</b></div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ==========================================
    # Tab 4: Security & Privacy
    # ==========================================
    with t4:
        st.markdown("### Security & Privacy Disclosures")
        st.markdown(
            """
            - **In-Memory Processing:** Resumes are processed in temporary RAM memory during the session.
            - **No Unsolicited File Storage:** Original PDF and DOCX files are discarded after processing.
            - **Local Database:** Only metadata metrics (score, job title, skills count) are saved locally in `data/analyses.db` if enabled.
            - **No Hardcoded Secrets:** All API keys are loaded via environment variables or entered into session state.
            """
        )

        st.markdown(
            f"""
            <div class="callout-box callout-warning" style="margin-top: 1rem;">
                <b>Legal Disclaimer:</b><br/>
                {ATS_DISCLAIMER}
            </div>
            """,
            unsafe_allow_html=True
        )
