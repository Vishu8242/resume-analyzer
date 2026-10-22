"""
Experience Analyzer Module
Analyzes work experience from resume text and compares against job requirements.
Handles date ranges, year calculations, and flags insufficient information explicitly.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


MONTHS_REGEX = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

# Date range patterns: e.g. "Jan 2020 - Present", "2018 - 2022", "06/2019 to 08/2021"
YEAR_RANGE_REGEX = re.compile(
    rf"(?:({MONTHS_REGEX})[\s,.-]+)?(\b20\d\d|\b19\d\d)\s*(?:-|–|—|to)\s*"
    rf"(?:(?:({MONTHS_REGEX})[\s,.-]+)?(\b20\d\d|\b19\d\d)|(present|current|now))",
    re.IGNORECASE
)

EXPLICIT_EXP_REGEX = re.compile(
    r"(\d+(?:\.\d+)?)\+?\s*years?(?:\s+of)?(?:\s+relevant|\s+work|\s+professional)?\s+experience",
    re.IGNORECASE
)


def estimate_experience_years(resume_text: str, experience_section_text: str = "") -> Tuple[float, List[str], bool]:
    """
    Estimates total years of experience using explicit mentions and detected date ranges.
    Returns (estimated_years, list_of_evidence_snippets, insufficient_evidence_flag).
    """
    evidence = []
    
    # 1. Check for explicit statements (e.g. "Over 4 years of experience in software development")
    explicit_matches = EXPLICIT_EXP_REGEX.findall(resume_text)
    if explicit_matches:
        try:
            years = max([float(m) for m in explicit_matches])
            evidence.append(f"Explicit mention found: '{years} years of experience'")
            return years, evidence, False
        except Exception:
            pass

    # 2. Check date intervals in experience section or resume
    search_text = experience_section_text if experience_section_text and experience_section_text != "Not detected" else resume_text
    matches = YEAR_RANGE_REGEX.findall(search_text)

    current_year = datetime.now().year
    intervals = []

    for m in matches:
        start_year = int(m[1])
        if m[4]:  # "present" / "current"
            end_year = current_year
        elif m[3]:
            end_year = int(m[3])
        else:
            end_year = start_year

        # Plausibility check (between 1980 and current year + 1)
        if 1980 <= start_year <= current_year + 1 and start_year <= end_year <= current_year + 1:
            intervals.append((start_year, end_year))
            evidence.append(f"Date interval: {start_year} - {end_year if not m[4] else 'Present'}")

    if not intervals:
        return 0.0, ["No chronological work experience dates detected in resume."], True

    # Merge overlapping intervals to prevent double-counting
    intervals.sort(key=lambda x: x[0])
    merged = []
    for interval in intervals:
        if not merged:
            merged.append(interval)
        else:
            prev_start, prev_end = merged[-1]
            if interval[0] <= prev_end:
                merged[-1] = (prev_start, max(prev_end, interval[1]))
            else:
                merged.append(interval)

    total_years = sum(end - start for start, end in merged)
    # If 0 (e.g., started and ended in same year), count as at least 0.5 year
    if total_years == 0 and merged:
        total_years = len(merged) * 0.5

    return round(total_years, 1), evidence, False


def evaluate_experience(
    resume_text: str,
    jd_min_years: int = 0,
    experience_section_text: str = ""
) -> Dict[str, Any]:
    """
    Evaluates candidate experience against job requirements.
    Calculates an experience score from 0 to 100.
    """
    cand_years, evidence, insufficient = estimate_experience_years(resume_text, experience_section_text)

    if jd_min_years <= 0:
        # Job description does not require specific years
        score = 100.0
        explanation = (
            f"The job description does not mandate a minimum number of years. "
            f"Candidate has approximately {cand_years} years of documented experience."
            if not insufficient else
            "No specific experience length mandated in job description."
        )
        status = "Satisfied"
    elif insufficient:
        # Candidate experience dates were not found
        score = 50.0  # Moderate baseline when evidence is insufficient
        explanation = (
            f"Insufficient date or tenure information in resume to verify the required "
            f"{jd_min_years}+ years of experience. A partial score was applied."
        )
        status = "Insufficient Information"
    else:
        if cand_years >= jd_min_years:
            score = 100.0
            explanation = (
                f"Candidate meets or exceeds experience requirement: "
                f"~{cand_years} years identified vs {jd_min_years}+ years required."
            )
            status = "Strong Match"
        else:
            ratio = cand_years / jd_min_years
            score = round(ratio * 100.0, 1)
            explanation = (
                f"Candidate has approximately {cand_years} years of documented experience, "
                f"which is below the target requirement of {jd_min_years}+ years."
            )
            status = "Below Target"

    # Clamp
    score = max(0.0, min(100.0, float(score)))

    return {
        "score": score,
        "candidate_years": cand_years,
        "required_years": jd_min_years,
        "status": status,
        "explanation": explanation,
        "evidence": evidence,
        "insufficient_information": insufficient
    }
