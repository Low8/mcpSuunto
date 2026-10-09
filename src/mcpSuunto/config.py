"""Local application configuration."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.toml"


@dataclass(frozen=True)
class AppConfig:
    """Paths that vary between installations."""

    onedrive_dir: Path
    inbox_dir: Path
    processed_dir: Path
    database_path: Path
    log_file: Path

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> AppConfig:
        values: dict[str, str] = {}
        if path.is_file():
            with path.open("rb") as config_file:
                data = tomllib.load(config_file)
            values = {key: str(value) for key, value in data.get("paths", {}).items()}

        def get_path(name: str, default: str) -> Path:
            value = os.environ.get(f"SUUNTO_{name.upper()}") or values.get(name, default)
            result = Path(value).expanduser()
            return result if result.is_absolute() else PROJECT_ROOT / result

        return cls(
            onedrive_dir=get_path("onedrive_dir", r"C:\Users\Louis\OneDrive\suunto\fit"),
            inbox_dir=get_path("inbox_dir", "data/inbox"),
            processed_dir=get_path("processed_dir", "data/processed"),
            database_path=get_path("database_path", "data/database/suunto.duckdb"),
            log_file=get_path("log_file", "data/logs/ingestion.log"),
        )
