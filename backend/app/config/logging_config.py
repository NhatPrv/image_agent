"""Logging configuration for Image Agent.

Provides structured logging with console and rotating file handlers.
Console uses colored output for development, file uses plain text for parsing.
"""

from __future__ import annotations

import contextlib
import logging
import logging.handlers
import sys
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pathlib import Path


def setup_logging(log_level: str = "DEBUG", logs_dir: Path | None = None) -> None:
    """Configure application-wide logging.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        logs_dir: Directory for log files. If None, file logging is disabled.
    """
    # Reconfigure stdout/stderr to use UTF-8 on Windows to prevent UnicodeEncodeError
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stderr.reconfigure(encoding="utf-8")

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))

    # Clear existing handlers to avoid duplicates on reconfiguration
    root_logger.handlers.clear()

    # ─── Console Handler (colored for development) ───
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = _ColoredFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ─── File Handler (rotating, plain text) ───
    if logs_dir is not None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / "image_agent.log"

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10_000_000,  # 10MB per file
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # ─── Suppress noisy third-party loggers ───
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("diffusers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


class _ColoredFormatter(logging.Formatter):
    """Custom formatter that adds ANSI color codes to log levels.

    Only used for console output in development mode.
    """

    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET: ClassVar[str] = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)
