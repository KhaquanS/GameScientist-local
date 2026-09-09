from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from gamescientist.core.evaluation import EvaluationReport


class RunStore:
    """Small local SQLite store for reproducible run summaries and public traces."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path))
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in {0, 1}:
                raise RuntimeError(f"unsupported GameScientist database version: {version}")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    task_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    complete INTEGER NOT NULL,
                    reward INTEGER,
                    steps INTEGER NOT NULL,
                    actions_json TEXT NOT NULL,
                    transcript_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute("PRAGMA user_version = 1")

    def record(
        self,
        report: EvaluationReport,
        actions: list[str],
        transcript: list[dict[str, object]],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO runs (
                    run_id, task_key, status, complete, reward, steps,
                    actions_json, transcript_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.run_id,
                    report.task_key,
                    report.status,
                    int(report.complete),
                    report.reward,
                    report.steps,
                    json.dumps(actions),
                    json.dumps(transcript),
                ),
            )

    def list_runs(self, task_key: str = "") -> list[dict[str, Any]]:
        query = "SELECT * FROM runs"
        parameters: tuple[str, ...] = ()
        if task_key:
            query += " WHERE task_key = ?"
            parameters = (task_key,)
        query += " ORDER BY created_at, run_id"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [
            {
                "runId": row["run_id"],
                "taskKey": row["task_key"],
                "status": row["status"],
                "complete": bool(row["complete"]),
                "reward": row["reward"],
                "steps": row["steps"],
                "actions": json.loads(row["actions_json"]),
                "transcript": json.loads(row["transcript_json"]),
                "createdAt": row["created_at"],
            }
            for row in rows
        ]
