import hashlib
import json
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import duckdb

from mcpSuunto.models import ParsedActivity

DB_PATH = Path("data/database/suunto.duckdb")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection(database_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    path = database_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def initialize_schema(connection: duckdb.DuckDBPyConnection) -> None:
    """Create the database tables from the canonical SQL schema."""
    connection.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
    connection.execute("ALTER TABLE activities ADD COLUMN IF NOT EXISTS avg_ngp_m_s DOUBLE")
    connection.execute("ALTER TABLE activities ADD COLUMN IF NOT EXISTS hills DOUBLE")
    connection.execute("ALTER TABLE records ADD COLUMN IF NOT EXISTS ngp_m_s DOUBLE")
    connection.execute("ALTER TABLE records ADD COLUMN IF NOT EXISTS grade_pct DOUBLE")


def _insert_rows(
    connection: duckdb.DuckDBPyConnection,
    table: str,
    columns: list[str],
    rows: Iterable[dict[str, Any]],
) -> None:
    materialized = list(rows)
    if not materialized:
        return
    names = ", ".join(columns)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".jsonl", delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        for row in materialized:
            temporary.write(json.dumps(row, default=str) + "\n")
    try:
        connection.execute(
            f"INSERT INTO {table} ({names}) "
            f"SELECT {names} FROM read_json_auto(?)",
            [str(temporary_path)],
        )
    finally:
        temporary_path.unlink(missing_ok=True)


def _child_rows(
    activity_id: str,
    prefix: str,
    rows: Iterable[Any],
    id_column: str,
) -> list[dict[str, Any]]:
    result = []
    for index, model in enumerate(rows):
        identifier = int(
            hashlib.sha256(f"{activity_id}:{prefix}:{index}".encode()).hexdigest()[:15],
            16,
        )
        result.append({id_column: identifier, "activity_id": activity_id, **model.model_dump(mode="json")})
    return result


def replace_activity(
    parsed: ParsedActivity,
    database_path: Path | None = None,
) -> None:
    """Atomically replace one activity and all its child records."""
    connection = get_connection(database_path)
    transaction_started = False
    activity_id = parsed.activity_id
    try:
        initialize_schema(connection)
        connection.execute("BEGIN TRANSACTION")
        transaction_started = True
        for table in (
            "records",
            "laps",
            "intervals",
            "developer_fields",
            "lengths",
            "events",
            "activities",
        ):
            connection.execute(f"DELETE FROM {table} WHERE activity_id = ?", [activity_id])

        activity = parsed.activity.model_dump(mode="json")
        _insert_rows(connection, "activities", list(activity), [activity])
        _insert_rows(
            connection,
            "records",
            ["activity_id"] + list(parsed.records[0].model_dump(mode="json"))
            if parsed.records
            else [],
            [{"activity_id": activity_id, **record.model_dump(mode="json")} for record in parsed.records],
        )
        _insert_rows(
            connection,
            "laps",
            ["lap_id", "activity_id"] + list(parsed.laps[0].model_dump(mode="json"))
            if parsed.laps
            else [],
            _child_rows(activity_id, "lap", parsed.laps, "lap_id"),
        )
        _insert_rows(
            connection,
            "intervals",
            ["interval_id", "activity_id"] + list(parsed.intervals[0].model_dump(mode="json"))
            if parsed.intervals
            else [],
            _child_rows(activity_id, "interval", parsed.intervals, "interval_id"),
        )
        _insert_rows(
            connection,
            "developer_fields",
            ["developer_field_id", "activity_id"] + list(parsed.developer_fields[0].model_dump(mode="json"))
            if parsed.developer_fields
            else [],
            _child_rows(activity_id, "developer", parsed.developer_fields, "developer_field_id"),
        )
        _insert_rows(
            connection,
            "lengths",
            ["length_id", "activity_id"] + list(parsed.lengths[0].model_dump(mode="json"))
            if parsed.lengths
            else [],
            _child_rows(activity_id, "length", parsed.lengths, "length_id"),
        )
        _insert_rows(
            connection,
            "events",
            ["event_id", "activity_id"] + list(parsed.events[0].model_dump(mode="json"))
            if parsed.events
            else [],
            _child_rows(activity_id, "event", parsed.events, "event_id"),
        )
        connection.execute("COMMIT")
    except Exception:
        if transaction_started:
            connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()