"""
Comprehensive Tests for Deterministic ATS Scoring, Dual-Score Separation,
Duplicate Keyword Prevention, and False Match Prevention.
"""

import pytest
from modules.ats_scorer import calculate_ats_score
from modules.keyword_analyzer import (
    evaluate_keywords,
    deduplicate_keywords,
    build_keyword_pattern,
    calculate_tfidf_similarity
)
from modules.skills_matcher import match_skills
from modules.job_description_parser import parse_job_description, extract_keywords_from_jd
from modules.experience_analyzer import evaluate_experience
from modules.education_analyzer import evaluate_education
from modules.formatting_analyzer import evaluate_formatting


class TestDeterministicScoring:
    """Verifies that the same resume and JD always produce 100% identical scores."""

    def test_strict_reproducibility_across_iterations(self):
        """
        Runs the full scoring pipeline on identical resume and JD 50 times.
        Every score must be identical to 6 decimal places across all runs.
        """
        resume_text = """
        Alex Johnson
        alex.johnson@email.com | +1-555-019-2834 | linkedin.com/in/alexjohnson | github.com/alexj
        
        Professional Summary:
        Senior Full Stack Engineer with 6 years of experience building resilient cloud applications.
        
        Technical Skills:
        Python, JavaScript, TypeScript, React, Docker, Kubernetes, PostgreSQL, AWS, Git
        
        Work Experience:
        Senior Software Engineer | CloudTech Solutions
        Jan 2020 – Present
        - Architected scalable microservices using Python, FastAPI, and PostgreSQL.
        - Deployed containerized applications with Docker and Kubernetes on AWS.
        - Mentored junior engineers and spearheaded agile sprint delivery.
        
        Software Engineer | DataSystems Inc
        Jan 2018 – Dec 2019
        - Engineered frontend user interfaces with React and TypeScript.
        - Optimized relational database queries, reducing latency by 45%.
        
        Education:
        Bachelor of Science in Computer Science, Tech University (2014 – 2018)
        """

        jd_text = """
        Job Title: Senior Backend Engineer
        Requirements:
        - 5+ years of software engineering experience
        - Bachelor's degree in Computer Science or related field
        - Expert in Python, PostgreSQL, Docker, AWS, and Git
        - Nice to have: Kubernetes, React
        """

        # Pre-parse inputs
        parsed_jd = parse_job_description(jd_text)
        
        scores_history = []
        for _ in range(50):
            # 1. Skills
            resume_skills = {"Python", "JavaScript", "TypeScript", "React", "Docker", "Kubernetes", "PostgreSQL", "AWS", "Git"}
            skills_res = match_skills(
                resume_skills,
                parsed_jd.get("required_skills", ["Python", "PostgreSQL", "Docker", "AWS", "Git"]),
                parsed_jd.get("preferred_skills", ["Kubernetes", "React"])
            )

            # 2. Experience
            exp_res = evaluate_experience(resume_text, parsed_jd["experience"]["min_years"])

            # 3. Education
            edu_res = evaluate_education(["Bachelor of Science in Computer Science"], resume_text, parsed_jd["education"], jd_text)

            # 4. Keywords
            kw_res = evaluate_keywords(resume_text, parsed_jd["keywords"], jd_text)

            # 5. Formatting
            fmt_res = evaluate_formatting(
                resume_text,
                {"name": "Alex Johnson", "email": "alex.johnson@email.com", "phone": "+1-555-019-2834"},
                {"skills": "...", "experience": "...", "education": "..."}
            )

            # 6. ATS Scorer
            score_bundle = calculate_ats_score(
                skills_score=skills_res["score"],
                experience_score=exp_res["score"],
                education_score=edu_res["score"],
                keyword_score=kw_res["score"],
                formatting_score=fmt_res["score"],
                has_jd=True
            )

            scores_history.append((
                score_bundle["overall_score"],
                score_bundle["job_match_score"],
                score_bundle["resume_quality_score"],
                score_bundle["grade"],
                score_bundle["job_match_grade"]
            ))

        # Assert every single run produced the exact same tuple
        first_run = scores_history[0]
        for idx, run in enumerate(scores_history[1:], start=2):
            assert run == first_run, f"Run #{idx} produced different scores: {run} vs {first_run}"


