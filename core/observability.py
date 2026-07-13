"""SQLite observability logger.
Writes AssessmentEvents to data/assessments.db.
log_assessment() is always wrapped in try/except — never crashes the pipeline.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from core.schema import AssessmentEvent

DB_PATH = Path("data/assessments.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS assessment_events (
    event_id        TEXT PRIMARY KEY,
    timestamp       TEXT NOT NULL,
    business_name   TEXT NOT NULL,
    sector          TEXT NOT NULL,
    tier            TEXT NOT NULL,
    weighted_score  REAL NOT NULL,
    total_latency_ms INTEGER NOT NULL,
    payload         TEXT NOT NULL
)
"""


class ObservabilityLogger:
    """Writes assessment events to SQLite. Never raises."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(CREATE_TABLE_SQL)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def log_assessment(self, event: AssessmentEvent) -> None:
        """Write one event to SQLite. Silently swallows all errors."""
        try:
            payload = json.dumps({
                "scorecard_latency_ms": event.scorecard_latency_ms,
                "llm_explain_latency_ms": event.llm_explain_latency_ms,
                "llm_plan_latency_ms": event.llm_plan_latency_ms,
                "retrieval_latency_ms": event.retrieval_latency_ms,
                "weakest_dimensions": event.scorecard_result.weakest_dimensions,
                "explanation_length": len(event.explanation),
                "plan_action_count": len(event.improvement_plan.actions),
                "recommendations_count": len(event.recommendation_result.matches),
                "cluster_id": event.cluster_assignment.cluster_id,
            })
            with self._connect() as conn:
                conn.execute(
                    """INSERT INTO assessment_events
                       (event_id, timestamp, business_name, sector, tier,
                        weighted_score, total_latency_ms, payload)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        event.event_id,
                        event.timestamp,
                        event.profile.business_name,
                        event.profile.sector,
                        event.scorecard_result.tier,
                        event.scorecard_result.weighted_score,
                        event.total_latency_ms,
                        payload,
                    ),
                )
                conn.commit()
        except Exception:
            pass

    def get_recent_assessments(self, n: int = 10) -> list[dict]:
        """Return the n most recent assessment events as dicts. For debugging."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """SELECT event_id, timestamp, business_name, sector,
                              tier, weighted_score, total_latency_ms, payload
                       FROM assessment_events
                       ORDER BY timestamp DESC
                       LIMIT ?""",
                    (n,),
                ).fetchall()
            result = []
            for row in rows:
                entry = {
                    "event_id": row[0],
                    "timestamp": row[1],
                    "business_name": row[2],
                    "sector": row[3],
                    "tier": row[4],
                    "weighted_score": row[5],
                    "total_latency_ms": row[6],
                }
                entry.update(json.loads(row[7]))
                result.append(entry)
            return result
        except Exception:
            return []
