"""
Skills Matcher Module
Compares candidate skills against job requirements.
Categorizes skills into:
- Matching required skills
- Matching preferred skills
- Missing required skills
- Missing preferred skills
- Additional resume skills
Calculates weighted skill match score (0 - 100).
"""

from typing import Dict, List, Set, Any, Union
from config.skills_dictionary import SKILLS_TAXONOMY


def match_skills(
    resume_skills: Union[List[str], Set[str], Dict[str, Any]],
    jd_required_skills: Union[List[str], Set[str]],
    jd_preferred_skills: Union[List[str], Set[str]] = None
) -> Dict[str, Any]:
    """
    Compares candidate's extracted skills with the job description's required and preferred skills.
    Returns categorized match lists and an objective skills score.
    """
    if jd_preferred_skills is None:
        jd_preferred_skills = []

    # Normalize sets
    if isinstance(resume_skills, dict):
        resume_set = set(resume_skills.keys())
    else:
        resume_set = set(resume_skills)

    req_set = set(jd_required_skills)
    pref_set = set(jd_preferred_skills)

    # Calculate intersections and differences
    matching_required = sorted(list(resume_set.intersection(req_set)))
    missing_required = sorted(list(req_set - resume_set))

    matching_preferred = sorted(list(resume_set.intersection(pref_set)))
    missing_preferred = sorted(list(pref_set - resume_set))

    all_matching = sorted(list(resume_set.intersection(req_set | pref_set)))
    all_job_skills = sorted(list(req_set | pref_set))
    
    additional_skills = sorted(list(resume_set - (req_set | pref_set)))

    # Calculate skill score (0 to 100)
    # Policy:
    # If both required and preferred exist: 75% weight on required, 25% on preferred
    # If only required exists: 100% on required
    # If only preferred exists: 100% on preferred
    # If no job skills specified: insufficient evidence -> score is 100 with warning
    has_req = len(req_set) > 0
    has_pref = len(pref_set) > 0

    if not has_req and not has_pref:
        skill_score = 100.0
        score_explanation = "No specific technical skills were identified in the job description."
    elif has_req and has_pref:
        req_ratio = len(matching_required) / len(req_set)
        pref_ratio = len(matching_preferred) / len(pref_set)
        skill_score = (req_ratio * 0.75 + pref_ratio * 0.25) * 100.0
        score_explanation = (
            f"Matched {len(matching_required)} of {len(req_set)} required skills (75% weight) "
            f"and {len(matching_preferred)} of {len(pref_set)} preferred skills (25% weight)."
        )
    elif has_req:
        req_ratio = len(matching_required) / len(req_set)
        skill_score = req_ratio * 100.0
        score_explanation = f"Matched {len(matching_required)} of {len(req_set)} required skills."
    else:
        pref_ratio = len(matching_preferred) / len(pref_set)
        skill_score = pref_ratio * 100.0
        score_explanation = f"Matched {len(matching_preferred)} of {len(pref_set)} preferred skills."

    # Clamp score strictly between 0 and 100
    skill_score = max(0.0, min(100.0, round(skill_score, 1)))

    # Categorize matching and missing skills by domain
    categorized_matches: Dict[str, List[str]] = {}
    for skill in all_matching:
        cat = SKILLS_TAXONOMY.get(skill, {}).get("category", "Other")
        categorized_matches.setdefault(cat, []).append(skill)

    categorized_missing: Dict[str, List[str]] = {}
    for skill in (missing_required + missing_preferred):
        cat = SKILLS_TAXONOMY.get(skill, {}).get("category", "Other")
        categorized_missing.setdefault(cat, []).append(skill)

    total_target_count = len(all_job_skills)
    match_percentage = round((len(all_matching) / total_target_count * 100), 1) if total_target_count > 0 else 0.0

    return {
        "matching_skills": all_matching,
        "matching_required": matching_required,
        "matching_preferred": matching_preferred,
        "missing_required": missing_required,
        "missing_preferred": missing_preferred,
        "additional_skills": additional_skills,
        "match_percentage": match_percentage,
        "score": skill_score,
        "score_explanation": score_explanation,
        "categorized_matches": categorized_matches,
        "categorized_missing": categorized_missing,
        "stats": {
            "total_job_skills": total_target_count,
            "total_matching": len(all_matching),
            "total_missing_required": len(missing_required),
            "total_missing_preferred": len(missing_preferred),
            "total_candidate_skills": len(resume_set)
        }
    }