class TestDuplicateKeywordAndFalseMatchPrevention:
    """Verifies that duplicate keywords and false substring matches are strictly prevented."""

    def test_deduplicate_jd_keywords(self):
        """Duplicates in JD keywords must be collapsed case-insensitively."""
        raw_keywords = ["Python", "python", "PYTHON", "Docker", "docker", "AWS", "aws", "PostgreSQL"]
        deduped = deduplicate_keywords(raw_keywords)
        assert len(deduped) == 4
        assert deduped == ["Python", "Docker", "AWS", "PostgreSQL"]

    def test_repeated_resume_keywords_do_not_inflate_score(self):
        """
        A candidate repeating the same keyword 50 times in their resume must receive
        the exact same match ratio as a candidate mentioning it once.
        """
        resume_single = "Proficient in Python and Docker."
        resume_stuffed = "Python " * 50 + "Docker " * 50

        jd_keywords = ["Python", "Docker", "Kubernetes", "AWS"]

        res_single = evaluate_keywords(resume_single, jd_keywords)
        res_stuffed = evaluate_keywords(resume_stuffed, jd_keywords)

        # Both match exactly 2 out of 4 keywords
        assert res_single["match_ratio"] == 0.5
        assert res_stuffed["match_ratio"] == 0.5
        assert set(res_single["matching_keywords"]) == {"Python", "Docker"}
        assert set(res_stuffed["matching_keywords"]) == {"Python", "Docker"}

    def test_false_match_java_vs_javascript(self):
        """'Java' must NOT falsely match 'JavaScript'."""
        resume_text = "Proficient in JavaScript and React frontend development."
        res = evaluate_keywords(resume_text, ["Java", "JavaScript"])

        assert "JavaScript" in res["matching_keywords"]
        assert "Java" not in res["matching_keywords"]
        assert "Java" in res["missing_keywords"]

    def test_false_match_sql_vs_nosql(self):
        """'SQL' must NOT falsely match 'NoSQL'."""
        resume_text = "Experienced in MongoDB and NoSQL architectures."
        res = evaluate_keywords(resume_text, ["SQL"])

        assert "SQL" not in res["matching_keywords"]
        assert "SQL" in res["missing_keywords"]

    def test_false_match_go_vs_good(self):
        """'Go' must NOT falsely match words like 'Good' or 'Going'."""
        resume_text = "Good team player with strong ongoing communication skills."
        res = evaluate_keywords(resume_text, ["Go"])

        assert "Go" not in res["matching_keywords"]
        assert "Go" in res["missing_keywords"]

    def test_false_match_c_vs_words_and_initials(self):
        """'C' must NOT falsely match 'Cat', 'React', 'Vitamin C', or 'Section C'."""
        resume_text = "The candidate completed Section C and took Vitamin C while building React apps."
        res = evaluate_keywords(resume_text, ["C"])

        assert "C" not in res["matching_keywords"]
        assert "C" in res["missing_keywords"]

    def test_positive_match_c_programming_language(self):
        """'C' must properly match when written as a programming language."""
        resume_text_1 = "Strong experience programming in C, C++, and Python."
        res_1 = evaluate_keywords(resume_text_1, ["C", "C++", "Python"])
        assert "C" in res_1["matching_keywords"]
        assert "C++" in res_1["matching_keywords"]
        assert "Python" in res_1["matching_keywords"]

        resume_text_2 = "Hands-on experience with C programming and embedded systems."
        res_2 = evaluate_keywords(resume_text_2, ["C"])
        assert "C" in res_2["matching_keywords"]

    def test_special_symbols_cpp_csharp_dotnet(self):
        """Special language symbols C++, C#, and .NET must match accurately."""
        resume_text = "Developed enterprise services in C# and .NET Core, with high-performance C++ modules."
        res = evaluate_keywords(resume_text, ["C++", "C#", ".NET", "Java"])

        assert "C++" in res["matching_keywords"]
        assert "C#" in res["matching_keywords"]
        assert ".NET" in res["matching_keywords"]
        assert "Java" not in res["matching_keywords"]


