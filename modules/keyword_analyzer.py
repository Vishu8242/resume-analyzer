"""
Keyword Analyzer Module
Extracts domain-relevant keywords from the job description and evaluates their
coverage in the resume text.
Avoids counting repeated words, excludes stop words, handles special symbols (C++, C#, .NET),
prevents false substring matches, and leverages deterministic TF-IDF similarity.
"""

import re
from typing import Dict, List, Any, Set

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def build_keyword_pattern(kw: str) -> re.Pattern:
    """
    Builds a boundary-safe regular expression pattern for a keyword.
    Correctly handles:
    - Special programming language symbols: C++, C#, .NET, Node.js
    - Substring false positives: Java inside JavaScript, SQL inside NoSQL, Go inside Good, C inside Cat
    """
    kw_clean = kw.strip()
    kw_lower = kw_clean.lower()

    # Specialized patterns for single-letter or ambiguous short terms
    if kw_lower == "c":
        # Match 'C' when used as a programming language (e.g. "C and Python", "C, C++", "C programming", "ANSI C")
        # and NOT inside words (Cat, React) or arbitrary initials (Vitamin C, Section C)
        return re.compile(
            r"(?:\b[Cc]\b(?=\s*(?:and|,)\s*(?:Python|Java|C\+\+|Rust|Go|C\#|Ruby|Linux|Git|SQL)\b))|"
            r"(?:\b(?:c\s+programming|c\s+language|ansi\s+c)\b)|"
            r"(?:\bC\/(?:C\+\+|Embedded)\b)|"
            r"(?:(?<![a-zA-Z0-9])C(?=\s*,\s*(?:C\+\+|Java|Python)))",
            re.IGNORECASE
        )
    if kw_lower == "r":
        # Match 'R' when referring to the statistical programming language
        return re.compile(
            r"(?:\b(?:r\s*(?:programming|language|studio)|rstudio|r-project)\b)|"
            r"(?:\b[Rr]\b(?=\s*(?:and|,)\s*(?:Python|SQL|Pandas|Stats|Data|Machine|MATLAB)\b))",
            re.IGNORECASE
        )
    if kw_lower == "go":
        # Match 'Go' as language (golang, go language, or go programming, not 'good', 'going')
        return re.compile(
            r"(?:\bgolang\b)|(?:\bGo\s+(?:language|programming|developer|code)\b)|"
            r"(?:\bGo\b(?=\s*(?:and|,)\s*(?:Python|Rust|Java|Docker|Kubernetes)\b))",
            re.IGNORECASE
        )

    escaped = re.escape(kw_lower)

    # Prefix boundary
    if kw_clean[0].isalnum():
        prefix = r"(?<![a-zA-Z0-9])"
    else:
        # For keywords starting with punctuation like .NET
        prefix = r"(?<!\S)"

    # Suffix boundary
    if kw_clean[-1].isalnum():
        suffix = r"(?![a-zA-Z0-9+#])"
    else:
        # For keywords ending with +, #, etc. (C++, C#)
        suffix = r"(?![a-zA-Z0-9])"

    return re.compile(prefix + escaped + suffix, re.IGNORECASE)


def calculate_tfidf_similarity(resume_text: str, jd_text: str) -> float:
    """
    Computes deterministic cosine similarity between resume and JD using TF-IDF.
    Returns score between 0.0 and 1.0 rounded to 4 decimals.
    """
    if not SKLEARN_AVAILABLE or not resume_text or not jd_text:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=500,
            ngram_range=(1, 2),
            norm="l2"
        )
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(float(sim), 4)
    except Exception:
        return 0.0


def deduplicate_keywords(keywords: List[str]) -> List[str]:
    """
    Deduplicates a list of keywords case-insensitively while preserving original order
    and clean canonical casing. Avoids inflating scores with duplicate keywords.
    """
    seen: Set[str] = set()
    unique_list: List[str] = []
    for kw in keywords:
        if not kw:
            continue
        clean_kw = kw.strip()
        lower_kw = clean_kw.lower()
        if lower_kw and lower_kw not in seen:
            seen.add(lower_kw)
            unique_list.append(clean_kw)
    return unique_list


def evaluate_keywords(
    resume_text: str,
    jd_keywords: List[str],
    jd_text: str = ""
) -> Dict[str, Any]:
    """
    Evaluates keyword presence and contextual similarity deterministically.
    - Strictly deduplicates input JD keywords to eliminate duplicate counting.
    - Counts each unique target keyword once (binary coverage) regardless of resume repetitions.
    - Prevents false substring matches (e.g. Java in JavaScript, SQL in NoSQL).
    - Normalizes keyword score to [0.0, 100.0].
    """
    # 1. Strictly deduplicate target keywords
    unique_jd_keywords = deduplicate_keywords(jd_keywords)

    if not unique_jd_keywords:
        return {
            "score": 100.0,
            "matching_keywords": [],
            "missing_keywords": [],
            "match_ratio": 1.0,
            "semantic_similarity": 0.0,
            "explanation": "No specific domain keywords were extracted from the job description."
        }

    matching_keywords = []
    missing_keywords = []

    # 2. Check each unique keyword with boundary-safe matcher
    for kw in unique_jd_keywords:
        pattern = build_keyword_pattern(kw)
        if pattern.search(resume_text):
            matching_keywords.append(kw)
        else:
            missing_keywords.append(kw)

    total_unique_kw = len(unique_jd_keywords)
    match_ratio = len(matching_keywords) / total_unique_kw if total_unique_kw > 0 else 1.0

    # 3. Deterministic TF-IDF cosine similarity (if available)
    sim = calculate_tfidf_similarity(resume_text, jd_text) if jd_text else 0.0

    # 4. Deterministic score formulation: 80% unique keyword coverage + 20% TF-IDF alignment
    if SKLEARN_AVAILABLE and sim > 0:
        raw_score = (match_ratio * 0.80 + sim * 0.20) * 100.0
    else:
        raw_score = match_ratio * 100.0

    # Clamp strictly between 0.0 and 100.0
    score = max(0.0, min(100.0, round(raw_score, 1)))

    explanation = (
        f"Resume matches {len(matching_keywords)} of {total_unique_kw} unique target keywords "
        f"({match_ratio * 100:.1f}% coverage)."
    )
    if sim > 0:
        explanation += f" Contextual TF-IDF alignment: {sim * 100:.1f}%."

    return {
        "score": score,
        "matching_keywords": matching_keywords,
        "missing_keywords": missing_keywords,
        "match_ratio": round(match_ratio, 4),
        "semantic_similarity": round(sim, 4),
        "total_unique_keywords": total_unique_kw,
        "explanation": explanation
    }
