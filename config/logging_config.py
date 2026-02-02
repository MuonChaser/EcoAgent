"""
Unified Logging Configuration Module

Generates an independent log file for each run, with filenames including script name and timestamp.

Usage:
    from config.logging_config import setup_logger

    # Call at the beginning of a script
    setup_logger("my_script")  # Generates logs/my_script_20240129_143052.log

    # Or auto-detect the caller's script name
    setup_logger()  # Auto-detect script name
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from loguru import logger

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Log directory
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger(
    script_name: str = None,
    level: str = "INFO",
    file_level: str = "DEBUG",
    console: bool = True
) -> Path:
    """
    Configure logging system, generating an independent log file for each run

    Args:
        script_name: Script name for log file naming. If None, auto-detect
        level: Console log level
        file_level: File log level
        console: Whether to output to console

    Returns:
        Log file path
    """
    # Auto-detect script name
    if script_name is None:
        # Get caller's script name
        import inspect
        frame = inspect.stack()[1]
        caller_file = frame.filename
        script_name = Path(caller_file).stem

    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"{script_name}_{timestamp}.log"

    # Remove default handlers
    logger.remove()

    # Add console handler
    if console:
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level=level
        )

    # Add file handler
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=file_level,
        encoding="utf-8",
        rotation=None,  # No rotation, one new file per run
    )

    logger.info(f"Log file: {log_file}")

    return log_file


def get_logger():
    """Get logger instance"""
    return logger


# Convenience variable
LOG_FILE = None  # Will be set after setup_logger is called


def setup_logger_with_return(script_name: str = None, **kwargs) -> tuple:
    """
    Configure logging and return logger and log file path

    Returns:
        (logger, log_file_path)
    """
    log_file = setup_logger(script_name, **kwargs)
    return logger, log_file
