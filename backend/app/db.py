from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "app.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {row["name"] for row in rows}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    for column, definition in columns.items():
        ensure_column(conn, table, column, definition)


def init_db() -> None:
    schema_statements: Iterable[str] = [
        """
        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'manual',
            source_url TEXT,
            summary TEXT NOT NULL DEFAULT '',
            raw_text TEXT NOT NULL DEFAULT '',
            tags TEXT NOT NULL DEFAULT '[]',
            weirdness INTEGER NOT NULL DEFAULT 5,
            pain_signal INTEGER NOT NULL DEFAULT 5,
            source_category TEXT NOT NULL DEFAULT '',
            quality_score INTEGER,
            quality_reason TEXT NOT NULL DEFAULT '',
            fingerprint TEXT NOT NULL DEFAULT '',
            collected_at TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ideas (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            one_liner TEXT NOT NULL DEFAULT '',
            weird_angle TEXT NOT NULL DEFAULT '',
            real_pain TEXT NOT NULL DEFAULT '',
            first_screen TEXT NOT NULL DEFAULT '',
            mvp TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'new',
            status_note TEXT NOT NULL DEFAULT '',
            rejection_reason TEXT NOT NULL DEFAULT '',
            revival_condition TEXT NOT NULL DEFAULT '',
            source_signal_ids TEXT NOT NULL DEFAULT '[]',
            scores TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            review_type TEXT NOT NULL,
            passes INTEGER NOT NULL DEFAULT 0,
            flags TEXT NOT NULL DEFAULT '[]',
            comment TEXT NOT NULL DEFAULT '',
            suggestions TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            title TEXT NOT NULL,
            goal TEXT NOT NULL DEFAULT '',
            method TEXT NOT NULL DEFAULT '',
            success_criteria TEXT NOT NULL DEFAULT '',
            result_status TEXT NOT NULL DEFAULT 'pending',
            result_summary TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS exports (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            export_type TEXT NOT NULL,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE
        )
        """,


        """
        CREATE TABLE IF NOT EXISTS prototype_workspaces (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            worker TEXT NOT NULL DEFAULT 'manual',
            directory TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'created',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS prototype_runs (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            workspace_id TEXT,
            title TEXT NOT NULL DEFAULT '',
            worker TEXT NOT NULL DEFAULT 'manual',
            status TEXT NOT NULL DEFAULT 'planned',
            goal TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            changed_files TEXT NOT NULL DEFAULT '[]',
            test_commands TEXT NOT NULL DEFAULT '[]',
            result TEXT NOT NULL DEFAULT '',
            next_step TEXT NOT NULL DEFAULT '',
            report_path TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE,
            FOREIGN KEY (workspace_id) REFERENCES prototype_workspaces(id) ON DELETE SET NULL
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS repo_experiments (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            repo_url TEXT NOT NULL,
            run_mode TEXT NOT NULL DEFAULT 'inspect_only',
            status TEXT NOT NULL DEFAULT 'planned',
            summary TEXT NOT NULL DEFAULT '',
            detected_stack TEXT NOT NULL DEFAULT '[]',
            evidence TEXT NOT NULL DEFAULT '[]',
            setup_commands TEXT NOT NULL DEFAULT '[]',
            build_commands TEXT NOT NULL DEFAULT '[]',
            test_commands TEXT NOT NULL DEFAULT '[]',
            start_commands TEXT NOT NULL DEFAULT '[]',
            risks TEXT NOT NULL DEFAULT '[]',
            report_path TEXT NOT NULL DEFAULT '',
            workspace_dir TEXT NOT NULL DEFAULT '',
            logs TEXT NOT NULL DEFAULT '[]',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS taste_feedback (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            action TEXT NOT NULL,
            weight INTEGER NOT NULL DEFAULT 0,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
            id TEXT PRIMARY KEY,
            job_key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            enabled INTEGER NOT NULL DEFAULT 0,
            schedule_type TEXT NOT NULL DEFAULT 'daily',
            interval_minutes INTEGER,
            time_of_day TEXT NOT NULL DEFAULT '',
            day_of_week INTEGER,
            config_json TEXT NOT NULL DEFAULT '{}',
            last_run_at TEXT NOT NULL DEFAULT '',
            next_run_at TEXT NOT NULL DEFAULT '',
            last_status TEXT NOT NULL DEFAULT 'idle',
            last_message TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scheduled_job_runs (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            job_key TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL DEFAULT '',
            duration_seconds REAL NOT NULL DEFAULT 0,
            summary TEXT NOT NULL DEFAULT '',
            warning TEXT NOT NULL DEFAULT '',
            error TEXT NOT NULL DEFAULT '',
            result_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY (job_id) REFERENCES scheduled_jobs(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS idea_events (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            related_idea_ids TEXT NOT NULL DEFAULT '[]',
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE
        )
        """,
    ]
    with get_connection() as conn:
        for statement in schema_statements:
            conn.execute(statement)

        # Keep additive migrations explicit so older phase databases can still boot.
        ensure_columns(
            conn,
            "signals",
            {
                "source_category": "TEXT NOT NULL DEFAULT ''",
                "quality_score": "INTEGER",
                "quality_reason": "TEXT NOT NULL DEFAULT ''",
                "fingerprint": "TEXT NOT NULL DEFAULT ''",
                "collected_at": "TEXT NOT NULL DEFAULT ''",
            },
        )
        ensure_columns(
            conn,
            "ideas",
            {
                "status_note": "TEXT NOT NULL DEFAULT ''",
                "rejection_reason": "TEXT NOT NULL DEFAULT ''",
                "revival_condition": "TEXT NOT NULL DEFAULT ''",
            },
        )
        ensure_columns(
            conn,
            "prototype_workspaces",
            {
                "title": "TEXT NOT NULL DEFAULT ''",
                "worker": "TEXT NOT NULL DEFAULT 'manual'",
                "status": "TEXT NOT NULL DEFAULT 'created'",
                "notes": "TEXT NOT NULL DEFAULT ''",
                "updated_at": "TEXT NOT NULL DEFAULT ''",
            },
        )
        ensure_columns(
            conn,
            "prototype_runs",
            {
                "workspace_id": "TEXT",
                "worker": "TEXT NOT NULL DEFAULT 'manual'",
                "status": "TEXT NOT NULL DEFAULT 'planned'",
                "goal": "TEXT NOT NULL DEFAULT ''",
                "summary": "TEXT NOT NULL DEFAULT ''",
                "changed_files": "TEXT NOT NULL DEFAULT '[]'",
                "test_commands": "TEXT NOT NULL DEFAULT '[]'",
                "result": "TEXT NOT NULL DEFAULT ''",
                "next_step": "TEXT NOT NULL DEFAULT ''",
                "report_path": "TEXT NOT NULL DEFAULT ''",
                "updated_at": "TEXT NOT NULL DEFAULT ''",
            },
        )
        ensure_columns(
            conn,
            "repo_experiments",
            {
                "title": "TEXT NOT NULL DEFAULT ''",
                "run_mode": "TEXT NOT NULL DEFAULT 'inspect_only'",
                "status": "TEXT NOT NULL DEFAULT 'planned'",
                "summary": "TEXT NOT NULL DEFAULT ''",
                "detected_stack": "TEXT NOT NULL DEFAULT '[]'",
                "evidence": "TEXT NOT NULL DEFAULT '[]'",
                "setup_commands": "TEXT NOT NULL DEFAULT '[]'",
                "build_commands": "TEXT NOT NULL DEFAULT '[]'",
                "test_commands": "TEXT NOT NULL DEFAULT '[]'",
                "start_commands": "TEXT NOT NULL DEFAULT '[]'",
                "risks": "TEXT NOT NULL DEFAULT '[]'",
                "report_path": "TEXT NOT NULL DEFAULT ''",
                "workspace_dir": "TEXT NOT NULL DEFAULT ''",
                "logs": "TEXT NOT NULL DEFAULT '[]'",
                "notes": "TEXT NOT NULL DEFAULT ''",
                "updated_at": "TEXT NOT NULL DEFAULT ''",
            },
        )
        ensure_columns(
            conn,
            "scheduled_jobs",
            {
                "description": "TEXT NOT NULL DEFAULT ''",
                "enabled": "INTEGER NOT NULL DEFAULT 0",
                "schedule_type": "TEXT NOT NULL DEFAULT 'daily'",
                "interval_minutes": "INTEGER",
                "time_of_day": "TEXT NOT NULL DEFAULT ''",
                "day_of_week": "INTEGER",
                "config_json": "TEXT NOT NULL DEFAULT '{}'",
                "last_run_at": "TEXT NOT NULL DEFAULT ''",
                "next_run_at": "TEXT NOT NULL DEFAULT ''",
                "last_status": "TEXT NOT NULL DEFAULT 'idle'",
                "last_message": "TEXT NOT NULL DEFAULT ''",
            },
        )
        ensure_columns(
            conn,
            "scheduled_job_runs",
            {
                "finished_at": "TEXT NOT NULL DEFAULT ''",
                "duration_seconds": "REAL NOT NULL DEFAULT 0",
                "summary": "TEXT NOT NULL DEFAULT ''",
                "warning": "TEXT NOT NULL DEFAULT ''",
                "error": "TEXT NOT NULL DEFAULT ''",
                "result_json": "TEXT NOT NULL DEFAULT '{}'",
            },
        )
        ensure_columns(
            conn,
            "idea_events",
            {
                "title": "TEXT NOT NULL DEFAULT ''",
                "note": "TEXT NOT NULL DEFAULT ''",
                "related_idea_ids": "TEXT NOT NULL DEFAULT '[]'",
                "metadata": "TEXT NOT NULL DEFAULT '{}'",
            },
        )
        ensure_columns(
            conn,
            "taste_feedback",
            {
                "weight": "INTEGER NOT NULL DEFAULT 0",
                "note": "TEXT NOT NULL DEFAULT ''",
            },
        )
        conn.commit()
