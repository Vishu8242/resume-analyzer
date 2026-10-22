"""
ATS Score Calculation Engine
Calculates transparent weighted ATS compatibility score between 0 and 100.
Maintains clear separation between:
1. Job-Specific ATS Match Score (Skills, Experience, Education, Keywords alignment)
2. General Resume Quality Score (Formatting, Structure, Contact Completeness, Action Verbs, Readability)
Provides 100% deterministic scoring, strict [0, 100] normalization, and comprehensive
mathematical score breakdown explanations.
"""

from typing import Dict, List, Optional, Any, Tuple
from config.settings import DEFAULT_WEIGHTS, ATS_DISCLAIMER

# Default weighting for Job-Specific alignment pillars (sums to 1.0)
DEFAULT_JOB_MATCH_WEIGHTS = {
    "skills": 0.40,
    "experience": 0.25,
    "education": 0.15,
    "keywords": 0.20
}


def _get_compatibility_verdict(score: float) -> Tuple[str, str, str]:
    """Returns grade label, color hex, and explanatory verdict for overall ATS score."""
    if score >= 85:
        return (
            "Excellent Compatibility",
            "#10B981",
            "High probability of passing automated ATS filters. Resume closely matches job requirements."
        )
    elif score >= 70:
        return (
            "Strong Compatibility",
            "#3B82F6",
            "Good alignment with requirements. Addressing minor missing skills will further boost ranking."
        )
    elif score >= 50:
        return (
            "Moderate Compatibility",
            "#F59E0B",
            "Partially matches job requirements. Several required skills or keywords are absent."
        )
    else:
        return (
            "Low Compatibility",
            "#EF4444",
            "Significant gaps detected between resume and job description. Substantial tailoring recommended."
        )


def _get_quality_verdict(score: float) -> Tuple[str, str, str]:
    """Returns grade label, color hex, and explanatory verdict for general resume quality."""
    if score >= 85:
        return (
            "High Quality",
            "#10B981",
            "Resume demonstrates professional layout, complete contact info, strong action verbs, and clear ATS-friendly structure."
        )
    elif score >= 70:
        return (
            "Good Quality",
            "#3B82F6",
            "Resume has solid structural health. Minor polish to bullet point verbs or contact links will make it shine."
        )
    elif score >= 50:
        return (
            "Moderate Quality",
            "#F59E0B",
            "Document structure requires attention. Section headings, contact completeness, or content length need improvement."
        )
    else:
        return (
            "Needs Structural Polish",
            "#EF4444",
            "Significant formatting, length, or readability issues detected. Review ATS formatting guidelines."
        )


