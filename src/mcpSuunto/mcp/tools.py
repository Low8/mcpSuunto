"""MCP tool definitions backed by the read-only repository."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from mcpSuunto.mcp.repository import SuuntoRepository

repo = SuuntoRepository()


def _date_range(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")


def list_activities(limit: int = 10, sport: str | None = None, sub_sport: str | None = None) -> list[dict]:
    """List recent activities, without second-by-second records."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    return repo.list_activities(limit, sport, sub_sport)


def get_activity(activity_id: str, include_records: bool = False, include_laps: bool = True, include_intervals: bool = True) -> dict:
    """Get one activity summary and optionally its laps, intervals, and records."""
    result = repo.get_activity(activity_id, include_records, include_laps, include_intervals)
    if result is None:
        raise ValueError(f"Activity not found: {activity_id}")
    return result


def search_activities(start_date: date | None = None, end_date: date | None = None, sport: str | None = None, sub_sport: str | None = None, min_distance: float | None = None, max_distance: float | None = None, min_duration: float | None = None, max_duration: float | None = None, min_elevation_gain: float | None = None, max_elevation_gain: float | None = None) -> list[dict]:
    """Search activities by date, sport, distance, duration, and elevation."""
    if start_date and end_date:
        _date_range(start_date, end_date)
    return repo.search_activities(**locals())


def get_training_history(start_date: date, end_date: date, sport: str | None = None, group_by: Literal["day", "week", "month"] = "week") -> list[dict]:
    """Aggregate training history by day, week, or month."""
    _date_range(start_date, end_date)
    return repo.training_history(start_date, end_date, sport, group_by)


def get_training_load(start_date: date, end_date: date, sport: str | None = None) -> dict:
    """Return objective training load totals and weekly breakdown."""
    _date_range(start_date, end_date)
    return repo.training_load(start_date, end_date, sport)


def get_performance_trends(start_date: date, end_date: date, sport: str = "running") -> list[dict]:
    """Return comparable activity metrics for trend analysis by the LLM."""
    _date_range(start_date, end_date)
    return repo.search_activities(start_date=start_date, end_date=end_date, sport=sport)


def get_intervals(activity_id: str | None = None, source: str | None = None, limit: int = 100) -> list[dict]:
    """Return structured workout intervals, preserving their FIT source metadata."""
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")
    return repo.intervals(activity_id, source, limit)


def query_activity_records(activity_id: str, start_time: datetime | None = None, end_time: datetime | None = None, fields: list[str] | None = None, sample_every: int = 1) -> list[dict]:
    """Query selected activity records with optional time bounds and sampling."""
    if end_time and start_time and end_time < start_time:
        raise ValueError("end_time must be on or after start_time")
    return repo.records(activity_id, start_time, end_time, fields, sample_every)


def compare_activities(activity_ids: list[str]) -> list[dict]:
    """Compare activity summaries by returning the selected activities as rows."""
    if not 1 <= len(activity_ids) <= 20:
        raise ValueError("activity_ids must contain between 1 and 20 items")
    return repo.compare(activity_ids)


def compare_intervals(activity_ids: list[str]) -> list[dict]:
    """Return intervals from multiple activities for structured comparison."""
    if not 1 <= len(activity_ids) <= 20:
        raise ValueError("activity_ids must contain between 1 and 20 items")
    return repo.intervals(None, None, 5000) if len(activity_ids) == 0 else repo._query("SELECT * FROM intervals WHERE activity_id IN (" + ", ".join("?" for _ in activity_ids) + ") ORDER BY start_time", activity_ids)


def get_similar_activities(activity_id: str, limit: int = 10) -> list[dict]:
    """Find activities with the same sport and similar distance and elevation."""
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    return repo.similar(activity_id, limit)


def get_personal_bests() -> dict:
    """Return only personal-best metrics computable from stored summaries."""
    return repo.personal_bests()


def get_recent_training_context() -> dict:
    """Return seven-day and 28-day objective training context for the LLM."""
    return repo.recent_context()
