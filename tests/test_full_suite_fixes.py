"""
Comprehensive Tests for Resume Analyzer Bug Fixes and Enhancements
Covers:
- Email domain exclusion from portfolio URL extraction
- Legitimate portfolio URL extraction
- Full analysis bundle persistence in SQLite database
- Legacy database record graceful reconstruction
- ReportLab PDF generator special characters escaping (XML safety)
- Robust None handling in charts component
"""

import os
import pytest
from modules.information_extractor import extract_contact_info
from modules.database import init_db, save_analysis, get_all_analyses, delete_analysis, clear_all_analyses
from modules.report_generator import build_pdf_report, _safe_xml
from components.charts import (
    create_radar_chart,
    create_horizontal_bar_chart,
    create_skills_donut_chart,
    create_gauge_chart
)


class TestContactExtractorFixes:
    def test_email_domain_not_captured_as_portfolio(self):
        """
        Verifies that email addresses like john.doe@email.com or jane@techmail.com
        do NOT cause email.com or techmail.com to be flagged as personal portfolio websites.
        """
        text = """
        John Doe
        Email: john.doe@email.com
        Phone: (555) 019-2834
        Boston, MA
        GitHub: https://github.com/johndoe
        LinkedIn: https://linkedin.com/in/johndoe
        """
        contacts = extract_contact_info(text)
        assert contacts["name"] == "John Doe"
        assert contacts["email"] == "john.doe@email.com"
        assert contacts["portfolio"] == "Not detected"

    def test_legitimate_portfolio_detection(self):
        """
        Verifies that actual candidate portfolio websites are accurately extracted.
        """
        text = """
        Jane Smith
        Email: jane@techmail.com
        Portfolio: https://janesmith.dev
        Phone: 555-123-4567
        """
        contacts = extract_contact_info(text)
        assert contacts["email"] == "jane@techmail.com"
        assert "janesmith.dev" in contacts["portfolio"]


class TestDatabaseFullDataBundle:
    def test_full_analysis_bundle_roundtrip(self, tmp_path):
        """
        Verifies that full analysis bundle is stored and completely restored
        without losing skills analysis, stats, weights, or verdict.
        """
        test_db = str(tmp_path / "test_full_bundle.db")
        init_db(test_db)

        full_bundle = {
            "overall_score": 88.5,
            "grade": "Excellent Compatibility",
            "color": "#10B981",
            "verdict": "Candidate demonstrates high technical alignment with modern cloud stack.",
            "job_title": "Lead Full Stack AI Engineer",
            "candidate_name": "Alice Wonderland",
            "component_scores": {
                "skills": 95.0, "experience": 85.0, "education": 100.0, "keywords": 80.0, "formatting": 90.0
            },
            "effective_weights": {
                "skills": 0.40, "experience": 0.20, "education": 0.15, "keywords": 0.15, "formatting": 0.10
            },
            "skills_analysis": {
                "matching_skills": ["Python", "FastAPI", "React", "Docker"],
                "missing_required": ["Kubernetes"],
                "missing_preferred": ["LangChain"],
                "additional_skills": ["Git", "Linux"],
                "stats": {
                    "total_job_skills": 6,
                    "total_matching": 4,
                    "total_missing_required": 1,
                    "total_missing_preferred": 1,
                    "total_candidate_skills": 6
                },
                "match_percentage": 66.7
            },
            "recommendations": [
                "Acquire hands-on experience with Kubernetes orchestration.",
                "Highlight production LangChain application development."
            ]
        }

        rec_id = save_analysis(
            overall_score=88.5,
            component_scores=full_bundle["component_scores"],
            job_title=full_bundle["job_title"],
            matching_skills=full_bundle["skills_analysis"]["matching_skills"],
            missing_skills=full_bundle["skills_analysis"]["missing_required"],
            summary=full_bundle["verdict"],
            full_data=full_bundle,
            db_path=test_db
        )
        assert rec_id > 0

        records = get_all_analyses(test_db)
        assert len(records) == 1
        retrieved = records[0]

        assert retrieved["overall_score"] == 88.5
        assert retrieved["grade"] == "Excellent Compatibility"
        assert retrieved["color"] == "#10B981"
        assert retrieved["candidate_name"] == "Alice Wonderland"
        assert retrieved["verdict"] == full_bundle["verdict"]
        assert len(retrieved["skills_analysis"]["matching_skills"]) == 4
        assert retrieved["skills_analysis"]["stats"]["total_matching"] == 4
        assert len(retrieved["recommendations"]) == 2

    def test_legacy_database_record_fallback_reconstruction(self, tmp_path):
        """
        Verifies that records saved without full_data still construct all required fields
        so results_view and report_generator do not crash or show empty cards.
        """
        test_db = str(tmp_path / "test_legacy.db")
        init_db(test_db)

        # Save legacy style without full_data
        rec_id = save_analysis(
            overall_score=78.0,
            component_scores={"skills": 80.0, "experience": 75.0},
            job_title="Software Developer",
            matching_skills=["Python", "SQL"],
            missing_skills=["AWS", "Docker"],
            summary="Solid candidate fit.",
            db_path=test_db
        )

        records = get_all_analyses(test_db)
        assert len(records) == 1
        rec = records[0]

        assert rec["grade"] == "Strong Compatibility"
        assert rec["verdict"] == "Solid candidate fit."
        assert rec["skills_analysis"]["matching_skills"] == ["Python", "SQL"]
        assert rec["skills_analysis"]["missing_required"] == ["AWS", "Docker"]
        assert rec["skills_analysis"]["stats"]["total_matching"] == 2
        assert len(rec["recommendations"]) >= 1


