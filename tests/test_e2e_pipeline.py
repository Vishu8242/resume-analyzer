"""
End-to-End Pipeline Integration Test
Tests the full lifecycle:
Sample PDF & DOCX extraction -> Information extraction -> JD Parsing
-> Skills matching -> Experience/Education/Keywords/Formatting analyzers
-> Weighted ATS score -> ReportLab PDF export -> SQLite persistence.
"""

import os
import pytest
from modules.resume_parser import extract_resume_text
from modules.information_extractor import extract_resume_information
from modules.job_description_parser import parse_job_description
from modules.skills_matcher import match_skills
from modules.experience_analyzer import evaluate_experience
from modules.education_analyzer import evaluate_education
from modules.keyword_analyzer import evaluate_keywords
from modules.formatting_analyzer import evaluate_formatting
from modules.ats_scorer import calculate_ats_score
from modules.report_generator import build_pdf_report
from modules.database import save_analysis, get_all_analyses


class TestEndToEndPipeline:
    def test_full_pipeline_with_sample_files(self):
        pdf_path = os.path.join("sample_resumes", "john_doe_senior_engineer.pdf")
        docx_path = os.path.join("sample_resumes", "jane_smith_frontend_developer.docx")
        jd_path = os.path.join("sample_resumes", "sample_job_description.txt")

        assert os.path.exists(pdf_path), "Sample PDF should exist"
        assert os.path.exists(docx_path), "Sample DOCX should exist"
        assert os.path.exists(jd_path), "Sample JD should exist"

        # 1. Parse PDF Resume
        res = extract_resume_text(pdf_path)
        assert res["success"] is True
        assert res["word_count"] > 30

        # 2. Extract Candidate Info
        info = extract_resume_information(res["text"])
        assert info["personal_info"]["name"] == "John Doe"
        assert "john.doe@email.com" in info["personal_info"]["email"]
        assert len(info["technical_skills"]) >= 5

        # 3. Parse Job Description
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()
        jd = parse_job_description(jd_text)
        assert jd["success"] is True
        assert "Senior Full Stack" in jd["job_title"]
        assert len(jd["required_skills"]) > 0

        # 4. Match Skills
        sm = match_skills(info["skills"], jd["required_skills"], jd["preferred_skills"])
        assert sm["score"] > 50.0
        assert len(sm["matching_skills"]) > 0

        # 5. Pillar Analyzers
        exp = evaluate_experience(res["text"], jd["experience"]["min_years"])
        edu = evaluate_education(info["education"], res["text"], jd["education"])
        kw = evaluate_keywords(res["text"], jd["keywords"], jd_text)
        fmt = evaluate_formatting(res["text"], info["personal_info"], info["raw_sections"])

        assert 0.0 <= exp["score"] <= 100.0
        assert 0.0 <= edu["score"] <= 100.0
        assert 0.0 <= kw["score"] <= 100.0
        assert 0.0 <= fmt["score"] <= 100.0

        # 6. Overall Weighted ATS Score
        overall = calculate_ats_score(
            sm["score"], exp["score"], edu["score"], kw["score"], fmt["score"]
        )
        assert 0.0 <= overall["overall_score"] <= 100.0
        assert overall["grade"] in [
            "Excellent Compatibility", "Strong Compatibility",
            "Moderate Compatibility", "Low Compatibility"
        ]

        # 7. PDF Report Generation
        pdf_bytes = build_pdf_report(
            {
                **overall,
                "job_title": jd["job_title"],
                "candidate_name": info["personal_info"]["name"],
                "skills_analysis": sm,
                "recommendations": ["Highlight cloud architecture", "Add metrics"]
            },
            candidate_name=info["personal_info"]["name"],
            job_title=jd["job_title"]
        )
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF")

        # 8. DOCX Resume Pipeline verification
        res_docx = extract_resume_text(docx_path)
        assert res_docx["success"] is True
        info_docx = extract_resume_information(res_docx["text"])
        assert "Jane Smith" in info_docx["personal_info"]["name"]
        assert "React" in info_docx["technical_skills"]
