from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from mcpSuunto.duckdb.database import replace_activity
from mcpSuunto.mcp import tools
from mcpSuunto.mcp.repository import SuuntoRepository
from mcpSuunto.models import Activity, ParsedActivity


@pytest.fixture
def mcp_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SuuntoRepository:
    database_path = tmp_path / "suunto.duckdb"
    replace_activity(
        ParsedActivity(
            activity=Activity(
                activity_id="mcp-activity",
                source_file="run.fit",
                start_time=datetime(2026, 10, 1, tzinfo=UTC),
                sport="running",
                distance_m=10000,
                duration_seconds=3600,
                ascent_m=120,
            )
        ),
        database_path,
    )
    repository = SuuntoRepository(database_path)
    monkeypatch.setattr(tools, "repo", repository)
    return repository


def test_list_activities_returns_summary_without_records(mcp_repository: SuuntoRepository) -> None:
    result = tools.list_activities()

    assert result[0]["activity_id"] == "mcp-activity"
    assert "records" not in result[0]


def test_get_activity_rejects_unknown_id(mcp_repository: SuuntoRepository) -> None:
    with pytest.raises(ValueError, match="Activity not found"):
        tools.get_activity("missing")


def test_training_history_and_comparison_use_duckdb(mcp_repository: SuuntoRepository) -> None:
    history = tools.get_training_history(
        date(2026, 1, 1), date(2026, 12, 31)
    )
    comparison = tools.compare_activities(["mcp-activity"])

    assert history[0]["activities"] == 1
    assert comparison[0]["distance_m"] == 10000
