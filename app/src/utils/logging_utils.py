"""Logging utilities."""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(log_file: Optional[str] = None,
                 console_logging: bool = True,
                 file_logging: bool = True,
                 debug: bool = False) -> logging.Logger:
    """Set up application logging.

    Args:
        log_file: Path to log file. If None, uses default location.
        console_logging: Enable console logging.
        file_logging: Enable file logging.
        debug: Enable debug level logging.

    Returns:
        Configured logger instance.
    """
    # Create main logger
    logger = logging.getLogger('sonarr_youtubedl')

    # Clear any existing handlers
    logger.handlers.clear()

    # Set log level
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Set up file logging
    if file_logging:
        if log_file is None:
            # Default log file location
            log_dir = Path(__file__).parent.parent.parent.parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = '{}/sonarr_youtubedl.log'.format(log_dir)

        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=5
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            file_handler.set_name('FileHandler')
            logger.addHandler(file_handler)

        except Exception as e:
            print(f"Warning: Could not set up file logging: {e}")

    # Set up console logging
    if console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        console_handler.set_name('StreamHandler')
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)