class TestReportGeneratorSafety:
    def test_xml_special_characters_escaping(self):
        """
        Verifies that user strings containing XML special characters like &, <, >
        do not crash ReportLab paragraph parsing.
        """
        escaped = _safe_xml("Developer <C++ & HTML> & CSS")
        assert "&amp;" in escaped
        assert "&lt;" in escaped
        assert "&gt;" in escaped

    def test_build_pdf_report_with_special_characters(self):
        """
        Generates PDF report where candidate name, title, skills, and verdict
        contain XML characters and verifies build succeeds without ExpatError.
        """
        analysis = {
            "overall_score": 82.5,
            "grade": "Strong Compatibility",
            "verdict": "Candidate excels in C++ & Frontend <UI/UX> architectures.",
            "job_title": "R&D Principal Software Engineer <Systems>",
            "candidate_name": "Tom & Jerry",
            "component_scores": {
                "skills": 85.0, "experience": 80.0, "education": 100.0, "keywords": 75.0, "formatting": 90.0
            },
            "effective_weights": {
                "skills": 0.40, "experience": 0.20, "education": 0.15, "keywords": 0.15, "formatting": 0.10
            },
            "skills_analysis": {
                "matching_skills": ["C++", "HTML & CSS", "TCP/IP"],
                "missing_required": ["Embedded <C>"],
                "missing_preferred": ["CI/CD & Jenkins"]
            },
            "recommendations": [
                "Document experience with <RTOS> & embedded devices.",
                "Highlight automated CI/CD & unit testing."
            ]
        }

        pdf_bytes = build_pdf_report(analysis)
        assert pdf_bytes is not None
        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 1000


class TestChartsDefensiveHandling:
    def test_charts_with_none_inputs(self):
        """
        Verifies that None or empty inputs to chart functions do not raise AttributeError.
        """
        assert create_radar_chart(None) is not None
        assert create_horizontal_bar_chart(None) is not None
        assert create_skills_donut_chart(None) is None
        assert create_gauge_chart(75.0) is not None


class TestOptionalJobDescriptionPipeline:
    def test_analysis_without_target_job_description(self, tmp_path):
        """
        Verifies that a resume can be fully evaluated when the target job description
        is omitted (optional), generating a valid general audit score, PDF report,
        and database record.
        """
        from modules.resume_parser import extract_resume_text
        from modules.information_extractor import extract_resume_information
        from modules.experience_analyzer import evaluate_experience
        from modules.education_analyzer import evaluate_education
        from modules.formatting_analyzer import evaluate_formatting
        from modules.ats_scorer import calculate_ats_score

        pdf_path = os.path.join("sample_resumes", "john_doe_senior_engineer.pdf")
        assert os.path.exists(pdf_path)

        res = extract_resume_text(pdf_path)
        assert res["success"] is True

        info = extract_resume_information(res["text"])
        tech_skills = info.get("technical_skills", [])
        soft_skills = info.get("soft_skills", [])
        assert len(tech_skills) >= 5

        # Simulating upload_form.py optional JD execution path
        total_tech = len(tech_skills)
        if total_tech >= 10:
            s_score = 95.0
        elif total_tech >= 6:
            s_score = 88.0
        else:
            s_score = 75.0

        skills_res = {
            "matching_skills": tech_skills,
            "matching_required": tech_skills,
            "matching_preferred": soft_skills,
            "missing_required": [],
            "missing_preferred": [],
            "additional_skills": [],
            "match_percentage": 100.0,
            "score": s_score,
            "stats": {
                "total_job_skills": total_tech,
                "total_matching": total_tech,
                "total_missing_required": 0,
                "total_missing_preferred": 0,
                "total_candidate_skills": len(tech_skills) + len(soft_skills)
            }
        }

        exp_res = evaluate_experience(res["text"], 0, info.get("work_experience", ""))
        assert exp_res["score"] >= 80.0

        edu_res = evaluate_education(info.get("education", []), res["text"], {"required_degrees": []}, "")
        assert edu_res["score"] == 100.0

        kw_score = 85.0
        fmt_res = evaluate_formatting(res["text"], info["personal_info"], info["raw_sections"])
        assert fmt_res["score"] >= 70.0

        scoring = calculate_ats_score(
            skills_score=skills_res["score"],
            experience_score=exp_res["score"],
            education_score=edu_res["score"],
            keyword_score=kw_score,
            formatting_score=fmt_res["score"]
        )
        assert 70.0 <= scoring["overall_score"] <= 100.0
        assert scoring["grade"] in ("Excellent Compatibility", "Strong Compatibility")

        # Bundle and save
        bundle = {
            "overall_score": scoring["overall_score"],
            "grade": scoring["grade"],
            "color": scoring["color"],
            "verdict": scoring["verdict"],
            "component_scores": scoring["component_scores"],
            "effective_weights": scoring["effective_weights"],
            "job_title": "General Professional Profile",
            "candidate_name": info["personal_info"]["name"],
            "skills_analysis": skills_res,
            "recommendations": ["Expand Technical Skills section with specific tools."]
        }

        test_db = str(tmp_path / "test_optional_jd.db")
        rec_id = save_analysis(
            overall_score=scoring["overall_score"],
            component_scores=scoring["component_scores"],
            job_title="General Professional Profile",
            matching_skills=tech_skills,
            missing_skills=[],
            summary=scoring["verdict"],
            full_data=bundle,
            db_path=test_db
        )
        assert rec_id > 0

        # Retrieve and verify PDF report generation without JD
        records = get_all_analyses(test_db)
        assert len(records) == 1
        retrieved = records[0]
        assert retrieved["job_title"] == "General Professional Profile"

        pdf_bytes = build_pdf_report(retrieved)
        assert pdf_bytes is not None
        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 1000
