"""
Logging configuration for WinSvalinn.
"""

import logging
import os
from datetime import datetime


def setup_logging(log_file="winsvalinn.log", level=logging.INFO):
    """
    Setup application logging.

    Args:
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
    )

    logger = logging.getLogger("WinSvalinn")
    logger.info("=" * 60)
    logger.info(f"WinSvalinn started at {datetime.now()}")
    logger.info("=" * 60)

    return logger


# Create default logger
logger = logging.getLogger("WinSvalinn")


class ModuleLogger:
    """
    Logger wrapper for modules.

    Provides consistent logging across all modules with module-specific names.
    """

    def __init__(self, module_name):
        self.logger = logging.getLogger(f"WinSvalinn.{module_name}")

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.logger.exception(msg, *args, **kwargs)
