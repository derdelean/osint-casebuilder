"""SQLite persistence for investigations ("cases"). Stdlib only.

Each run is saved as one row: the seed inputs, the full findings list, and the
correlation summary (findings/summary stored as JSON blobs)."""

import json
import sqlite3
from datetime import datetime

DEFAULT_DB = "cases.db"


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT NOT NULL,
            seed        TEXT NOT NULL,
            n_findings  INTEGER NOT NULL,
            findings    TEXT NOT NULL,
            summary     TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_case(seed: dict, findings: list, summary: dict, db_path: str = DEFAULT_DB,
              created_at: str = None) -> int:
    """Persist one investigation. Returns the new case id."""
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO cases (created_at, seed, n_findings, findings, summary) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                json.dumps(seed, default=str),
                len(findings),
                json.dumps(findings, default=str),
                json.dumps(summary, default=str),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_cases(db_path: str = DEFAULT_DB) -> list:
    """Return case headers (no findings blob), newest first."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, created_at, seed, n_findings FROM cases ORDER BY id DESC"
        ).fetchall()
        return [
            {"id": r[0], "created_at": r[1], "seed": json.loads(r[2]), "n_findings": r[3]}
            for r in rows
        ]
    finally:
        conn.close()


def load_case(case_id: int, db_path: str = DEFAULT_DB) -> dict:
    """Return one full case, or None if not found."""
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT id, created_at, seed, findings, summary FROM cases WHERE id = ?",
            (case_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "created_at": row[1],
            "seed": json.loads(row[2]),
            "findings": json.loads(row[3]),
            "summary": json.loads(row[4]),
        }
    finally:
        conn.close()
