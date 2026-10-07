from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest

from mcpSuunto.duckdb import database
from mcpSuunto.duckdb.database import replace_activity
from mcpSuunto.ingestion import ingest
from mcpSuunto.models import Activity, ParsedActivity


def make_activity() -> ParsedActivity:
    return ParsedActivity(
        activity=Activity(
            activity_id="activity-1",
            source_file="run.fit",
            start_time=datetime(2026, 1, 1, tzinfo=UTC),
            sport="running",
        )
    )


def test_database_transaction_persists_valid_activity(tmp_path: Path) -> None:
    database = tmp_path / "suunto.duckdb"

    replace_activity(make_activity(), database)

    connection = duckdb.connect(str(database), read_only=True)
    assert connection.execute("SELECT count(*) FROM activities").fetchone() == (1,)
    connection.close()


def test_database_rolls_back_when_a_child_insert_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "suunto.duckdb"
    replace_activity(make_activity(), database_path)

    def fail(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated insert failure")

    monkeypatch.setattr(database, "_insert_rows", fail)
    with pytest.raises(RuntimeError, match="simulated insert failure"):
        replace_activity(make_activity(), database_path)

    connection = duckdb.connect(str(database_path), read_only=True)
    assert connection.execute("SELECT count(*) FROM activities").fetchone() == (1,)
    connection.close()


def test_invalid_fit_stays_in_inbox(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    invalid = inbox / "invalid.fit"
    invalid.write_bytes(b"not a FIT file")

    assert ingest.ingest_directory(inbox, tmp_path / "database.duckdb") == []
    assert invalid.exists()
    assert not (tmp_path / "processed" / invalid.name).exists()


def test_local_onedrive_client_copies_then_deletes_source(tmp_path: Path) -> None:
    source = tmp_path / "onedrive"
    inbox = tmp_path / "inbox"
    source.mkdir()
    fit = source / "activity.fit"
    fit.write_bytes(b"fit")

    client = ingest.LocalOneDriveClient(source)
    downloaded = ingest.download_onedrive_files(client, inbox)

    assert downloaded == [inbox / "activity.fit"]
    assert downloaded[0].read_bytes() == b"fit"
    assert not fit.exists()


def test_local_onedrive_client_can_keep_source(tmp_path: Path) -> None:
    source = tmp_path / "onedrive"
    inbox = tmp_path / "inbox"
    source.mkdir()
    fit = source / "activity.fit"
    fit.write_bytes(b"fit")

    client = ingest.LocalOneDriveClient(source, delete_after_download=False)
    ingest.download_onedrive_files(client, inbox)

    assert fit.exists()


def test_files_are_processed_independently(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    first = inbox / "first.fit"
    second = inbox / "second.fit"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    def parse(path: Path, source_file: str) -> ParsedActivity:
        if path.name == "first.fit":
            raise ValueError("invalid first file")
        return make_activity()

    monkeypatch.setattr(ingest, "parse_fit", parse)
    monkeypatch.setattr(ingest, "replace_activity", lambda parsed, database: None)

    assert len(ingest.ingest_directory(inbox, tmp_path / "database.duckdb")) == 1
    assert first.exists()
    assert not second.exists()
    assert (tmp_path / "processed" / second.name).exists()


@pytest.mark.skipif(
    not Path("data/processed/2026-09-30_15.36.50-running.fit").exists(),
    reason="local FIT sample is not checked into Git",
)
def test_workout_steps_are_intervals() -> None:
    from mcpSuunto.parsing.parser import parse_fit

    parsed = parse_fit(Path("data/processed/2026-09-30_15.36.50-running.fit"))

    assert len(parsed.intervals) == 8
    assert all(interval.source == "workout" for interval in parsed.intervals)
    assert all(interval.interval_type is None for interval in parsed.intervals)
