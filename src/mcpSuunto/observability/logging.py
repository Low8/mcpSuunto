"""Centralized logging configuration and pipeline error reporting."""

from __future__ import annotations

import logging
from pathlib import Path

_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(log_file: Path | None = None, level: int = logging.INFO) -> None:
    """Configure console logging and, optionally, a persistent log file."""
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(level=level, format=_FORMAT, handlers=handlers, force=True)


def log_pipeline_error(
    logger: logging.Logger,
    *,
    path: Path,
    stage: str,
    error: BaseException,
) -> None:
    """Log a failure with the file and pipeline stage needed for diagnosis."""
    logger.error("FIT processing failed file=%s stage=%s error=%s", path, stage, error)
    logger.debug("FIT processing traceback file=%s stage=%s", path, stage, exc_info=error)
