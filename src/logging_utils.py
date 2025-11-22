# src/logging_utils.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def get_logger(name: str, log_path: Path) -> logging.Logger:
    """
    Create or return a logger with a rotating file handler.
    Ensures we don't attach duplicate handlers if called multiple times.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:  # avoid duplicate handlers
        handler = RotatingFileHandler(
            log_path,
            maxBytes=500_000,  # ~500KB
            backupCount=3,
            encoding="utf-8",
        )
        fmt = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    return logger
