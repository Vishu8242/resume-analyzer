"""
Resume Information Extractor Module
Extracts personal contact details, education, experience, projects,
certifications, skills, and section blocks using robust regex and rule-based NLP.
Never fabricates information: missing fields default to 'Not detected'.
"""

import re
from typing import Dict, List, Any, Optional
from config.skills_dictionary import find_skills_in_text


# Regex patterns for contact information
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Phone numbers (handles international, parens, hyphens, spaces)
PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,5}[\s.-]?\d{3,5}\b"
)

# Social / Professional URLs
LINKEDIN_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/(?:in|pub)\/([A-Za-z0-9_-]+)\/?",
    re.IGNORECASE
)
GITHUB_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?github\.com\/([A-Za-z0-9_-]+)\/?",
    re.IGNORECASE
)
PORTFOLIO_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9.-]+\.(?:com|org|net|io|dev|me|tech|app|ai)(?:\/[^\s]*)?)",
    re.IGNORECASE
)

# Section Headers Definition
SECTION_PATTERNS = {
    "summary": [
        r"^(?:professional\s+)?summary",
        r"^about\s+me",
        r"^(?:career\s+)?objective",
        r"^profile",
        r"^executive\s+summary",
        r"^overview"
    ],
    "skills": [
        r"^(?:technical\s+|core\s+)?skills",
        r"^technologies",
        r"^technical\s+proficiencies",
        r"^competencies",
        r"^tools\s+(?:&|and)\s+technologies",
        r"^areas\s+of\s+expertise"
    ],
    "experience": [
        r"^(?:work\s+|professional\s+|employment\s+)?experience",
        r"^work\s+history",
        r"^employment\s+history",
        r"^career\s+history"
    ],
    "internships": [
        r"^internships?",
        r"^internship\s+experience",
        r"^industrial\s+training"
    ],
    "education": [
        r"^education(?:al\s+background)?",
        r"^academic\s+(?:background|qualifications|history)",
        r"^qualifications",
        r"^degrees?"
    ],
    "projects": [
        r"^(?:key\s+|personal\s+|academic\s+)?projects?",
        r"^selected\s+projects?",
        r"^portfolio\s+projects?"
    ],
    "certifications": [
        r"^certifications?",
        r"^licenses?\s+(?:&|and)\s+certifications?",
        r"^courses?\s+(?:&|and)\s+certifications?",
        r"^accreditations?"
    ],
    "achievements": [
        r"^achievements?",
        r"^honors?\s+(?:&|and)\s+awards?",
        r"^accomplishments?",
        r"^awards?"
    ]
}


def extract_contact_info(text: str) -> Dict[str, str]:
    """
    Extracts name, email, phone, LinkedIn, GitHub, and portfolio URLs.
    """
    contacts = {
        "name": "Not detected",
        "email": "Not detected",
        "phone": "Not detected",
        "linkedin": "Not detected",
        "github": "Not detected",
        "portfolio": "Not detected"
    }

    if not text:
        return contacts

    # 1. Email extraction
    email_matches = EMAIL_REGEX.findall(text)
    if email_matches:
        contacts["email"] = email_matches[0].strip()

    # 2. Phone extraction
    phone_matches = PHONE_REGEX.findall(text)
    valid_phones = []
    for p in phone_matches:
        # Strip punctuation to count digits
        digits = re.sub(r"\D", "", p)
        if 8 <= len(digits) <= 15:
            valid_phones.append(p.strip())
    if valid_phones:
        contacts["phone"] = valid_phones[0]

    # 3. LinkedIn
    linkedin_matches = LINKEDIN_REGEX.findall(text)
    if linkedin_matches:
        contacts["linkedin"] = f"https://linkedin.com/in/{linkedin_matches[0]}"

    # 4. GitHub
    github_matches = GITHUB_REGEX.findall(text)
    excluded_github_usernames = {"features", "pricing", "explore", "topics", "trending", "about"}
    for user in github_matches:
        if user.lower() not in excluded_github_usernames:
            contacts["github"] = f"https://github.com/{user}"
            break

    # 5. Portfolio / Personal Site
    # Remove email addresses and other social links from text before matching generic portfolio URLs
    text_without_emails = EMAIL_REGEX.sub(" ", text)
    portfolio_matches = PORTFOLIO_REGEX.findall(text_without_emails)
    excluded_domains = {
        "linkedin.com", "github.com", "gmail.com", "yahoo.com", "outlook.com",
        "hotmail.com", "icloud.com", "proton.me", "protonmail.com", "mail.com",
        "email.com", "techmail.com", "example.com"
    }
    for site in portfolio_matches:
        site_str = str(site).strip()
        lower_site = site_str.lower()
        if (
            not any(dom in lower_site for dom in excluded_domains)
            and not lower_site.endswith(".pdf")
            and not lower_site.endswith(".docx")
            and not lower_site.endswith(".png")
            and not lower_site.endswith(".jpg")
        ):
            if not site_str.startswith("http"):
                site_str = "https://" + site_str
            contacts["portfolio"] = site_str
            break

    # 6. Name extraction heuristic
    # Candidate name is almost always at the very top (first 3-5 lines),
    # consisting of 2 to 4 capitalized words without digits, symbols, or common section keywords.
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    candidate_name = None
    blacklist_words = {
        "resume", "cv", "curriculum", "vitae", "profile", "contact",
        "page", "summary", "engineer", "developer", "student", "phone",
        "email", "address", "linkedin", "github", "portfolio"
    }

    for line in lines[:5]:
        # Skip if contains email or url or phone
        if "@" in line or "http" in line or "www." in line or re.search(r"\d", line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4:
            # Check if all words are alphabetic and capitalized
            if all(w.replace(".", "").isalpha() and w[0].isupper() for w in words):
                lower_words = {w.lower() for w in words}
                if not lower_words.intersection(blacklist_words):
                    candidate_name = line
                    break

    if candidate_name:
        contacts["name"] = candidate_name

    return contacts


def segment_resume_sections(text: str) -> Dict[str, str]:
    """
    Splits resume into identified sections based on common headings.
    """
    if not text:
        return {}

    lines = text.split("\n")
    sections: Dict[str, List[str]] = {}
    current_section = "header"
    sections[current_section] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if line matches any section header pattern
        detected_sec = None
        # Usually headers are short (< 40 chars, <= 4 words)
        if len(stripped) <= 45 and len(stripped.split()) <= 4:
            clean_heading = re.sub(r"[:\-_|]", "", stripped).strip().lower()
            for sec_name, patterns in SECTION_PATTERNS.items():
                for pat in patterns:
                    if re.match(pat, clean_heading, re.IGNORECASE):
                        detected_sec = sec_name
                        break
                if detected_sec:
                    break

        if detected_sec:
            current_section = detected_sec
            if current_section not in sections:
                sections[current_section] = []
        else:
            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].append(stripped)

    # Convert list of lines to joined string
    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


