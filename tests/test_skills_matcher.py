"""
Unit Tests for Skills Matching Engine
Verifies alias normalization, boundary matching, required vs preferred classification,
and missing skill detection.
"""

import pytest
from config.skills_dictionary import find_skills_in_text
from modules.skills_matcher import match_skills


class TestSkillsMatcher:
    def test_alias_normalization(self):
        """
        Verifies that known aliases normalize to canonical taxonomy skills:
        e.g., 'JS' -> 'JavaScript', 'k8s' -> 'Kubernetes', 'Postgres' -> 'PostgreSQL'.
        """
        text = "Experienced with JS, TypeScript, Postgres, and deployed on k8s."
        detected = find_skills_in_text(text)

        assert "JavaScript" in detected
        assert "TypeScript" in detected
        assert "PostgreSQL" in detected
        assert "Kubernetes" in detected

    def test_boundary_aware_matching(self):
        """
        Verifies that short names like 'C' or 'R' or 'Go' do not trigger false positive
        substring matches in words like 'Cat', 'React', 'Good'.
        """
        text = "The Cat reacted Good."
        detected = find_skills_in_text(text)

        # 'Cat' shouldn't match 'C', 'Good' shouldn't match 'Go'
        assert "Go" not in detected
        assert "C" not in detected

        # Standalone 'C' programming language
        text_with_c = "Strong foundation in C and Python programming."
        detected_c = find_skills_in_text(text_with_c)
        assert "C" in detected_c
        assert "Python" in detected_c

    def test_skills_matching_classification(self):
        """
        Verifies correct categorization into:
        - matching_required
        - matching_preferred
        - missing_required
        - missing_preferred
        - additional_skills
        """
        resume_skills = {"Python", "React", "Docker", "Git"}
        jd_required = ["Python", "React", "PostgreSQL", "FastAPI"]
        jd_preferred = ["Docker", "Kubernetes"]

        result = match_skills(resume_skills, jd_required, jd_preferred)

        assert set(result["matching_required"]) == {"Python", "React"}
        assert set(result["missing_required"]) == {"PostgreSQL", "FastAPI"}
        assert set(result["matching_preferred"]) == {"Docker"}
        assert set(result["missing_preferred"]) == {"Kubernetes"}
        assert set(result["additional_skills"]) == {"Git"}

    def test_skills_score_calculation(self):
        """
        Verifies skill score behavior:
        - 100% when all matched
        - 0% when none matched
        - Proportional weighting (75% on required, 25% on preferred)
        """
        # Perfect match
        res_full = match_skills(["Python", "AWS"], ["Python"], ["AWS"])
        assert res_full["score"] == 100.0

        # Zero match
        res_zero = match_skills(["Ruby"], ["Python", "Java"], ["AWS"])
        assert res_zero["score"] == 0.0

        # Half required (1/2 = 50%), all preferred (1/1 = 100%)
        # (0.50 * 0.75 + 1.0 * 0.25) * 100 = (0.375 + 0.25) * 100 = 62.5%
        res_half = match_skills(["Python", "AWS"], ["Python", "Java"], ["AWS"])
        assert res_half["score"] == 62.5
