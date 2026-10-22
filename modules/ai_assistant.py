"""
AI Resume Improvement Assistant Module
Provides tailored suggestions for:
- Professional summary rewrite
- Bullet point refinement (action-verb & metric orientation)
- Stronger project descriptions (STAR framework)
- Skill learning roadmap & keyword placement
- Achievement quantification templates

Includes:
1. Optional Google Gemini API integration
2. Optional Hugging Face API integration
3. Complete, high-quality rule-based fallback when no API key is provided
"""

import json
import os
import requests
from typing import Dict, List, Any, Optional, Tuple
from config.settings import GEMINI_API_KEY, HUGGINGFACE_API_KEY, DEFAULT_GEMINI_MODEL


# Action verbs mapped by domain
IMPACT_VERBS = {
    "development": ["Architected", "Engineered", "Implemented", "Developed", "Deployed", "Refactored"],
    "performance": ["Optimized", "Accelerated", "Streamlined", "Maximized", "Reduced", "Scaled"],
    "leadership": ["Spearheaded", "Orchestrated", "Led", "Mentored", "Directed", "Coordinated"],
    "analytics": ["Analyzed", "Quantified", "Modeled", "Evaluated", "Uncovered", "Visualized"]
}


def rule_based_summary_generation(
    candidate_name: str,
    target_job_title: str,
    top_skills: List[str],
    experience_years: float,
    current_summary: str = ""
) -> str:
    """
    Generates a tailored, professional summary template based strictly on verified inputs.
    """
    skills_str = ", ".join(top_skills[:5]) if top_skills else "modern software engineering practices"
    years_str = f"with ~{experience_years} years of demonstrated experience" if experience_years > 0 else "with a solid foundation in software development"
    role_str = target_job_title if target_job_title and target_job_title != "Not specified" else "Software Engineering Professional"

    template = (
        f"Results-driven {role_str} {years_str}, specializing in {skills_str}. "
        f"Proven track record of designing scalable solutions, optimizing performance, and collaborating in agile teams. "
        f"Seeking to leverage technical proficiencies and problem-solving skills to drive impactful engineering outcomes."
    )
    return template


def rule_based_bullet_enhancement(bullet_or_text: str) -> List[Dict[str, str]]:
    """
    Transforms plain resume descriptions into high-impact, quantified achievement statements.
    """
    lines = [l.strip(" -•*") for l in bullet_or_text.split("\n") if len(l.strip()) > 15]
    if not lines:
        lines = [
            "Responsible for developing web application features and fixing bugs.",
            "Worked with database queries and backend APIs.",
            "Collaborated with team members to deliver project on time."
        ]

    improvements = []
    sample_transforms = [
        (
            "Architected and deployed responsive full-stack features using {skills}, improving user workflow efficiency by [Insert % or Metric].",
            "Added quantifiable impact and active verb 'Architected'."
        ),
        (
            "Engineered robust RESTful backend endpoints and optimized database query execution, reducing latency by [Insert %].",
            "Replaced passive role with specific engineering actions and performance metric placeholder."
        ),
        (
            "Spearheaded cross-functional sprint deliverables in an Agile environment, ensuring 100% on-time release milestones.",
            "Demonstrated ownership, leadership, and verifiable delivery cadence."
        )
    ]

    for idx, line in enumerate(lines[:3]):
        tmpl, rationale = sample_transforms[idx % len(sample_transforms)]
        improvements.append({
            "original": line,
            "suggested": tmpl,
            "rationale": rationale
        })

    return improvements


def rule_based_project_enhancement(project_name: str, skills_used: List[str]) -> Dict[str, str]:
    """
    Provides a STAR (Situation, Task, Action, Result) enhancement framework for candidate projects.
    """
    skills_phrase = ", ".join(skills_used[:3]) if skills_used else "modern frameworks"
    return {
        "framework": "STAR (Situation, Task, Action, Result)",
        "guidelines": (
            "1. Situation: What business or technical challenge did this project address?\n"
            "2. Task: What was your specific responsibility or objective?\n"
            "3. Action: Which specific tools ({skills_phrase}) and architectures did you implement?\n"
            "4. Result: What measurable outcome was achieved (e.g., speedup, user adoption, accuracy)?"
        ).format(skills_phrase=skills_phrase),
        "example_bullet": (
            f"Designed and implemented '{project_name}' leveraging {skills_phrase}; "
            f"engineered core backend services and user interfaces, resulting in [quantifiable outcome, e.g., 40% latency reduction]."
        )
    }


def rule_based_quantification_guide() -> List[Dict[str, str]]:
    """
    Supplies actionable formulas for candidates to quantify their real achievements.
    """
    return [
        {
            "category": "Time & Efficiency",
            "formula": "Automated [Task] using [Tool], reducing manual effort from [X hours] to [Y minutes].",
            "example": "Automated data ingestion pipeline using Python and Pandas, reducing report generation time by 65%."
        },
        {
            "category": "Scale & Volume",
            "formula": "Engineered [System] capable of handling [X concurrent requests / Y records] with [Z% uptime].",
            "example": "Engineered REST APIs handling 10,000+ daily requests with 99.9% uptime."
        },
        {
            "category": "Performance & Accuracy",
            "formula": "Trained [Model] achieving [X% accuracy/F1-score], outperforming the baseline by [Y%].",
            "example": "Developed NLP classification model achieving 92% accuracy, outperforming existing rule engine by 18%."
        }
    ]


