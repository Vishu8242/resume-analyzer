"""
Configurable Skills Dictionary and Aliases Mapping
AI Resume Analyzer and ATS Score Checker
"""

import re
from typing import Dict, List, Set, Tuple

# Comprehensive Technical Skills Categorized Dictionary
# Canonical name -> { "category": str, "aliases": List[str], "regex": Optional[str] }
SKILLS_TAXONOMY: Dict[str, Dict] = {
    # --- Programming Languages ---
    "Python": {
        "category": "Programming Languages",
        "aliases": ["py", "python3", "python 3", "python2"]
    },
    "Java": {
        "category": "Programming Languages",
        "aliases": ["core java", "java 8", "java 11", "java 17", "java 21"]
    },
    "C": {
        "category": "Programming Languages",
        "aliases": ["c language", "ansi c"],
        # Strict boundary to avoid matching grade 'C' or standalone letters in addresses
        "pattern": r"\b[Cc]\b(?!\s*[\+\#])"
    },
    "C++": {
        "category": "Programming Languages",
        "aliases": ["cpp", "c plus plus", "c/c++"],
        "pattern": r"\bC\+\+\b|\bcpp\b|\bc plus plus\b"
    },
    "C#": {
        "category": "Programming Languages",
        "aliases": ["c sharp", "csharp", "c#.net"],
        "pattern": r"\bC\#\b|\bc sharp\b|\bcsharp\b"
    },
    "JavaScript": {
        "category": "Programming Languages",
        "aliases": ["js", "javascript", "ecmascript", "es6", "es6+"]
    },
    "TypeScript": {
        "category": "Programming Languages",
        "aliases": ["ts", "typescript"]
    },
    "R": {
        "category": "Programming Languages",
        "aliases": ["r programming", "r language"],
        "pattern": r"\bR\s*(?:programming|language|studio)?\b(?<!\w)"
    },
    "Go": {
        "category": "Programming Languages",
        "aliases": ["golang", "go language"],
        "pattern": r"\bgolang\b|\bGo\s+language\b|\bGo\s+programming\b"
    },
    "Rust": {
        "category": "Programming Languages",
        "aliases": ["rust-lang", "rustlang"]
    },
    "PHP": {
        "category": "Programming Languages",
        "aliases": ["php7", "php8"]
    },
    "Ruby": {
        "category": "Programming Languages",
        "aliases": ["ruby on rails", "rails", "ror"]
    },
    "Swift": {
        "category": "Programming Languages",
        "aliases": ["swiftui"]
    },
    "Kotlin": {
        "category": "Programming Languages",
        "aliases": ["kotlin/android"]
    },
    "Dart": {
        "category": "Programming Languages",
        "aliases": ["dart language"]
    },
    "SQL": {
        "category": "Programming Languages",
        "aliases": ["structured query language", "t-sql", "pl/sql", "plsql"]
    },

    # --- Frontend Development ---
    "HTML": {
        "category": "Frontend",
        "aliases": ["html5", "html 5", "xhtml"]
    },
    "CSS": {
        "category": "Frontend",
        "aliases": ["css3", "css 3", "cascading style sheets"]
    },
    "React": {
        "category": "Frontend",
        "aliases": ["reactjs", "react.js", "react js", "react native"]
    },
    "Angular": {
        "category": "Frontend",
        "aliases": ["angularjs", "angular.js", "angular 2+", "angular 14", "angular 15"]
    },
    "Vue.js": {
        "category": "Frontend",
        "aliases": ["vue", "vuejs", "vue 3", "vue 2"]
    },
    "Next.js": {
        "category": "Frontend",
        "aliases": ["nextjs", "next js"]
    },
    "Tailwind CSS": {
        "category": "Frontend",
        "aliases": ["tailwind", "tailwindcss"]
    },
    "Bootstrap": {
        "category": "Frontend",
        "aliases": ["bootstrap 4", "bootstrap 5"]
    },
    "Sass": {
        "category": "Frontend",
        "aliases": ["scss", "sass/scss"]
    },
    "Redux": {
        "category": "Frontend",
        "aliases": ["redux toolkit", "rtk", "redux-saga"]
    },
    "jQuery": {
        "category": "Frontend",
        "aliases": ["jquery"]
    },

    # --- Backend Development ---
    "Node.js": {
        "category": "Backend",
        "aliases": ["nodejs", "node js", "node"]
    },
    "Express.js": {
        "category": "Backend",
        "aliases": ["express", "expressjs", "express js"]
    },
    "Django": {
        "category": "Backend",
        "aliases": ["django rest framework", "drf"]
    },
    "Flask": {
        "category": "Backend",
        "aliases": ["flask framework"]
    },
    "FastAPI": {
        "category": "Backend",
        "aliases": ["fast-api", "fast api"]
    },
    "Spring Boot": {
        "category": "Backend",
        "aliases": ["spring", "springboot", "spring framework", "spring mvc"]
    },
    ".NET": {
        "category": "Backend",
        "aliases": [".net core", "asp.net", "asp.net core", "dotnet"],
        "pattern": r"\.NET(?:\s*Core)?\b|\bdotnet\b|\bASP\.NET\b"
    },
    "REST API": {
        "category": "Backend",
        "aliases": ["restful api", "rest", "restful apis", "rest web services", "restful"]
    },
    "GraphQL": {
        "category": "Backend",
        "aliases": ["apollo graphql", "graphql api"]
    },
    "Microservices": {
        "category": "Backend",
        "aliases": ["microservice architecture", "micro-services", "micro service"]
    },

    # --- Databases ---
    "MySQL": {
        "category": "Databases",
        "aliases": ["my-sql", "mariadb"]
    },
    "PostgreSQL": {
        "category": "Databases",
        "aliases": ["postgres", "postgresql", "psql"]
    },
    "MongoDB": {
        "category": "Databases",
        "aliases": ["mongo", "mongodb atlas"]
    },
    "SQLite": {
        "category": "Databases",
        "aliases": ["sqlite3"]
    },
    "Redis": {
        "category": "Databases",
        "aliases": ["redis cache"]
    },
    "Oracle Database": {
        "category": "Databases",
        "aliases": ["oracle db", "oracle sql"]
    },
    "Microsoft SQL Server": {
        "category": "Databases",
        "aliases": ["mssql", "sql server", "ms sql"]
    },
    "Cassandra": {
        "category": "Databases",
        "aliases": ["apache cassandra"]
    },
    "DynamoDB": {
        "category": "Databases",
        "aliases": ["aws dynamodb", "amazon dynamodb"]
    },

    # --- AI, Machine Learning & Data Science ---
    "Machine Learning": {
        "category": "AI and Machine Learning",
        "aliases": ["ml", "machine-learning"]
    },
    "Deep Learning": {
        "category": "AI and Machine Learning",
        "aliases": ["dl", "neural networks", "deep-learning", "artificial neural networks", "ann", "cnn", "rnn", "lstm"]
    },
    "Natural Language Processing": {
        "category": "AI and Machine Learning",
        "aliases": ["nlp", "natural language processing", "text processing", "text analytics"]
    },
    "Computer Vision": {
        "category": "AI and Machine Learning",
        "aliases": ["cv", "image processing", "opencv"]
    },
    "TensorFlow": {
        "category": "AI and Machine Learning",
        "aliases": ["tf", "tensorflow 2"]
    },
    "PyTorch": {
        "category": "AI and Machine Learning",
        "aliases": ["torch", "pytorch"]
    },
    "scikit-learn": {
        "category": "AI and Machine Learning",
        "aliases": ["sklearn", "scikit learn"]
    },
    "Keras": {
        "category": "AI and Machine Learning",
        "aliases": ["keras"]
    },
    "Generative AI": {
        "category": "AI and Machine Learning",
        "aliases": ["genai", "gen ai", "llm", "large language models", "prompt engineering", "langchain", "llamaindex", "transformers", "hugging face", "huggingface"]
    },
    "Reinforcement Learning": {
        "category": "AI and Machine Learning",
        "aliases": ["rl", "reinforcement learning"]
    },

    # --- Cloud & DevOps ---
    "AWS": {
        "category": "Cloud and DevOps",
        "aliases": ["amazon web services", "amazon aws", "aws cloud", "ec2", "s3", "lambda"]
    },
    "Azure": {
        "category": "Cloud and DevOps",
        "aliases": ["microsoft azure", "azure cloud", "azure devops"]
    },
    "Google Cloud Platform": {
        "category": "Cloud and DevOps",
        "aliases": ["gcp", "google cloud"]
    },
    "Docker": {
        "category": "Cloud and DevOps",
        "aliases": ["docker container", "docker compose", "containerization"]
    },
    "Kubernetes": {
        "category": "Cloud and DevOps",
        "aliases": ["k8s", "kube", "k8", "k8s cluster"]
    },
    "Git": {
        "category": "Cloud and DevOps",
        "aliases": ["git version control", "git cli"],
        "pattern": r"\b[Gg]it\b(?!\s*hub|\s*lab)"
    },
    "GitHub": {
        "category": "Cloud and DevOps",
        "aliases": ["github actions", "gh actions"]
    },
    "GitLab": {
        "category": "Cloud and DevOps",
        "aliases": ["gitlab ci"]
    },
    "CI/CD": {
        "category": "Cloud and DevOps",
        "aliases": ["continuous integration", "continuous delivery", "ci / cd", "ci-cd"]
    },
    "Jenkins": {
        "category": "Cloud and DevOps",
        "aliases": ["jenkins ci"]
    },
    "Terraform": {
        "category": "Cloud and DevOps",
        "aliases": ["infrastructure as code", "iac"]
    },
    "Linux": {
        "category": "Cloud and DevOps",
        "aliases": ["unix", "ubuntu", "debian", "redhat", "centos", "bash", "shell scripting"]
    },

    # --- Data Analytics & BI ---
    "Pandas": {
        "category": "Data Analytics",
        "aliases": ["pandas library"]
    },
    "NumPy": {
        "category": "Data Analytics",
        "aliases": ["numpy array"]
    },
    "Excel": {
        "category": "Data Analytics",
        "aliases": ["ms excel", "microsoft excel", "advanced excel", "vlookup", "pivot tables"]
    },
    "Power BI": {
        "category": "Data Analytics",
        "aliases": ["powerbi", "ms power bi"]
    },
    "Tableau": {
        "category": "Data Analytics",
        "aliases": ["tableau desktop", "tableau server"]
    },
    "Matplotlib": {
        "category": "Data Analytics",
        "aliases": ["seaborn", "data visualization"]
    },
    "Apache Spark": {
        "category": "Data Analytics",
        "aliases": ["spark", "pyspark"]
    },
    "Hadoop": {
        "category": "Data Analytics",
        "aliases": ["apache hadoop", "mapreduce"]
    },
    "BigQuery": {
        "category": "Data Analytics",
        "aliases": ["google bigquery"]
    },
    "Snowflake": {
        "category": "Data Analytics",
        "aliases": ["snowflake db", "snowflake data warehouse"]
    },

    # --- Soft Skills ---
    "Communication": {
        "category": "Soft Skills",
        "aliases": ["verbal communication", "written communication", "interpersonal skills", "presentation skills"]
    },
    "Leadership": {
        "category": "Soft Skills",
        "aliases": ["team leadership", "mentorship", "guiding", "lead"]
    },
    "Problem Solving": {
        "category": "Soft Skills",
        "aliases": ["analytical skills", "troubleshooting", "problem-solving", "critical thinking"]
    },
    "Teamwork": {
        "category": "Soft Skills",
        "aliases": ["collaboration", "cross-functional collaboration", "team player", "collaborative"]
    },
    "Time Management": {
        "category": "Soft Skills",
        "aliases": ["prioritization", "multitasking", "deadline management"]
    },
    "Agile": {
        "category": "Methodologies",
        "aliases": ["agile methodology", "scrum", "kanban", "sprints", "standup"]
    },
    "Project Management": {
        "category": "Methodologies",
        "aliases": ["jira", "trello", "asana", "confluence", "pmp"]
    }
}

