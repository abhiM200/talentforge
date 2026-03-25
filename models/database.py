"""
SQLite database models for TalentForge.
Stores resume analysis results.
"""

import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'talentforge.db')

def get_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                candidate_name TEXT,
                ats_score REAL,
                ats_tier TEXT,
                skills_count INTEGER,
                matched_keywords INTEGER,
                missing_keywords INTEGER,
                top_job_match TEXT,
                email_sent_to TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                full_analysis TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

def save_analysis(
    filename: str,
    analysis: Dict[str, Any],
    email_sent_to: Optional[str] = None
) -> Optional[int]:
    """
    Save analysis results to database.
    
    Args:
        filename: Original uploaded file name
        analysis: Complete analysis dictionary
        email_sent_to: Email address if report was sent
        
    Returns:
        Record ID on success, None on failure
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        parsed = analysis.get("parsed_resume", {})
        ats = analysis.get("ats_score", {})
        jobs = analysis.get("job_matches", [])
        
        top_job = jobs[0]["title"] if jobs else None
        
        cursor.execute('''
            INSERT INTO analyses (
                filename, candidate_name, ats_score, ats_tier,
                skills_count, matched_keywords, missing_keywords,
                top_job_match, email_sent_to, full_analysis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            filename,
            parsed.get("name", "Unknown"),
            ats.get("total_score", 0),
            ats.get("tier", "N/A"),
            len(parsed.get("skills", [])),
            len(ats.get("matched_keywords", [])),
            len(ats.get("missing_keywords", [])),
            top_job,
            email_sent_to,
            json.dumps(analysis)
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Analysis saved with ID: {record_id}")
        return record_id
        
    except Exception as e:
        logger.error(f"Error saving analysis: {e}")
        return None

def get_recent_analyses(limit: int = 10) -> List[Dict]:
    """Get recent analyses from database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, candidate_name, ats_score, ats_tier,
                   skills_count, top_job_match, created_at
            FROM analyses
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"Error fetching analyses: {e}")
        return []

def get_analysis_by_id(record_id: int) -> Optional[Dict]:
    """Get full analysis by ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM analyses WHERE id = ?', (record_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result = dict(row)
            if result.get("full_analysis"):
                result["full_analysis"] = json.loads(result["full_analysis"])
            return result
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching analysis: {e}")
        return None
