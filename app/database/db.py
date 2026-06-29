from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.database.models import ConnectedAccountRecord, ProcessedSubmissionRecord


class SQLiteSubmissionStore:
    def __init__(self, database_url: str) -> None:
        self.database_path = self._resolve_database_path(database_url)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.ensure_schema()

    @staticmethod
    def _resolve_database_path(database_url: str) -> Path:
        if database_url.startswith("sqlite:///"):
            return Path(database_url.removeprefix("sqlite:///"))
        return Path(database_url)

    def ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_submissions (
                submission_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                processed_at TEXT NOT NULL,
                github_status TEXT NOT NULL DEFAULT 'pending',
                github_commit TEXT,
                linkedin_status TEXT NOT NULL,
                linkedin_error TEXT,
                github_error TEXT
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS connected_accounts (
                provider TEXT PRIMARY KEY,
                account_data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._ensure_column("processed_submissions", "github_status", "TEXT NOT NULL DEFAULT 'pending'")
        self._ensure_column("processed_submissions", "linkedin_error", "TEXT")
        self._ensure_column("processed_submissions", "github_error", "TEXT")
        self._connection.commit()

    def _ensure_column(self, table_name: str, column_name: str, column_definition: str) -> None:
        existing_columns = {
            row[1]
            for row in self._connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        if column_name not in existing_columns:
            self._connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")

    def get(self, submission_id: str) -> ProcessedSubmissionRecord | None:
        row = self._connection.execute(
            "SELECT submission_id, title, processed_at, github_status, github_commit, linkedin_status, linkedin_error, github_error FROM processed_submissions WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
        if row is None:
            return None
        return ProcessedSubmissionRecord(
            submission_id=row["submission_id"],
            title=row["title"],
            processed_at=datetime.fromisoformat(row["processed_at"]),
            github_status=row["github_status"] or "pending",
            github_commit=row["github_commit"],
            linkedin_status=row["linkedin_status"],
            linkedin_error=row["linkedin_error"],
            github_error=row["github_error"],
        )

    def save(self, record: ProcessedSubmissionRecord) -> None:
        self._connection.execute(
            """
            INSERT INTO processed_submissions (submission_id, title, processed_at, github_status, github_commit, linkedin_status, linkedin_error, github_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(submission_id) DO UPDATE SET
                title = excluded.title,
                processed_at = excluded.processed_at,
                github_status = excluded.github_status,
                github_commit = excluded.github_commit,
                linkedin_status = excluded.linkedin_status,
                linkedin_error = excluded.linkedin_error,
                github_error = excluded.github_error
            """,
            (
                record.submission_id,
                record.title,
                record.processed_at.astimezone(timezone.utc).isoformat(),
                record.github_status,
                record.github_commit,
                record.linkedin_status,
                record.linkedin_error,
                record.github_error,
            ),
        )
        self._connection.commit()

    def upsert_account(self, record: ConnectedAccountRecord) -> None:
        self._connection.execute(
            """
            INSERT INTO connected_accounts (provider, account_data, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                account_data = excluded.account_data,
                updated_at = excluded.updated_at
            """,
            (
                record.provider,
                json.dumps(record.data),
                record.updated_at.astimezone(timezone.utc).isoformat(),
            ),
        )
        self._connection.commit()

    def get_account(self, provider: str) -> ConnectedAccountRecord | None:
        row = self._connection.execute(
            "SELECT provider, account_data, updated_at FROM connected_accounts WHERE provider = ?",
            (provider,),
        ).fetchone()
        if row is None:
            return None
        return ConnectedAccountRecord(
            provider=row["provider"],
            data=json.loads(row["account_data"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def delete_account(self, provider: str) -> None:
        self._connection.execute("DELETE FROM connected_accounts WHERE provider = ?", (provider,))
        self._connection.commit()

    def list_accounts(self) -> list[ConnectedAccountRecord]:
        rows = self._connection.execute(
            "SELECT provider, account_data, updated_at FROM connected_accounts ORDER BY provider"
        ).fetchall()
        return [
            ConnectedAccountRecord(
                provider=row["provider"],
                data=json.loads(row["account_data"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    def latest(self) -> ProcessedSubmissionRecord | None:
        row = self._connection.execute(
            "SELECT submission_id, title, processed_at, github_status, github_commit, linkedin_status, linkedin_error, github_error FROM processed_submissions ORDER BY processed_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return ProcessedSubmissionRecord(
            submission_id=row["submission_id"],
            title=row["title"],
            processed_at=datetime.fromisoformat(row["processed_at"]),
            github_status=row["github_status"] or "pending",
            github_commit=row["github_commit"],
            linkedin_status=row["linkedin_status"],
            linkedin_error=row["linkedin_error"],
            github_error=row["github_error"],
        )

    def close(self) -> None:
        self._connection.close()
