"""Read-only queries used by the MCP tools."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb

from mcpSuunto.duckdb.database import DB_PATH


def _date(value: date | datetime | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, datetime.min.time()) if isinstance(value, date) and not isinstance(value, datetime) else value


def _json(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value.isoformat() if isinstance(value, (datetime, date)) else value for key, value in row.items()}


class SuuntoRepository:
    """Small read-only repository over the existing DuckDB schema."""

    def __init__(self, database_path: Path = DB_PATH) -> None:
        self.database_path = database_path

    def _query(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        connection = duckdb.connect(str(self.database_path), read_only=True)
        try:
            result = connection.execute(sql, params or [])
            return [_json(dict(zip([item[0] for item in result.description], row))) for row in result.fetchall()]
        finally:
            connection.close()

    def list_activities(self, limit: int, sport: str | None, sub_sport: str | None) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if sport:
            clauses.append("sport = ?")
            params.append(sport)
        if sub_sport:
            clauses.append("sub_sport = ?")
            params.append(sub_sport)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        return self._query(
            f"""SELECT activity_id, start_time AS date, sport, sub_sport, distance_m,
                duration_seconds, elapsed_seconds, ascent_m AS elevation_gain_m,
                descent_m AS elevation_loss_m, avg_heart_rate, max_heart_rate,
                avg_speed_m_s AS avg_speed, calories, training_stress_score AS tss,
                training_effect, avg_power_w, estimated_vo2_max
                FROM activities {where} ORDER BY start_time DESC LIMIT ?""",
            params,
        )

    def get_activity(self, activity_id: str, include_records: bool, include_laps: bool, include_intervals: bool) -> dict[str, Any] | None:
        activities = self._query("SELECT * FROM activities WHERE activity_id = ?", [activity_id])
        if not activities:
            return None
        result: dict[str, Any] = {"activity": activities[0]}
        if include_laps:
            result["laps"] = self._query("SELECT * FROM laps WHERE activity_id = ? ORDER BY start_time", [activity_id])
        if include_intervals:
            result["intervals"] = self._query("SELECT * FROM intervals WHERE activity_id = ? ORDER BY sequence_number", [activity_id])
        if include_records:
            result["records"] = self._query("SELECT * FROM records WHERE activity_id = ? ORDER BY timestamp", [activity_id])
        return result

    def search_activities(self, **filters: Any) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        mapping = {
            "start_date": (">=", _date(filters.get("start_date"))),
            "end_date": ("<=", _date(filters.get("end_date"))),
            "min_distance": (">=", filters.get("min_distance")),
            "max_distance": ("<=", filters.get("max_distance")),
            "min_duration": (">=", filters.get("min_duration")),
            "max_duration": ("<=", filters.get("max_duration")),
            "min_elevation_gain": (">=", filters.get("min_elevation_gain")),
            "max_elevation_gain": ("<=", filters.get("max_elevation_gain")),
        }
        for name, (operator, value) in mapping.items():
            if value is not None:
                column = {"start_date": "start_time", "end_date": "start_time", "min_distance": "distance_m", "max_distance": "distance_m", "min_duration": "duration_seconds", "max_duration": "duration_seconds", "min_elevation_gain": "ascent_m", "max_elevation_gain": "ascent_m"}[name]
                clauses.append(f"{column} {operator} ?")
                params.append(value)
        for name in ("sport", "sub_sport"):
            if filters.get(name):
                clauses.append(f"{name} = ?")
                params.append(filters[name])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(100)
        return self._query(f"SELECT * FROM activities {where} ORDER BY start_time DESC LIMIT ?", params)

    def training_history(self, start_date: date, end_date: date, sport: str | None, group_by: str) -> list[dict[str, Any]]:
        group = {"day": "day", "week": "week", "month": "month"}[group_by]
        sport_clause = "AND sport = ?" if sport else ""
        params: list[Any] = [datetime.combine(start_date, datetime.min.time()), datetime.combine(end_date, datetime.max.time())]
        if sport:
            params.append(sport)
        return self._query(
            f"""SELECT date_trunc('{group}', start_time) AS period, count(*) AS activities,
                sum(distance_m) AS distance_m, sum(duration_seconds) AS duration_seconds,
                sum(ascent_m) AS elevation_gain_m, sum(descent_m) AS elevation_loss_m,
                sum(training_stress_score) AS tss, sum(calories) AS calories
                FROM activities WHERE start_time BETWEEN ? AND ? {sport_clause}
                GROUP BY 1 ORDER BY 1""",
            params,
        )

    def training_load(self, start_date: date, end_date: date, sport: str | None) -> dict[str, Any]:
        history = self.training_history(start_date, end_date, sport, "week")
        activities = self.search_activities(start_date=start_date, end_date=end_date, sport=sport)
        return {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "activities": len(activities), "weeks": history, "last_intense": next((item for item in activities if (item.get("training_effect") or 0) >= 3), None), "longest_activity": max(activities, key=lambda item: item.get("distance_m") or 0, default=None)}

    def records(self, activity_id: str, start_time: datetime | None, end_time: datetime | None, fields: list[str] | None, sample_every: int) -> list[dict[str, Any]]:
        allowed = {"timestamp", "latitude", "longitude", "distance_m", "altitude_m", "speed_m_s", "heart_rate", "cadence", "power_w", "temperature_c", "vertical_speed_m_s", "ngp_m_s", "grade_pct"}
        selected = ["timestamp"] + [field for field in (fields or sorted(allowed - {"timestamp"})) if field in allowed and field != "timestamp"]
        clauses = ["activity_id = ?"]
        params: list[Any] = [activity_id]
        if start_time:
            clauses.append("timestamp >= ?")
            params.append(start_time)
        if end_time:
            clauses.append("timestamp <= ?")
            params.append(end_time)
        params.append(max(1, min(sample_every, 3600)))
        return self._query(f"SELECT {', '.join(selected)} FROM records WHERE {' AND '.join(clauses)} QUALIFY row_number() OVER (ORDER BY timestamp) % ? = 1 ORDER BY timestamp", params)

    def intervals(self, activity_id: str | None, source: str | None, limit: int) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if activity_id:
            clauses.append("activity_id = ?")
            params.append(activity_id)
        if source:
            clauses.append("source = ?")
            params.append(source)
        params.append(limit)
        return self._query(f"SELECT * FROM intervals {'WHERE ' + ' AND '.join(clauses) if clauses else ''} ORDER BY start_time DESC LIMIT ?", params)

    def compare(self, activity_ids: list[str]) -> list[dict[str, Any]]:
        placeholders = ", ".join("?" for _ in activity_ids)
        return self._query(f"SELECT * FROM activities WHERE activity_id IN ({placeholders}) ORDER BY start_time", activity_ids)

    def similar(self, activity_id: str, limit: int) -> list[dict[str, Any]]:
        activity = self.get_activity(activity_id, False, False, False)
        if activity is None:
            return []
        item = activity["activity"]
        return self._query("""SELECT *, abs(distance_m - ?) + abs(coalesce(ascent_m, 0) - coalesce(?, 0)) * 0.01 AS similarity_score
            FROM activities WHERE activity_id <> ? AND sport = ? ORDER BY similarity_score LIMIT ?""",
            [item["distance_m"] or 0, item["ascent_m"] or 0, activity_id, item["sport"], limit])

    def personal_bests(self) -> dict[str, Any]:
        rows = self._query("""SELECT 'longest_activity' AS metric, activity_id, distance_m AS value, start_time AS date
            FROM activities ORDER BY distance_m DESC NULLS LAST LIMIT 1""")
        elevation = self._query("""SELECT 'largest_elevation_gain' AS metric, activity_id, ascent_m AS value, start_time AS date
            FROM activities ORDER BY ascent_m DESC NULLS LAST LIMIT 1""")
        return {"available_metrics": rows + elevation, "note": "Distance-based running records require record-level segment computation and are not inferred from activity summaries."}

    def recent_context(self) -> dict[str, Any]:
        today = datetime.now(UTC).date()
        return {"last_7_days": self.training_load(today - timedelta(days=6), today, None), "last_28_days": self.training_load(today - timedelta(days=27), today, None), "recent_activities": self.list_activities(10, None, None)}
