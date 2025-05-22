import logging
from pathlib import Path
from rich.logging import RichHandler

from core import Settings

def generate(name: str, level: int = logging.DEBUG):
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)
    logger.propagate = False

    logger.addHandler(RichHandler())

    log_path = Path(Settings.LOG_DIR) / f"{name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    return logger