class TestDualScoreSeparation:
    """Verifies that General Resume Quality Score is kept strictly separate from Job-Specific ATS Match Score."""

    def test_dual_score_with_job_description(self):
        """When JD is provided, both Job-Specific ATS Match and Resume Quality scores are computed."""
        result = calculate_ats_score(
            skills_score=80.0,
            experience_score=90.0,
            education_score=100.0,
            keyword_score=70.0,
            formatting_score=85.0,
            has_jd=True
        )

        assert result["job_match_score"] is not None
        assert 0.0 <= result["job_match_score"] <= 100.0
        assert result["resume_quality_score"] == 85.0
        assert 0.0 <= result["overall_score"] <= 100.0
        assert result["job_match_grade"] in ("Excellent Job Match", "Strong Job Match", "Moderate Job Match")
        assert result["resume_quality_grade"] in ("High Quality", "Good Quality")

        # Verify score breakdown structure
        breakdown = result["score_breakdown"]
        assert "overall" in breakdown
        assert "job_match" in breakdown
        assert "resume_quality" in breakdown
        assert breakdown["job_match"]["has_jd"] is True

    def test_dual_score_without_job_description(self):
        """When JD is omitted (General Audit Mode), Job-Specific Match is None while Resume Quality is computed."""
        result = calculate_ats_score(
            skills_score=85.0,
            experience_score=90.0,
            education_score=100.0,
            keyword_score=None,  # No JD keywords
            formatting_score=92.0,
            has_jd=False
        )

        assert result["job_match_score"] is None
        assert result["job_match_grade"] == "N/A - General Audit Mode"
        assert result["resume_quality_score"] == 92.0
        assert result["resume_quality_grade"] == "High Quality"
        # Overall score uses remaining available components
        assert 0.0 <= result["overall_score"] <= 100.0
        assert result["missing_policy_applied"] is True

    def test_score_breakdown_mathematics(self):
        """Verifies that the score breakdown mathematical sums exactly match the overall score."""
        result = calculate_ats_score(
            skills_score=80.0,
            experience_score=70.0,
            education_score=100.0,
            keyword_score=60.0,
            formatting_score=90.0,
            has_jd=True
        )

        breakdown = result["score_breakdown"]["overall"]
        pillars = breakdown["pillars"]
        
        # Calculate sum of points contributed
        total_pts = sum(p["points_contributed"] for p in pillars.values())
        # Overall score must equal round(total_pts, 1) within floating precision
        assert round(total_pts, 1) == result["overall_score"]


class TestMultipleResumesAndJobDescriptions:
    """Tests diverse realistic candidate profiles and job requirements."""

    def test_software_engineer_strong_match(self):
        """Fullstack developer matching a Fullstack JD closely."""
        resume_skills = {"Python", "React", "TypeScript", "Docker", "PostgreSQL", "Git"}
        jd_required = ["Python", "React", "PostgreSQL"]
        jd_preferred = ["Docker", "TypeScript"]

        match_res = match_skills(resume_skills, jd_required, jd_preferred)
        assert match_res["score"] == 100.0
        assert len(match_res["missing_required"]) == 0

    def test_junior_developer_vs_senior_embedded_mismatch(self):
        """Junior web dev applying for senior embedded C/Rust role -> Low compatibility score."""
        resume_skills = {"HTML", "CSS", "JavaScript", "Bootstrap"}
        jd_required = ["C", "C++", "Rust", "Embedded Linux", "RTOS"]
        jd_preferred = ["ARM", "Device Drivers"]

        match_res = match_skills(resume_skills, jd_required, jd_preferred)
        # Skills score is 0
        assert match_res["score"] == 0.0
        assert len(match_res["matching_required"]) == 0
        assert len(match_res["missing_required"]) == 5

        # End-to-end score
        score_res = calculate_ats_score(
            skills_score=match_res["score"],
            experience_score=30.0,  # 1 year vs 5 required
            education_score=50.0,
            keyword_score=10.0,
            formatting_score=75.0,
            has_jd=True
        )
        assert score_res["overall_score"] < 40.0
        assert score_res["grade"] == "Low Compatibility"
        assert score_res["job_match_score"] < 30.0
        assert score_res["job_match_grade"] == "Low Job Match"

    def test_data_scientist_profile(self):
        """Data science candidate matching Python, R, SQL, and Machine Learning."""
        resume_skills = {"Python", "R", "SQL", "Machine Learning", "Pandas", "Scikit-Learn"}
        jd_required = ["Python", "SQL", "Machine Learning"]
        jd_preferred = ["R", "Deep Learning"]

        match_res = match_skills(resume_skills, jd_required, jd_preferred)
        assert "Python" in match_res["matching_required"]
        assert "SQL" in match_res["matching_required"]
        assert "R" in match_res["matching_preferred"]
        # Required is 100% (3/3), Preferred is 50% (1/2) -> (1.0 * 0.75 + 0.5 * 0.25) * 100 = 87.5%
        assert match_res["score"] == 87.5
