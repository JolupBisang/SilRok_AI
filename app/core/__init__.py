# core/__init__.py

import logging

from .settings import Settings
from .singleton import Singleton
from .async_manager import AsyncManager
from . import logging_manager

# logger = logging_manager.generate("core", logging.DEBUG)
logger = logging_manager.generate("core", logging.INFO)

__all__ = [
    "Settings",
    "Singleton",
    "AsyncManager",
    "logger",
    "logging_manager",
]
