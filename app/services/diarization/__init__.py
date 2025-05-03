# services/diarization/__init__.py

from .DiarizationService import DiarizationService
from . import dto

__all__ = [
  "DiarizationService",
  "dto"
]