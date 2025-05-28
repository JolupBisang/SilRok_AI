import logging
from pathlib import Path
from rich.logging import RichHandler

from config import Config

config = Config.get_instance()
LOG_DIR_PATH = Path(config.config.server.log_dir)
DEFAULT_LOG_LEVEL = config.config.server.log_level


def generate(name: str, level: int = DEFAULT_LOG_LEVEL):
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)
    logger.propagate = False

    logger.addHandler(RichHandler())

    log_path = LOG_DIR_PATH / f"{name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    return logger
