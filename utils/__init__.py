# utils/__init__.py

import logging


def get_logger(name: str, filename_prefix: str = "MusicMatcher"):
    """Return a basic stream logger used by crawler workers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
