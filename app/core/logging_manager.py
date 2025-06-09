import logging
from pathlib import Path
from rich.logging import RichHandler

from .config import Config

config = Config.get_instance()
LOG_DIR_PATH = Path(config.config.server.log_dir)
LOG_DIR_PATH.mkdir(exist_ok=True)
DEFAULT_LOG_LEVEL = config.config.server.log_level
FILE_LOG_LEVEL = config.config.server.file_log_level


def setup_main_logging():
    return

    # FIXME 로깅 설정에 문제 있음
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "formatter": "default",
                    "filename": str(LOG_DIR_PATH / "app.log"),
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "core": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": "WARNING",
            },
        }
    )


def generate(name: str, level: int = DEFAULT_LOG_LEVEL):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # logger.propagate = False

    if not any(isinstance(h, RichHandler) for h in logger.handlers):
        logger.addHandler(RichHandler())

    log_path = LOG_DIR_PATH / f"{name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not any(
        isinstance(h, logging.FileHandler) and h.baseFilename == str(log_path)
        for h in logger.handlers
    ):
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(FILE_LOG_LEVEL)
        logger.addHandler(file_handler)

    return logger
