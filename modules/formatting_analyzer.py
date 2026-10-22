"""
Formatting & Readability Analyzer Module
Evaluates resume document structure, section headings, contact completeness,
length, and readability for ATS parsing safety.
"""

import re
from typing import Dict, List, Any


ACTION_VERBS = {
    "led", "developed", "designed", "implemented", "created", "built", "engineered",
    "architected", "managed", "spearheaded", "optimized", "reduced", "increased",
    "improved", "automated", "delivered", "deployed", "scaled", "collaborated",
    "conducted", "analyzed", "generated", "mentored", "orchestrated", "transformed"
}


def evaluate_formatting(
    resume_text: str,
    contacts: Dict[str, str],
    sections: Dict[str, Any],
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Evaluates formatting, structure, and readability.
    Returns formatting score (0 - 100) and actionable feedback.
    """
    if metadata is None:
        metadata = {}

    word_count = len(resume_text.split())
    checks = []
    deductions = 0
    suggestions = []

    # 1. Contact Information Completeness (20 points)
    contact_score = 0
    if contacts.get("email") and contacts["email"] != "Not detected":
        contact_score += 8
    else:
        suggestions.append("Missing or unparseable email address. Ensure your email is written in plain text.")

    if contacts.get("phone") and contacts["phone"] != "Not detected":
        contact_score += 6
    else:
        suggestions.append("Missing phone number. Include a standard phone format (e.g., +1-555-123-4567).")

    if contacts.get("name") and contacts["name"] != "Not detected":
        contact_score += 6
    else:
        suggestions.append("Candidate name was not clearly identifiable at the top of the resume.")

    checks.append({
        "aspect": "Contact Completeness",
        "score": contact_score,
        "max_score": 20,
        "status": "Good" if contact_score >= 18 else "Needs Attention"
    })

    # 2. Section Headings Presence (25 points)
    # Check key sections: skills, experience, education, projects, summary
    essential_sections = ["experience", "education", "skills"]
    nice_sections = ["summary", "projects"]
    
    sec_score = 0
    found_essential = sum(1 for s in essential_sections if s in sections)
    sec_score += found_essential * 6  # up to 18
    found_nice = sum(1 for s in nice_sections if s in sections)
    sec_score += found_nice * 3.5    # up to 7
    sec_score = min(25.0, round(sec_score, 1))

    missing_core = [s.title() for s in essential_sections if s not in sections]
    if missing_core:
        suggestions.append(f"Missing distinct section headings for: {', '.join(missing_core)}. Use standard headings.")

    checks.append({
        "aspect": "Section Structure",
        "score": sec_score,
        "max_score": 25,
        "status": "Good" if sec_score >= 20 else "Needs Attention"
    })

    # 3. Content Length & Density (20 points)
    length_score = 20
    if word_count < 150:
        length_score = 6
        suggestions.append(f"Resume is very brief ({word_count} words). Aim for 350 - 800 words for adequate detail.")
    elif word_count < 300:
        length_score = 14
        suggestions.append(f"Resume is relatively short ({word_count} words). Consider adding more project details.")
    elif word_count > 2000:
        length_score = 12
        suggestions.append(f"Resume is exceptionally long ({word_count} words). Aim to keep it within 1 - 2 pages.")
    elif word_count > 1200:
        length_score = 17

    checks.append({
        "aspect": "Document Length",
        "score": length_score,
        "max_score": 20,
        "status": "Good" if length_score >= 17 else "Needs Attention"
    })

    # 4. Action Verbs & Bullet Point Usage (20 points)
    # Check for presence of strong active verbs
    lower_words = set(re.findall(r"\b[a-z]{3,}\b", resume_text.lower()))
    found_verbs = lower_words.intersection(ACTION_VERBS)
    
    if len(found_verbs) >= 6:
        verb_score = 20
    elif len(found_verbs) >= 3:
        verb_score = 14
        suggestions.append("Incorporate more strong action verbs (e.g., 'Engineered', 'Optimized', 'Spearheaded').")
    else:
        verb_score = 8
        suggestions.append("Few action verbs detected. Begin experience bullet points with impactful accomplishment verbs.")

    checks.append({
        "aspect": "Action-Oriented Language",
        "score": verb_score,
        "max_score": 20,
        "status": "Good" if verb_score >= 17 else "Needs Attention"
    })

    # 5. Parsing Cleanliness & Repetition (15 points)
    cleanliness_score = 15
    # Check for excessive duplicate lines (potential parsing loop)
    lines = [l.strip() for l in resume_text.split("\n") if len(l.strip()) > 10]
    if lines:
        unique_ratio = len(set(lines)) / len(lines)
        if unique_ratio < 0.65:
            cleanliness_score -= 8
            suggestions.append("Significant repeated text or duplicate lines detected. Check formatting layout.")

    # Check for strange non-ASCII artifacts
    weird_chars = len(re.findall(r"[^\x00-\x7F\u2022\u2013\u2014]", resume_text))
    if weird_chars > 30:
        cleanliness_score -= 4
        suggestions.append("Non-standard symbols or encoding artifacts found. Stick to clean standard UTF-8 characters.")

    cleanliness_score = max(0, cleanliness_score)

    checks.append({
        "aspect": "Text Extraction Cleanliness",
        "score": cleanliness_score,
        "max_score": 15,
        "status": "Good" if cleanliness_score >= 12 else "Needs Attention"
    })

    total_score = contact_score + sec_score + length_score + verb_score + cleanliness_score
    total_score = max(0.0, min(100.0, round(float(total_score), 1)))

    return {
        "score": total_score,
        "word_count": word_count,
        "checks": checks,
        "suggestions": suggestions,
        "found_action_verbs": sorted(list(found_verbs)),
        "explanation": f"Structural formatting scored {total_score}/100 based on contact info, sections, and readability."
    }