def extract_education_details(text: str, education_section: str = "") -> List[str]:
    """
    Extracts degrees, university names, and education entries.
    """
    source_text = education_section if education_section else text
    if not source_text:
        return []

    degree_patterns = [
        r"\b(?:B\.?Tech|B\.?E\.?|Bachelor\s+(?:of\s+)?(?:Science|Engineering|Technology|Arts|Commerce|Business|Computer\s+Applications))\b[^\n,]*",
        r"\b(?:M\.?Tech|M\.?E\.?|Master\s+(?:of\s+)?(?:Science|Engineering|Technology|Arts|Commerce|Business\s+Administration|Computer\s+Applications))\b[^\n,]*",
        r"\b(?:B\.?S\.?c?|M\.?S\.?c?|BCA|MCA|BBA|MBA|Ph\.?D\.?|Doctorate)\b[^\n,]*",
        r"\b(?:Associate\s+Degree|High\s+School|Diploma)\b[^\n,]*"
    ]

    entries = []
    lines = source_text.split("\n")
    for line in lines:
        for pat in degree_patterns:
            matches = re.findall(pat, line, re.IGNORECASE)
            for m in matches:
                clean_m = m.strip()
                if clean_m and clean_m not in entries:
                    entries.append(clean_m)

    return entries


def extract_resume_information(raw_text: str) -> Dict[str, Any]:
    """
    Main extraction function returning structured information from resume text.
    """
    if not raw_text:
        return {
            "personal_info": {
                "name": "Not detected",
                "email": "Not detected",
                "phone": "Not detected",
                "linkedin": "Not detected",
                "github": "Not detected",
                "portfolio": "Not detected"
            },
            "summary": "Not detected",
            "skills": {},
            "technical_skills": [],
            "soft_skills": [],
            "education": [],
            "work_experience": "Not detected",
            "internships": "Not detected",
            "projects": "Not detected",
            "certifications": "Not detected",
            "achievements": "Not detected"
        }

    # 1. Contact Information
    contacts = extract_contact_info(raw_text)

    # 2. Section Segmentation
    sections = segment_resume_sections(raw_text)

    # 3. Skills Detection using Taxonomy
    skills_detected = find_skills_in_text(raw_text)
    tech_skills = [
        s for s, data in skills_detected.items()
        if data["category"] not in ("Soft Skills", "Methodologies")
    ]
    soft_skills = [
        s for s, data in skills_detected.items()
        if data["category"] in ("Soft Skills", "Methodologies")
    ]

    # 4. Education Extraction
    edu_text = sections.get("education", "")
    education_list = extract_education_details(raw_text, edu_text)

    # 5. Build final information bundle
    return {
        "personal_info": contacts,
        "summary": sections.get("summary", "Not detected") if sections.get("summary") else "Not detected",
        "skills": skills_detected,
        "technical_skills": sorted(tech_skills),
        "soft_skills": sorted(soft_skills),
        "education": education_list if education_list else ["Not detected"],
        "work_experience": sections.get("experience", "Not detected") if sections.get("experience") else "Not detected",
        "internships": sections.get("internships", "Not detected") if sections.get("internships") else "Not detected",
        "projects": sections.get("projects", "Not detected") if sections.get("projects") else "Not detected",
        "certifications": sections.get("certifications", "Not detected") if sections.get("certifications") else "Not detected",
        "achievements": sections.get("achievements", "Not detected") if sections.get("achievements") else "Not detected",
        "raw_sections": sections
    }
