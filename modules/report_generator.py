"""
PDF Report Generator Module
Creates professional, publication-quality ATS Compatibility Evaluation Reports
using ReportLab.
Includes executive summary, score cards, skills breakdown tables, recommendations,
disclaimer, and dynamic page numbering.
"""
import io
from datetime import datetime
from typing import Dict, Any, List

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
    )
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def _safe_xml(val: Any) -> str:
    """Safely escapes XML control characters for ReportLab Paragraphs."""
    if val is None:
        return ""
    return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if REPORTLAB_AVAILABLE:
    class NumberedCanvas(canvas.Canvas):
        """
        Two-pass canvas to dynamically compute and draw total page count
        and running headers/footers on every page.
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(num_pages)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def draw_page_number(self, page_count: int):
            self.saveState()
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor("#64748B"))
            
            # Header (pages > 1)
            if self._pageNumber > 1:
                self.drawString(54, letter[1] - 36, "AI Resume Analyzer & ATS Score Checker — Evaluation Report")
                self.setStrokeColor(colors.HexColor("#E2E8F0"))
                self.setLineWidth(0.5)
                self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

            # Footer (all pages)
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(letter[0] - 54, 36, page_text)
            self.drawString(54, 36, "Confidential — Generated for personal career development only")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 48, letter[0] - 54, 48)
            self.restoreState()
else:
    NumberedCanvas = None


def build_pdf_report(
    analysis_results: Dict[str, Any],
    candidate_name: str = "Candidate",
    job_title: str = "Not specified",
    output_path: str = None
) -> bytes:
    """
    Generates a PDF analysis report and returns bytes (or writes to output_path).
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab library is not installed.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom palette
    primary_color = colors.HexColor("#1E3A8A")  # Deep blue
    accent_color = colors.HexColor("#4F46E5")   # Indigo
    text_color = colors.HexColor("#1E293B")     # Dark slate
    gray_muted = colors.HexColor("#64748B")     # Muted text
    card_bg = colors.HexColor("#F8FAFC")        # Soft gray
    border_color = colors.HexColor("#E2E8F0")

    # Typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=gray_muted,
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=text_color,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "BulletText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_color,
        leftIndent=12,
        spaceAfter=4
    )

    # Resolve candidate name and job title fallbacks
    if candidate_name == "Candidate" and analysis_results.get("candidate_name"):
        candidate_name = analysis_results.get("candidate_name")
    if (job_title == "Not specified" or not job_title) and analysis_results.get("job_title"):
        job_title = analysis_results.get("job_title")

    elements = []

    # 1. Header & Title Block
    elements.append(Paragraph("ATS Compatibility Evaluation Report", title_style))
    analysis_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    meta_text = (
        f"<b>Candidate:</b> {_safe_xml(candidate_name)} &nbsp;|&nbsp; "
        f"<b>Target Role:</b> {_safe_xml(job_title)} &nbsp;|&nbsp; "
        f"<b>Date:</b> {_safe_xml(analysis_date)}"
    )
    elements.append(Paragraph(meta_text, subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=2, spaceAfter=12))

    # 2. Executive Summary Score Card
    overall_score = float(analysis_results.get("overall_score", 0.0))
    job_match_score = analysis_results.get("job_match_score")
    resume_quality_score = analysis_results.get("resume_quality_score")
    comp_scores_tmp = analysis_results.get("component_scores", {}) or {}
    if resume_quality_score is None:
        resume_quality_score = float(comp_scores_tmp.get("formatting") or 0.0)

    grade = analysis_results.get("grade")
    if not grade:
        grade = "Excellent Compatibility" if overall_score >= 85 else (
            "Strong Compatibility" if overall_score >= 70 else (
                "Moderate Compatibility" if overall_score >= 50 else "Low Compatibility"
            )
        )
    verdict = analysis_results.get("verdict") or analysis_results.get("summary") or "Evaluation complete."

    jm_display = f"{job_match_score:.1f}%" if job_match_score is not None else "N/A (General Audit)"
    rq_display = f"{resume_quality_score:.1f}%"

    score_card_data = [
        [
            Paragraph(f"<font size=24 color='#1E3A8A'><b>{overall_score:.1f}</b></font><font size=12 color='#64748B'>/100</font><br/><b>{_safe_xml(grade)}</b>", body_style),
            Paragraph(
                f"<b>Job-Specific Match:</b> {_safe_xml(jm_display)} &nbsp;|&nbsp; "
                f"<b>Resume Quality:</b> {_safe_xml(rq_display)}<br/><br/>"
                f"<b>Executive Evaluation:</b><br/>{_safe_xml(verdict)}",
                body_style
            )
        ]
    ]

    score_table = Table(score_card_data, colWidths=[2.2 * inch, 4.8 * inch])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), card_bg),
        ("BOX", (0, 0), (-1, -1), 1, border_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 14))

    # 3. Component Scores Breakdown Table
    elements.append(Paragraph("1. Weighted Component Breakdown", h1_style))
    
    comp_scores = analysis_results.get("component_scores", {}) or {}
    weights = analysis_results.get("effective_weights", {}) or {
        "skills": 0.40, "experience": 0.20, "education": 0.15, "keywords": 0.15, "formatting": 0.10
    }

    table_data = [
        [
            Paragraph("<b>Component</b>", body_style),
            Paragraph("<b>Score</b>", body_style),
            Paragraph("<b>Weight</b>", body_style),
            Paragraph("<b>Evaluation Notes</b>", body_style)
        ]
    ]

    component_labels = {
        "skills": ("Skills Alignment", "Coverage of required and preferred technical proficiencies."),
        "experience": ("Relevant Experience", "Documented years and tenure vs job requirements."),
        "education": ("Academic Credentials", "Required degree tiers and educational qualifications."),
        "keywords": ("Keyword Relevance", "Coverage of key domain terms and contextual overlap."),
        "formatting": ("Document Structure", "Layout clarity, contact completeness, and ATS readability.")
    }

    for comp_key, (label, desc) in component_labels.items():
        score_val = comp_scores.get(comp_key)
        score_str = f"{score_val:.1f}%" if score_val is not None else "Insufficient Data"
        weight_str = f"{weights.get(comp_key, 0.0) * 100:.0f}%" if comp_key in weights else "—"
        table_data.append([
            Paragraph(f"<b>{_safe_xml(label)}</b>", body_style),
            Paragraph(_safe_xml(score_str), body_style),
            Paragraph(_safe_xml(weight_str), body_style),
            Paragraph(_safe_xml(desc), body_style)
        ])

    breakdown_table = Table(table_data, colWidths=[1.8 * inch, 1.1 * inch, 0.9 * inch, 3.2 * inch])
    breakdown_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), card_bg),
        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(breakdown_table)
    elements.append(Spacer(1, 14))

    # 4. Skills Analysis
    elements.append(Paragraph("2. Skills Compatibility Matrix", h1_style))
    skills_data = analysis_results.get("skills_analysis", {}) or {}
    matching_skills = skills_data.get("matching_skills", []) or analysis_results.get("matching_skills", [])
    missing_req = skills_data.get("missing_required", []) or analysis_results.get("missing_skills", [])
    missing_pref = skills_data.get("missing_preferred", [])

    match_str = ", ".join(matching_skills) if matching_skills else "None explicitly detected matching job criteria."
    miss_req_str = ", ".join(missing_req) if missing_req else "None! All required skills were identified."
    miss_pref_str = ", ".join(missing_pref) if missing_pref else "None identified."

    skills_matrix_data = [
        [Paragraph("<font color='#059669'><b>Matching Skills:</b></font>", body_style), Paragraph(_safe_xml(match_str), body_style)],
        [Paragraph("<font color='#DC2626'><b>Missing Required:</b></font>", body_style), Paragraph(_safe_xml(miss_req_str), body_style)],
        [Paragraph("<font color='#D97706'><b>Missing Preferred:</b></font>", body_style), Paragraph(_safe_xml(miss_pref_str), body_style)]
    ]
    skills_table = Table(skills_matrix_data, colWidths=[1.8 * inch, 5.2 * inch])
    skills_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), card_bg),
        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(skills_table)
    elements.append(Spacer(1, 14))

    # 5. Strategic Recommendations
    elements.append(Paragraph("3. Actionable Improvement Recommendations", h1_style))
    recommendations = analysis_results.get("recommendations", [])
    if not recommendations:
        recommendations = [
            "Incorporate high-priority missing technical skills into your Skills and Project sections.",
            "Quantify bullet points with tangible metrics (e.g., % improvement, scale of users).",
            "Ensure standard headings (Experience, Education, Skills) are prominently positioned."
        ]

    for rec in recommendations:
        elements.append(Paragraph(f"• {_safe_xml(rec)}", bullet_style))

    elements.append(Spacer(1, 14))

    # 6. Scoring Disclaimer & Limitations
    elements.append(Paragraph("4. Methodology & Disclaimer", h1_style))
    disclaimer_text = (
        "<b>Important Notice:</b> This report provides an estimated compatibility evaluation generated by automated "
        "natural language processing algorithms. It calculates keyword frequency, section structure, and technical skill "
        "matching based strictly on the uploaded resume and provided job description. It is not an official score from "
        "Workday, Taleo, Greenhouse, Lever, or any employer's proprietary ATS. Hiring decisions are made by human recruiters, "
        "and this tool guarantees neither interview invitations nor employment."
    )
    elements.append(Paragraph(disclaimer_text, ParagraphStyle("Disc", parent=body_style, fontSize=8, leading=11, textColor=gray_muted)))

    # Build document
    doc.build(elements, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
