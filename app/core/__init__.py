# core/__init__.py

import logging
from . import lifecycle
from . import logger_config
from . import logging_manager

# logger = logging_manager.generate("core", logging.DEBUG)
logger = logging_manager.generate("core", logging.INFO)

__all__ = [
    "lifecycle",
    "logger_config",
    "logging_manager",
    "logger",
]
