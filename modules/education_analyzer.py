"""
Education Analyzer Module
Compares candidate's educational degrees against job requirements.
Ranks educational tiers fairly and never penalizes for optional qualifications.
"""

import re
from typing import Dict, List, Any


DEGREE_LEVELS = {
    "doctorate": 4,
    "phd": 4,
    "master": 3,
    "m.tech": 3,
    "m.s": 3,
    "mca": 3,
    "mba": 3,
    "bachelor": 2,
    "b.tech": 2,
    "b.e": 2,
    "bca": 2,
    "b.s": 2,
    "associate": 1,
    "diploma": 1,
    "high school": 1
}


def detect_highest_degree_level(degrees: List[str], text: str = "") -> int:
    """
    Returns the integer hierarchy level (1 to 4) of candidate's highest detected degree.
    """
    combined = " ".join(degrees) + " " + text
    combined_lower = combined.lower()

    if re.search(r"\b(?:ph\.?d\.?|doctorate|doctoral)\b", combined_lower):
        return 4
    if re.search(r"\b(?:master'?s?|m\.?tech|m\.?s|m\.?e|mca|mba|m\.?sc)\b", combined_lower):
        return 3
    if re.search(r"\b(?:bachelor'?s?|b\.?tech|b\.?e|bca|b\.?s|b\.?sc|undergraduate)\b", combined_lower):
        return 2
    if re.search(r"\b(?:associate|diploma|high\s+school)\b", combined_lower):
        return 1
    return 0


def detect_jd_required_level(jd_degrees: List[str], jd_text: str = "") -> int:
    """
    Determines minimum required educational level from job description.
    """
    combined = " ".join(jd_degrees) + " " + jd_text
    combined_lower = combined.lower()

    # Look for minimum requirement keywords
    if re.search(r"\b(?:ph\.?d\.?|doctorate)\s*(?:required|needed|must\s+have)\b", combined_lower):
        return 4
    if re.search(r"\b(?:master'?s?|m\.?s|m\.?tech|mba|mca)\s*(?:required|or\s+equivalent|minimum)\b", combined_lower):
        return 3
    if re.search(r"\b(?:bachelor'?s?|b\.?tech|b\.?e|b\.?s|bca|degree\s+in)\b", combined_lower):
        return 2
    if re.search(r"\b(?:associate|high\s+school|diploma)\b", combined_lower):
        return 1
    
    # If mentions master's anywhere
    if any("master" in d.lower() or "phd" in d.lower() for d in jd_degrees):
        return 3
    if any("bachelor" in d.lower() for d in jd_degrees):
        return 2

    return 0  # No strict degree stated


def evaluate_education(
    candidate_education: List[str],
    resume_text: str,
    jd_education_req: Dict[str, Any],
    jd_text: str = ""
) -> Dict[str, Any]:
    """
    Evaluates candidate education match against JD requirements.
    Calculates education score (0 to 100).
    """
    cand_level = detect_highest_degree_level(candidate_education, resume_text)
    jd_degrees = jd_education_req.get("required_degrees", [])
    jd_level = detect_jd_required_level(jd_degrees, jd_text)

    # Clean list of candidate degrees
    valid_degrees = [d for d in candidate_education if d != "Not detected"]
    if not valid_degrees and cand_level > 0:
        tier_names = {4: "Doctorate / PhD", 3: "Master's Degree", 2: "Bachelor's Degree", 1: "Associate / Diploma"}
        valid_degrees = [tier_names.get(cand_level, "Higher Education Degree")]

    if jd_level == 0:
        # JD did not specify a mandatory degree
        score = 100.0
        if cand_level > 0:
            explanation = "Job has open educational requirements. Candidate possesses verified higher education."
        else:
            explanation = "Job has open educational requirements; no mandatory degree threshold specified."
        status = "Satisfied"
    elif cand_level >= jd_level:
        score = 100.0
        explanation = f"Candidate's education meets or exceeds the required level (Level {cand_level} vs Level {jd_level})."
        status = "Full Match"
    elif cand_level == jd_level - 1 and cand_level > 0:
        score = 75.0
        explanation = "Candidate holds a relevant degree one tier below preferred level (e.g., Bachelor's vs Master's)."
        status = "Near Match"
    elif cand_level > 0:
        score = 50.0
        explanation = "Candidate possesses foundational education, but below the specified degree requirement."
        status = "Partial Match"
    else:
        # No degree detected in resume at all
        score = 30.0
        explanation = "No recognizable higher education degree or academic qualifications detected in resume."
        status = "Insufficient Information"

    score = max(0.0, min(100.0, float(score)))

    return {
        "score": score,
        "candidate_degrees": valid_degrees if valid_degrees else ["None explicitly detected"],
        "required_degrees": jd_degrees,
        "candidate_level": cand_level,
        "required_level": jd_level,
        "status": status,
        "explanation": explanation
    }
