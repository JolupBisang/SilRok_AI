import logging
from rich.logging import RichHandler


def generate(name: str, level: int = logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(RichHandler())
    logger.propagate = False
    return logger
