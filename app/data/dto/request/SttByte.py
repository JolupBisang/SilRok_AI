import base64
import io
from fastapi import Query
import numpy as np

from util.util import bytes_to_np

class SttByte:
  def __init__(
    self, 
    raw_audio:str = Query(
      description= "Audio bytes encoded in base64.",
      example= "audio_bytes"
    ),
    prompt:str|None = Query(
      default = None,
      description= "Prompt for the audio file. Default is None.",
      example= "prompt"
    ),
    language:str|None = Query(
      default = None,
      description= "Language of the audio file. Default is None.",
      example= "ko"
    )
  ):
    self.audio = raw_audio
    self.prompt = prompt
    self.language = language

  async def get_audio(self, sr):
    byte_audio = base64.b64decode(self.audio.encode("utf-8"))
    np_audio = bytes_to_np(byte_audio, sr)
    return np.mean(np_audio, axis=1) if np_audio.ndim > 1 else np_audio