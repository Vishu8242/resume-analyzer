"""
Database Module for Analysis History
Uses SQLite to store privacy-compliant analysis metadata without retaining original
resume files or sensitive full text.
Uses parameterized queries and safe JSON serialization.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from config.settings import DATABASE_PATH, ATS_DISCLAIMER


def get_db_connection(db_path: str = DATABASE_PATH) -> sqlite3.Connection:
    """
    Creates and returns a SQLite database connection with row factory enabled.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DATABASE_PATH) -> None:
    """
    Initializes the SQLite database schema if not already present.
    Ensures the full_data column exists for complete analysis bundle persistence.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                job_title TEXT,
                overall_score REAL NOT NULL,
                component_scores TEXT NOT NULL,
                matching_skills TEXT,
                missing_skills TEXT,
                summary TEXT,
                full_data TEXT
            );
        """)
        # Safe migration if table previously created without full_data
        cursor.execute("PRAGMA table_info(analyses)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "full_data" not in columns:
            try:
                cursor.execute("ALTER TABLE analyses ADD COLUMN full_data TEXT;")
            except Exception:
                pass
        conn.commit()


def save_analysis(
    overall_score: float,
    component_scores: Dict[str, Any],
    job_title: str = "Not specified",
    matching_skills: List[str] = None,
    missing_skills: List[str] = None,
    summary: str = "",
    full_data: Optional[Dict[str, Any]] = None,
    db_path: str = DATABASE_PATH
) -> int:
    """
    Saves an analysis record using parameterized SQL.
    JSON serializes complex structures and full analysis bundle safely.
    Returns the newly inserted record ID.
    """
    init_db(db_path)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    comp_json = json.dumps(component_scores if component_scores else {})
    match_json = json.dumps(matching_skills if matching_skills else [])
    miss_json = json.dumps(missing_skills if missing_skills else [])
    full_data_json = json.dumps(full_data) if full_data else "{}"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analyses (
                created_at, job_title, overall_score, component_scores,
                matching_skills, missing_skills, summary, full_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            created_at,
            job_title,
            float(overall_score),
            comp_json,
            match_json,
            miss_json,
            summary,
            full_data_json
        ))
        conn.commit()
        return cursor.lastrowid


def get_all_analyses(db_path: str = DATABASE_PATH, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieves analysis records sorted newest first.
    Parses stored JSON fields and merges full analysis bundle back into Python structures.
    """
    init_db(db_path)
    records = []
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, created_at, job_title, overall_score,
                   component_scores, matching_skills, missing_skills, summary, full_data
            FROM analyses
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()

        for r in rows:
            try:
                comp = json.loads(r["component_scores"]) if r["component_scores"] else {}
            except Exception:
                comp = {}

            try:
                matches = json.loads(r["matching_skills"]) if r["matching_skills"] else []
            except Exception:
                matches = []

            try:
                missing = json.loads(r["missing_skills"]) if r["missing_skills"] else []
            except Exception:
                missing = []

            # Check if full_data column exists and parse it
            full_bundle = {}
            if "full_data" in r.keys() and r["full_data"]:
                try:
                    full_bundle = json.loads(r["full_data"])
                except Exception:
                    full_bundle = {}

            score = float(r["overall_score"])
            grade = "Excellent Compatibility" if score >= 85 else (
                "Strong Compatibility" if score >= 70 else (
                    "Moderate Compatibility" if score >= 50 else "Low Compatibility"
                )
            )
            color = "#10B981" if score >= 85 else (
                "#3B82F6" if score >= 70 else (
                    "#F59E0B" if score >= 50 else "#EF4444"
                )
            )

            rec = {
                "id": r["id"],
                "created_at": r["created_at"],
                "job_title": r["job_title"] or "Not specified",
                "overall_score": score,
                "grade": grade,
                "color": color,
                "verdict": r["summary"] or "",
                "component_scores": comp,
                "matching_skills": matches,
                "missing_skills": missing,
                "summary": r["summary"] or "",
                "candidate_name": "Candidate",
                "disclaimer": ATS_DISCLAIMER,
                "effective_weights": {
                    "skills": 0.40,
                    "experience": 0.20,
                    "education": 0.15,
                    "keywords": 0.15,
                    "formatting": 0.10
                },
                "skills_analysis": {
                    "matching_skills": matches,
                    "matching_required": matches,
                    "matching_preferred": [],
                    "missing_required": missing,
                    "missing_preferred": [],
                    "additional_skills": [],
                    "stats": {
                        "total_job_skills": len(matches) + len(missing),
                        "total_matching": len(matches),
                        "total_missing_required": len(missing),
                        "total_missing_preferred": 0,
                        "total_candidate_skills": len(matches)
                    },
                    "match_percentage": round((len(matches) / (len(matches) + len(missing)) * 100), 1) if (len(matches) + len(missing)) > 0 else 0.0
                },
                "recommendations": [
                    f"Incorporate missing required skills if experienced: {', '.join(missing[:4])}."
                ] if missing else [
                    "Highlight demonstrable impact with quantifiable metrics.",
                    "Ensure standard section headings are prominently positioned."
                ]
            }

            # Merge any saved full bundle data (takes precedence)
            if isinstance(full_bundle, dict):
                for k, v in full_bundle.items():
                    if v is not None and v != "" and v != {} and v != []:
                        rec[k] = v

            records.append(rec)

    return records


def delete_analysis(analysis_id: int, db_path: str = DATABASE_PATH) -> bool:
    """
    Deletes an analysis record by its primary key ID using parameterized SQL.
    """
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_analyses(db_path: str = DATABASE_PATH) -> bool:
    """
    Purges all analysis records from the database.
    """
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analyses")
        conn.commit()
        return True


def get_database_statistics(db_path: str = DATABASE_PATH) -> Dict[str, Any]:
    """
    Calculates summary statistics from real database records.
    Never returns fake metrics.
    """
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                AVG(overall_score) as avg_score,
                MAX(overall_score) as max_score
            FROM analyses
        """)
        row = cursor.fetchone()

        total = row["total_count"] if row else 0
        avg_score = round(float(row["avg_score"]), 1) if row and row["avg_score"] is not None else 0.0
        max_score = round(float(row["max_score"]), 1) if row and row["max_score"] is not None else 0.0

        # Fetch latest analysis
        latest_record = None
        if total > 0:
            cursor.execute("""
                SELECT id, created_at, job_title, overall_score
                FROM analyses
                ORDER BY id DESC
                LIMIT 1
            """)
            latest_row = cursor.fetchone()
            if latest_row:
                latest_record = {
                    "id": latest_row["id"],
                    "created_at": latest_row["created_at"],
                    "job_title": latest_row["job_title"] or "Not specified",
                    "overall_score": float(latest_row["overall_score"])
                }

    return {
        "total_analyses": total,
        "average_score": avg_score,
        "highest_score": max_score,
        "latest_analysis": latest_record
    }
