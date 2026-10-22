"""
Job Description Parser Module
Parses job descriptions to extract:
- Job title
- Explicitly required skills vs preferred / bonus skills
- Years of experience requirements
- Education qualifications
- Core responsibilities
- Domain keywords (excluding stop words)
"""

import re
from typing import Dict, List, Set, Any, Optional
from config.skills_dictionary import find_skills_in_text


COMMON_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "will", "job", "work", "role", "team", "company",
    "candidate", "working", "looking", "join", "opportunity", "experience", "years"
}


def extract_job_title(jd_text: str) -> str:
    """
    Attempts to identify the job title from the first few lines or explicit labels.
    """
    lines = [line.strip() for line in jd_text.split("\n") if line.strip()]
    if not lines:
        return "Not specified"

    # Check for explicit labels: "Job Title: ...", "Position: ...", "Role: ..."
    for line in lines[:8]:
        match = re.match(r"^(?:job\s+title|position|role|designation)\s*[:\-]\s*(.+)$", line, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Check the first 2 lines for typical job titles
    common_title_keywords = ["engineer", "developer", "analyst", "manager", "scientist", "architect", "consultant", "specialist", "intern"]
    for line in lines[:3]:
        lower_line = line.lower()
        if any(kw in lower_line for kw in common_title_keywords) and len(line) < 60:
            return line

    return lines[0][:60] if lines else "Not specified"


def extract_experience_requirement(jd_text: str) -> Dict[str, Any]:
    """
    Extracts required years of experience mentioned in the job description.
    """
    patterns = [
        # "3+ years", "3-5 years", "3 to 5 years", "at least 3 years"
        r"(?:at\s+least\s+)?(\d+)(?:\s*(?:-|to|\+)\s*(\d+))?\s*\+?\s*years?(?:\s+of)?\s+(?:relevant\s+|professional\s+|work\s+)?experience",
        r"(\d+)\+\s*years?(?:\s+of)?\s+experience"
    ]

    min_years = 0
    max_years = 0
    extracted_phrases = []

    for pat in patterns:
        matches = re.finditer(pat, jd_text, re.IGNORECASE)
        for match in matches:
            phrase = match.group(0).strip()
            extracted_phrases.append(phrase)
            val1 = int(match.group(1)) if match.group(1) else 0
            val2 = int(match.group(2)) if len(match.groups()) > 1 and match.group(2) else val1
            if val1 > min_years:
                min_years = val1
                max_years = max(val1, val2)

    return {
        "min_years": min_years,
        "max_years": max_years,
        "raw_mentions": list(set(extracted_phrases)),
        "summary": f"{min_years}+ years" if min_years > 0 else "Not explicitly specified"
    }


def extract_education_requirement(jd_text: str) -> Dict[str, Any]:
    """
    Extracts degree requirements like Bachelor's, Master's, PhD.
    """
    degrees_found = []
    
    if re.search(r"\b(?:Ph\.?D\.?|Doctorate)\b", jd_text, re.IGNORECASE):
        degrees_found.append("PhD / Doctorate")
    if re.search(r"\b(?:Master'?s?|M\.?S|M\.?Tech|MCA|MBA)\b", jd_text, re.IGNORECASE):
        degrees_found.append("Master's Degree")
    if re.search(r"\b(?:Bachelor'?s?|B\.?S|B\.?Tech|B\.?E|BCA)\b", jd_text, re.IGNORECASE):
        degrees_found.append("Bachelor's Degree")
    if re.search(r"\b(?:High\s+School|Diploma|Associate)\b", jd_text, re.IGNORECASE):
        degrees_found.append("Diploma / Associate")

    return {
        "required_degrees": degrees_found if degrees_found else ["Degree not strictly specified"],
        "has_strict_requirement": len(degrees_found) > 0
    }


def extract_keywords_from_jd(jd_text: str, top_n: int = 25) -> List[str]:
    """
    Extracts high-importance domain terms and keywords from the JD text deterministically.
    Avoids duplicate counting, strips trailing punctuation, and filters non-words.
    """
    # Tokenize words, length >= 3
    words = re.findall(r"\b[A-Za-z][A-Za-z0-9+#.-]{1,24}\b", jd_text.lower())
    freq: Dict[str, int] = {}
    for raw_w in words:
        w = raw_w.rstrip(".-")
        if w not in COMMON_STOPWORDS and not w.isdigit() and len(w) > 2:
            freq[w] = freq.get(w, 0) + 1

    # Deterministic sort: highest frequency first, alphabetized secondary key for ties
    sorted_keywords = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [k for k, _ in sorted_keywords[:top_n]]


def parse_job_description(jd_text: str) -> Dict[str, Any]:
    """
    Main job description parser that identifies requirements, preferred skills,
    experience, education, and keywords.
    """
    if not jd_text or not jd_text.strip():
        return {
            "success": False,
            "error": "Job description is empty. Please paste a job description or upload a file.",
            "job_title": "Not specified",
            "required_skills": [],
            "preferred_skills": [],
            "all_skills": [],
            "experience": {"min_years": 0, "summary": "Not specified"},
            "education": {"required_degrees": []},
            "keywords": []
        }

    cleaned_jd = jd_text.strip()
    job_title = extract_job_title(cleaned_jd)
    experience_req = extract_experience_requirement(cleaned_jd)
    education_req = extract_education_requirement(cleaned_jd)
    keywords = extract_keywords_from_jd(cleaned_jd)

    # Split text into Required vs Preferred blocks if present
    lines = cleaned_jd.split("\n")
    required_text_parts = []
    preferred_text_parts = []
    general_text_parts = []

    current_mode = "general"

    preferred_headers = [
        "preferred", "nice to have", "good to have", "plus", "bonus", "desirable", "desired qualifications"
    ]
    required_headers = [
        "requirements", "required qualifications", "what you need", "minimum qualifications",
        "must have", "essential", "basic qualifications", "prerequisites"
    ]

    for line in lines:
        lower_line = line.strip().lower()
        if not lower_line:
            continue

        # Check for section header transitions
        if any(h in lower_line for h in preferred_headers) and len(lower_line) < 45:
            current_mode = "preferred"
            continue
        elif any(h in lower_line for h in required_headers) and len(lower_line) < 45:
            current_mode = "required"
            continue
        elif any(h in lower_line for h in ["responsibilities", "about us", "benefits", "about the role"]) and len(lower_line) < 45:
            current_mode = "general"
            continue

        if current_mode == "preferred":
            preferred_text_parts.append(line)
        elif current_mode == "required":
            required_text_parts.append(line)
        else:
            general_text_parts.append(line)

    preferred_text = "\n".join(preferred_text_parts)
    required_text = "\n".join(required_text_parts)

    all_detected_skills = find_skills_in_text(cleaned_jd)

    # Separate into Required and Preferred skills
    required_skills = set()
    preferred_skills = set()

    if preferred_text:
        pref_detected = find_skills_in_text(preferred_text)
        preferred_skills.update(pref_detected.keys())

    if required_text:
        req_detected = find_skills_in_text(required_text)
        required_skills.update(req_detected.keys())

    # Distribute any remaining detected skills
    for skill in all_detected_skills:
        if skill not in preferred_skills and skill not in required_skills:
            # If no explicit sections were found, default detected skills to required
            if not required_text and not preferred_text:
                required_skills.add(skill)
            else:
                required_skills.add(skill)

    # Avoid overlap (if marked as both, keep in required)
    preferred_skills = preferred_skills - required_skills

    return {
        "success": True,
        "error": None,
        "job_title": job_title,
        "required_skills": sorted(list(required_skills)),
        "preferred_skills": sorted(list(preferred_skills)),
        "all_skills": sorted(list(all_detected_skills.keys())),
        "experience": experience_req,
        "education": education_req,
        "keywords": keywords,
        "word_count": len(cleaned_jd.split())
    }
