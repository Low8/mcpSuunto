"""Ingest FIT files from local inboxes and optional OneDrive adapters."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from mcpSuunto.duckdb.database import (
    DB_PATH,
    get_connection,
    initialize_schema,
    replace_activity,
)
from mcpSuunto.observability.logging import log_pipeline_error
from mcpSuunto.parsing.parser import _id_for_file, parse_fit

logger = logging.getLogger(__name__)


class OneDriveFile(Protocol):
    """Minimal remote-file contract required by the ingestion pipeline."""

    @property
    def name(self) -> str: ...


class OneDriveClient(Protocol):
    """Connector supplied by the application when OneDrive credentials exist."""

    def list_fit_files(self) -> list[OneDriveFile]: ...

    def download(self, remote_file: OneDriveFile, destination: Path) -> None: ...

    def delete(self, remote_file: OneDriveFile) -> None: ...


@dataclass(frozen=True)
class LocalOneDriveFile:
    """A FIT file in a locally synchronized OneDrive directory."""

    path: Path

    @property
    def name(self) -> str:
        return self.path.name


class LocalOneDriveClient:
    """Adapter for a OneDrive folder already synchronized on this machine."""

    def __init__(self, folder: Path, *, delete_after_download: bool = True) -> None:
        self.folder = folder
        self.delete_after_download = delete_after_download

    def list_fit_files(self) -> list[OneDriveFile]:
        return [
            LocalOneDriveFile(path)
            for path in sorted(self.folder.glob("*.fit"))
            if path.is_file()
        ]

    def download(self, remote_file: OneDriveFile, destination: Path) -> None:
        if not isinstance(remote_file, LocalOneDriveFile):
            raise TypeError("LocalOneDriveClient received an unsupported file type")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(remote_file.path, destination)

    def delete(self, remote_file: OneDriveFile) -> None:
        if not isinstance(remote_file, LocalOneDriveFile):
            raise TypeError("LocalOneDriveClient received an unsupported file type")
        if self.delete_after_download:
            remote_file.path.unlink()


def download_onedrive_files(client: OneDriveClient, inbox: Path) -> list[Path]:
    """Download remote FIT files atomically, deleting remote files only afterward."""
    inbox.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    for remote_file in client.list_fit_files():
        destination = inbox / remote_file.name
        temporary = destination.with_suffix(destination.suffix + ".partial")
        try:
            client.download(remote_file, temporary)
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise OSError("download produced no local FIT file")
            temporary.replace(destination)
            client.delete(remote_file)
            downloaded.append(destination)
        except Exception as error:  # noqa: BLE001 - one failed source file must not stop ingestion
            temporary.unlink(missing_ok=True)
            log_pipeline_error(
                logger,
                path=destination,
                stage="onedrive_download",
                error=error,
            )
    return downloaded


def discover_new_files(inbox: Path, database_path: Path = DB_PATH) -> list[Path]:
    """Return FIT files in the inbox not already committed to DuckDB."""
    files = sorted(inbox.glob("*.fit"))
    connection = get_connection(database_path)
    try:
        initialize_schema(connection)
        known_ids = {
            row[0]
            for row in connection.execute("SELECT activity_id FROM activities").fetchall()
        }
    finally:
        connection.close()
    return [path for path in files if _id_for_file(path) not in known_ids]


def process_fit_file(
    path: Path,
    processed_dir: Path,
    database_path: Path = DB_PATH,
) -> str:
    """Parse, validate, commit, and finally move one FIT file."""
    logger.info("Processing %s", path)
    stage = "parsing"
    try:
        parsed = parse_fit(path, path.name)
        stage = "duckdb_transaction"
        replace_activity(parsed, database_path)

        stage = "move_to_processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        destination = processed_dir / path.name
        if destination.exists():
            if _id_for_file(destination) != _id_for_file(path):
                raise FileExistsError(f"processed file already differs: {destination}")
            path.unlink()
        else:
            shutil.move(str(path), str(destination))
    except Exception as error:
        log_pipeline_error(logger, path=path, stage=stage, error=error)
        raise
    logger.info("Processed %s", path.name)
    return parsed.activity_id


def ingest_directory(
    inbox: Path,
    database_path: Path = DB_PATH,
    processed_dir: Path | None = None,
) -> list[str]:
    """Process every inbox FIT independently; failures remain in the inbox."""
    processed = processed_dir or inbox.parent / "processed"
    imported: list[str] = []
    for path in sorted(inbox.glob("*.fit")):
        try:
            imported.append(process_fit_file(path, processed, database_path))
        except Exception as error:  # noqa: BLE001 - one failed file must not stop ingestion
            log_pipeline_error(logger, path=path, stage="pipeline", error=error)
            continue
    return imported
