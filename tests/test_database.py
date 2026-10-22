"""
Unit Tests for Database Operations and Report Generation
Tests SQLite initialization, insertion, retrieval, statistics,
deletion, and PDF report generation.
"""

import os
import tempfile
import pytest

from modules.database import (
    init_db,
    save_analysis,
    get_all_analyses,
    delete_analysis,
    clear_all_analyses,
    get_database_statistics
)
from modules.report_generator import build_pdf_report


class TestDatabaseAndReports:
    @pytest.fixture
    def temp_db(self):
        """Creates a temporary SQLite database file for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        init_db(path)
        yield path
        import gc
        gc.collect()
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def test_database_crud_operations(self, temp_db):
        """
        Verifies insert, retrieve, statistics, delete, and clear.
        """
        # 1. Initially empty
        stats = get_database_statistics(temp_db)
        assert stats["total_analyses"] == 0
        assert stats["average_score"] == 0.0

        # 2. Insert record 1
        rec1_id = save_analysis(
            overall_score=85.0,
            component_scores={"skills": 90.0, "experience": 80.0},
            job_title="Backend Developer",
            matching_skills=["Python", "PostgreSQL"],
            missing_skills=["Docker"],
            summary="Strong match with minor skill gaps.",
            db_path=temp_db
        )
        assert rec1_id > 0

        # 3. Insert record 2
        rec2_id = save_analysis(
            overall_score=75.0,
            component_scores={"skills": 70.0, "experience": 80.0},
            job_title="Full Stack Engineer",
            matching_skills=["React", "Node.js"],
            missing_skills=["Kubernetes"],
            summary="Good match.",
            db_path=temp_db
        )
        assert rec2_id > rec1_id

        # 4. Retrieve records
        records = get_all_analyses(temp_db)
        assert len(records) == 2
        assert records[0]["id"] == rec2_id  # Sorted DESC
        assert records[0]["overall_score"] == 75.0
        assert "React" in records[0]["matching_skills"]

        # 5. Check statistics
        stats_updated = get_database_statistics(temp_db)
        assert stats_updated["total_analyses"] == 2
        assert stats_updated["average_score"] == 80.0  # (85 + 75) / 2
        assert stats_updated["highest_score"] == 85.0
        assert stats_updated["latest_analysis"]["job_title"] == "Full Stack Engineer"

        # 6. Delete record 1
        deleted = delete_analysis(rec1_id, temp_db)
        assert deleted is True
        remaining = get_all_analyses(temp_db)
        assert len(remaining) == 1
        assert remaining[0]["id"] == rec2_id

        # 7. Clear all
        clear_all_analyses(temp_db)
        assert len(get_all_analyses(temp_db)) == 0

    def test_pdf_report_generation(self):
        """
        Verifies ReportLab PDF generation builds valid non-empty bytes.
        """
        mock_analysis = {
            "overall_score": 88.5,
            "grade": "Excellent Compatibility",
            "verdict": "Candidate demonstrates high technical alignment.",
            "component_scores": {
                "skills": 90.0,
                "experience": 85.0,
                "education": 100.0,
                "keywords": 80.0,
                "formatting": 95.0
            },
            "effective_weights": {
                "skills": 0.40,
                "experience": 0.20,
                "education": 0.15,
                "keywords": 0.15,
                "formatting": 0.10
            },
            "skills_analysis": {
                "matching_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
                "missing_required": ["Kubernetes"],
                "missing_preferred": ["AWS Lambda"]
            },
            "recommendations": [
                "Highlight familiarity with Kubernetes in project bullet points.",
                "Quantify accomplishments with performance metrics."
            ]
        }

        pdf_bytes = build_pdf_report(
            mock_analysis,
            candidate_name="Jane Doe",
            job_title="Lead AI Engineer"
        )

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 1000
        # Check PDF header magic bytes '%PDF'
        assert pdf_bytes[:4] == b"%PDF"