def calculate_ats_score(
    skills_score: Optional[float],
    experience_score: Optional[float],
    education_score: Optional[float],
    keyword_score: Optional[float],
    formatting_score: Optional[float],
    weights: Optional[Dict[str, float]] = None,
    has_jd: bool = True,
    formatting_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculates overall estimated ATS compatibility score using weighted components.
    Maintains strict separation between:
    - job_match_score: alignment against job requirements (None when has_jd is False)
    - resume_quality_score: standalone document health and ATS formatting structure
    - overall_score: composite score normalized to [0.0, 100.0]

    Formula (default):
    Overall Score = (Skills * 0.40) + (Experience * 0.20) + (Education * 0.15)
                  + (Keywords * 0.15) + (Formatting * 0.10)

    Missing-Data Policy:
    If a component score is None (insufficient information / excluded), the remaining
    available components' weights are proportionally re-normalized to sum to 1.0.
    """
    raw_weights = weights if weights else DEFAULT_WEIGHTS.copy()

    input_scores = {
        "skills": skills_score,
        "experience": experience_score,
        "education": education_score,
        "keywords": keyword_score,
        "formatting": formatting_score
    }

    available_components = {}
    excluded_components = []

    for name, score in input_scores.items():
        if score is not None:
            # Strictly clamp component score to [0.0, 100.0]
            clamped = max(0.0, min(100.0, float(score)))
            available_components[name] = clamped
        else:
            excluded_components.append(name)

    # -------------------------------------------------------------
    # 1. Standalone General Resume Quality Score
    # -------------------------------------------------------------
    # Evaluates formatting, structure, contacts, action verbs, and readability
    if formatting_score is not None:
        resume_quality_score = max(0.0, min(100.0, round(float(formatting_score), 1)))
    else:
        resume_quality_score = 0.0

    rq_grade, rq_color, rq_verdict = _get_quality_verdict(resume_quality_score)

    # -------------------------------------------------------------
    # 2. Job-Specific ATS Match Score
    # -------------------------------------------------------------
    # Evaluates the 4 job-matching pillars (Skills, Experience, Education, Keywords)
    job_components = ["skills", "experience", "education", "keywords"]
    available_job_comps = {k: available_components[k] for k in job_components if k in available_components}

    if not has_jd or not available_job_comps:
        job_match_score = None
        jm_grade = "N/A - General Audit Mode"
        jm_color = "#64748B"
        jm_verdict = (
            "Job-Specific ATS Match was not calculated because no target job description was provided. "
            "Submit a target job description to evaluate role-specific alignment."
            if not has_jd else
            "Insufficient job alignment data to calculate job-specific match."
        )
        job_match_weights = {}
    else:
        # Re-normalize job-specific weights
        total_job_wt = sum(DEFAULT_JOB_MATCH_WEIGHTS[k] for k in available_job_comps)
        if total_job_wt <= 0:
            job_match_weights = {k: 1.0 / len(available_job_comps) for k in available_job_comps}
        else:
            job_match_weights = {k: DEFAULT_JOB_MATCH_WEIGHTS[k] / total_job_wt for k in available_job_comps}

        weighted_job_sum = sum(available_job_comps[k] * job_match_weights[k] for k in available_job_comps)
        job_match_score = max(0.0, min(100.0, round(weighted_job_sum, 1)))
        jm_grade, jm_color, jm_verdict = _get_compatibility_verdict(job_match_score)
        # Adapt grade title to Job Match context
        jm_grade = jm_grade.replace("Compatibility", "Job Match")

    # -------------------------------------------------------------
    # 3. Overall Weighted Composite ATS Score
    # -------------------------------------------------------------
    if not available_components:
        return {
            "overall_score": 0.0,
            "job_match_score": None,
            "resume_quality_score": 0.0,
            "grade": "Insufficient Data",
            "job_match_grade": "Insufficient Data",
            "resume_quality_grade": "Insufficient Data",
            "color": "#64748B",
            "verdict": "Insufficient data provided to perform ATS evaluation.",
            "job_match_verdict": jm_verdict,
            "resume_quality_verdict": rq_verdict,
            "component_scores": {k: 0.0 for k in input_scores},
            "effective_weights": {},
            "base_weights": raw_weights,
            "excluded_components": list(input_scores.keys()),
            "missing_policy_applied": True,
            "score_breakdown": {
                "overall": {"formula": "No available component data", "pillars": {}},
                "job_match": {"formula": "No job description provided", "pillars": {}},
                "resume_quality": {"score": 0.0, "status": "No formatting data"}
            },
            "disclaimer": ATS_DISCLAIMER
        }

    # Sum of available weights for overall formula
    total_avail_weight = sum(raw_weights[name] for name in available_components)

    if total_avail_weight <= 0:
        total_avail_weight = len(available_components)
        effective_weights = {k: 1.0 / len(available_components) for k in available_components}
    else:
        effective_weights = {
            name: raw_weights[name] / total_avail_weight
            for name in available_components
        }

    # Compute overall weighted score
    weighted_sum = sum(
        available_components[name] * effective_weights[name]
        for name in available_components
    )

    # Strictly clamp between 0.0 and 100.0
    final_score = max(0.0, min(100.0, round(weighted_sum, 1)))

    overall_grade, overall_color, overall_verdict = _get_compatibility_verdict(final_score)
    missing_policy_applied = len(excluded_components) > 0

    # -------------------------------------------------------------
    # 4. Detailed Mathematical Score Breakdown
    # -------------------------------------------------------------
    overall_pillars = {}
    formula_terms = []
    for comp_name, score_val in available_components.items():
        eff_wt = effective_weights[comp_name]
        pts = round(score_val * eff_wt, 2)
        overall_pillars[comp_name] = {
            "score": score_val,
            "weight": round(eff_wt, 4),
            "weight_pct": round(eff_wt * 100, 1),
            "points_contributed": pts
        }
        formula_terms.append(f"({comp_name.title()}: {score_val:.1f} × {eff_wt * 100:.0f}%)")

    overall_formula_str = " + ".join(formula_terms) + f" = {final_score:.1f}/100"

    job_pillars = {}
    if job_match_score is not None:
        jm_terms = []
        for jk, score_val in available_job_comps.items():
            jwt = job_match_weights[jk]
            pts = round(score_val * jwt, 2)
            job_pillars[jk] = {
                "score": score_val,
                "weight": round(jwt, 4),
                "weight_pct": round(jwt * 100, 1),
                "points_contributed": pts
            }
            jm_terms.append(f"({jk.title()}: {score_val:.1f} × {jwt * 100:.0f}%)")
        job_formula_str = " + ".join(jm_terms) + f" = {job_match_score:.1f}/100"
    else:
        job_formula_str = "Job-specific match score requires a target job description."

    breakdown = {
        "overall": {
            "score": final_score,
            "formula": overall_formula_str,
            "pillars": overall_pillars
        },
        "job_match": {
            "score": job_match_score,
            "formula": job_formula_str,
            "pillars": job_pillars,
            "has_jd": has_jd
        },
        "resume_quality": {
            "score": resume_quality_score,
            "grade": rq_grade,
            "verdict": rq_verdict,
            "formula": f"Resume Document Health & Formatting = {resume_quality_score:.1f}/100",
            "checks": formatting_details.get("checks", []) if formatting_details else []
        }
    }

    return {
        "overall_score": final_score,
        "job_match_score": job_match_score,
        "resume_quality_score": resume_quality_score,
        "grade": overall_grade,
        "job_match_grade": jm_grade,
        "resume_quality_grade": rq_grade,
        "color": overall_color,
        "job_match_color": jm_color,
        "resume_quality_color": rq_color,
        "verdict": overall_verdict,
        "job_match_verdict": jm_verdict,
        "resume_quality_verdict": rq_verdict,
        "component_scores": {
            k: (available_components[k] if k in available_components else None)
            for k in input_scores
        },
        "effective_weights": {k: round(v, 4) for k, v in effective_weights.items()},
        "base_weights": raw_weights,
        "excluded_components": excluded_components,
        "missing_policy_applied": missing_policy_applied,
        "score_breakdown": breakdown,
        "disclaimer": ATS_DISCLAIMER
    }

