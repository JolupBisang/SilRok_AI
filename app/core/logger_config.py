import logging
import logging.config
from pathlib import Path

from config import Config

LOG_DIR_PATH = Path(Config.get_instance().config.server.log_dir)
LOG_DIR_PATH.mkdir(exist_ok=True)


def setup_main_logging():

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
