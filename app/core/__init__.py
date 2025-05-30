# core/__init__.py

import logging
from . import lifecycle
from . import logging_manager
from .config import Config

# logger = logging_manager.generate("core", logging.DEBUG)
logger = logging_manager.generate("core", logging.INFO)

__all__ = [
    "lifecycle",
    "logging_manager",
    "logger",
    "Config",
]
