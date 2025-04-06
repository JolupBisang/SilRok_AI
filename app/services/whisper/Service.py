from logging import Logger
import re
from typing import Generator
import numpy as np

from ServerObject import ServerObject
from models import Whisper
from core import settings
from services import LoggerService
from services.whisper import Tokenizer
from services.whisper import Sentence, Word

class Service(ServerObject):
  @Whisper.object
  def __init__(
    self,
    whisper:Whisper,
    sample_rate:int = settings.MODEL_SAMPLE_RATE
  ):
    super().__init__()

    self._SAMPLE_RATE = sample_rate
    self._whisper = whisper

  def transcribe(
    self,
    audio:np.ndarray,
    prompt:str = None,
    language:str = None
  ):

    segments, info = self._whisper.transcribe(audio, language, prompt)
    language =info.lanuage
    sentences = self._segment_word(segments, language, 0)

    return sentences

  @LoggerService.object
  def _segment_word(
    self, 
    segments:Generator, 
    language:str, 
    time_offset:float,
    logger_service:Logger
  ):
    tokenizer = Tokenizer.get_tokenizer(language)
    
    sentences = []
    if tokenizer is None:
      logger_service.warning(f"Tokenizer not found for {language}.")
      for segment in segments:
        text = segment.text
        words = segment.words
        sentences.append(Sentence(
          [language], 
          text,
          [Word(
            w.start + time_offset, 
            w.end + time_offset, 
            w.word,
            language
          ) for w in words]
        ))
      return sentences

    text = ""
    words = []
    for segment in segments:
      text += segment.text
      words.extend([
        Word(
          w.start + time_offset, 
          w.end + time_offset, 
          w.word,
          language
        ) for w in segment.words
      ])
      
    scents = tokenizer.segment(text)
    idx_end = 0
    for scent in scents:
      idx_start = idx_end
      # 문제 있음
      idx_end = idx_start + len(re.split(r"[, ]", scent))

      sentences.append(Sentence(
        [language], 
        scent, 
        words[idx_start:idx_end]
      ))
      
    return sentences
