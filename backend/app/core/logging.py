"""Logging configuration built on Loguru.

Provides a single ``setup_logging`` entrypoint that the app calls on startup so
log formatting stays consistent across the codebase.
"""

import sys

from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    """Configure Loguru with a readable console sink."""
    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
        backtrace=False,
        diagnose=False,
    )


__all__ = ["logger", "setup_logging"]
