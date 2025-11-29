"""
Database Access Layer for Scanner Service
Lightweight interface to Django database
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from .config import DATABASE_URL


def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(DATABASE_URL)


def get_scan_by_id(scan_id: str):
    """Retrieve scan record by ID"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM scans_scan WHERE id = %s",
                (scan_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()


def update_scan_status(scan_id: str, status: str):
    """Update scan status"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE scans_scan 
                   SET status = %s, updated_at = %s 
                   WHERE id = %s""",
                (status, datetime.utcnow(), scan_id)
            )
            conn.commit()
    finally:
        conn.close()


def create_finding(finding_data: dict):
    """Create a new finding record"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO scans_finding 
                   (scan_id, tool, severity, title, file_path, line_number, raw_output, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (
                    finding_data['scan_id'],
                    finding_data['tool'],
                    finding_data['severity'],
                    finding_data['title'],
                    finding_data.get('file_path'),
                    finding_data.get('line_number'),
                    finding_data.get('raw_output', {}),
                    datetime.utcnow()
                )
            )
            finding_id = cur.fetchone()[0]
            conn.commit()
            return finding_id
    finally:
        conn.close()
