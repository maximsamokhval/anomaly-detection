"""Loguru logging configuration for debug mode."""

import sys
from pathlib import Path

from loguru import logger

# Remove default handler
logger.remove()

# Logs directory
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

# Add console handler with debug level
logger.add(
    sys.stderr,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

# Add file handler for debug logs
logger.add(
    logs_dir / "debug.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="10 MB",
    retention="7 days",
)


def get_logger(name: str = __name__):
    """Get a logger instance with the specified name."""
    return logger.bind(name=name)


__all__ = ["logger", "get_logger"]