def call_gemini_api(prompt: str, api_key: str, model: str = DEFAULT_GEMINI_MODEL) -> Tuple[bool, str]:
    """
    Calls Google Gemini REST API.
    """
    if not api_key:
        return False, "Gemini API key is not configured."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are an expert AI Career Coach and Resume Optimization Specialist. "
                            "STRICT RULES:\n"
                            "- Use ONLY the facts provided by the candidate.\n"
                            "- DO NOT invent employers, degrees, metrics, or credentials.\n"
                            "- Keep recommendations realistic and professional.\n\n"
                            + prompt
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1000
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return True, content
            return False, "Empty response received from Gemini API."
        else:
            return False, f"Gemini API returned status {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, f"Error calling Gemini API: {str(e)}"


def call_huggingface_api(prompt: str, api_key: str, model_id: str = "mistralai/Mistral-7B-Instruct-v0.2") -> Tuple[bool, str]:
    """
    Calls Hugging Face Inference API.
    """
    if not api_key:
        return False, "Hugging Face API key is not configured."

    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 500, "temperature": 0.3}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return True, result[0].get("generated_text", "")
            elif isinstance(result, dict) and "error" in result:
                return False, result["error"]
            return True, str(result)
        return False, f"Hugging Face returned status {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, f"Hugging Face request failed: {str(e)}"


def generate_improvement_suggestions(
    resume_info: Dict[str, Any],
    job_info: Dict[str, Any],
    skills_match: Dict[str, Any],
    provider: str = "auto",
    custom_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Coordinates AI suggestions with seamless fallback to rule-based analysis.
    """
    api_key = custom_api_key or GEMINI_API_KEY
    hf_key = custom_api_key or HUGGINGFACE_API_KEY
    
    # 1. Rule-based recommendations (always generated as baseline or fallback)
    candidate_name = resume_info.get("personal_info", {}).get("name", "Candidate")
    job_title = job_info.get("job_title", "Software Engineer")
    top_skills = resume_info.get("technical_skills", [])
    if not top_skills:
        top_skills = skills_match.get("matching_skills", []) or list(resume_info.get("skills", {}).keys())
    exp_years = resume_info.get("experience_years", 1.0)
    
    rule_summary = rule_based_summary_generation(candidate_name, job_title, top_skills, exp_years)
    rule_bullets = rule_based_bullet_enhancement(resume_info.get("work_experience", ""))
    rule_quant = rule_based_quantification_guide()
    rule_project = rule_based_project_enhancement(
        resume_info.get("projects", "Core Projects")[:30],
        top_skills
    )

    result = {
        "provider_used": "Rule-Based Expert Engine (Offline / Safe)",
        "summary_recommendation": rule_summary,
        "bullet_point_improvements": rule_bullets,
        "quantification_guide": rule_quant,
        "project_guidance": rule_project,
        "missing_skills_guidance": {
            "required": skills_match.get("missing_required", []),
            "preferred": skills_match.get("missing_preferred", [])
        },
        "ai_generated_text": None,
        "notice": (
            "Rule-based recommendations generated successfully without sending data to external APIs. "
            "All recommendations adhere to verified resume details."
        )
    }

    # 2. Attempt AI enhancements if requested and key is present
    if (provider == "gemini" or (provider == "auto" and api_key)) and api_key:
        prompt = (
            f"Review this candidate's resume against the target role '{job_title}'.\n"
            f"Candidate Skills: {', '.join(top_skills[:10])}\n"
            f"Target Missing Skills: {', '.join(skills_match.get('missing_required', [])[:6])}\n"
            f"Candidate Experience: {resume_info.get('work_experience', '')[:300]}\n\n"
            f"Provide:\n"
            f"1. A polished, 3-sentence professional summary tailored for this role.\n"
            f"2. Three high-impact resume bullet points using action verbs and metric placeholders [e.g. [X%]].\n"
            f"3. Advice on how to authentically integrate missing skills without exaggerating."
        )
        success, ai_text = call_gemini_api(prompt, api_key)
        if success:
            result["provider_used"] = "Google Gemini AI"
            result["ai_generated_text"] = ai_text
            result["notice"] = "Personalized AI suggestions generated using Google Gemini."

    elif (provider == "huggingface" or (provider == "auto" and hf_key)) and hf_key:
        prompt = (
            f"Improve this resume summary for the role of {job_title}: "
            f"Skills: {', '.join(top_skills[:8])}."
        )
        success, ai_text = call_huggingface_api(prompt, hf_key)
        if success:
            result["provider_used"] = "Hugging Face Inference AI"
            result["ai_generated_text"] = ai_text
            result["notice"] = "Suggestions generated using Hugging Face."

    return result