# Pre-compile regex matchers for high-speed, boundary-safe search
COMPILED_SKILLS: List[Tuple[str, str, re.Pattern]] = []

def _build_compiled_skills():
    compiled = []
    for canonical, details in SKILLS_TAXONOMY.items():
        category = details.get("category", "Other")
        # If explicit regex pattern provided, use it
        if "pattern" in details:
            pattern = re.compile(details["pattern"], re.IGNORECASE)
            compiled.append((canonical, category, pattern))
            continue

        # Otherwise build word-boundary regex for canonical and all aliases
        terms = [canonical] + details.get("aliases", [])
        # Escape terms and join with |
        escaped_terms = [re.escape(t) for t in terms]
        # Sort by length descending to match longest phrases first (e.g. "React Native" before "React")
        regex_str = r"(?<![\w])(" + "|".join(escaped_terms) + r")(?![\w])"
        pattern = re.compile(regex_str, re.IGNORECASE)
        compiled.append((canonical, category, pattern))
    return compiled

COMPILED_SKILLS = _build_compiled_skills()

def get_all_categories() -> List[str]:
    """Return distinct skill categories in display order."""
    seen = []
    for details in SKILLS_TAXONOMY.values():
        cat = details.get("category", "Other")
        if cat not in seen:
            seen.append(cat)
    return seen

def find_skills_in_text(text: str) -> Dict[str, Dict]:
    """
    Search text for technical and soft skills using word-boundary matching.
    Returns:
        Dict[canonical_name, {"category": str, "matched_term": str}]
    """
    if not text:
        return {}

    detected = {}
    for canonical, category, pattern in COMPILED_SKILLS:
        match = pattern.search(text)
        if match:
            detected[canonical] = {
                "category": category,
                "matched_term": match.group(0).strip()
            }
    return detected
