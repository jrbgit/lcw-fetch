import os
import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """Setup logging configuration with loguru"""

    # Remove default handler
    logger.remove()

    # Ensure log directory exists
    Path(log_dir).mkdir(exist_ok=True)

    # Console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File handler for general logs
    logger.add(
        os.path.join(log_dir, "lcw_fetcher.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="10 MB",
        retention="30 days",
        compression="gz",
    )

    # File handler for errors only
    logger.add(
        os.path.join(log_dir, "errors.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
    )

    # File handler for API calls (debug level)
    logger.add(
        os.path.join(log_dir, "api_calls.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        filter=lambda record: "api" in record.get("name", "").lower(),
        rotation="10 MB",
        retention="7 days",
        compression="gz",
    )

    logger.info(f"Logging configured with level: {log_level}")
    logger.info(f"Log files will be stored in: {Path(log_dir).resolve()}")
