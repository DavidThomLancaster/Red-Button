import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """Return a logger configured for this app"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # default log level (adjust per env)

    if not logger.handlers:  # avoid adding duplicate handlers
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
