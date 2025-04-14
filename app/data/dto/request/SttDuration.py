import base64
import io
from fastapi import Query
import numpy as np

from util.util import bytes_to_np, decompress_from_opus

class SttDuration:
  def __init__(
    self, 
    audio:str = Query(
      description= "Audio bytes encoded in base64.",
      example= "audio_bytes"
    ),
    group:str = Query(
      description= "Group name. This is used to identify the group of audio files.",
      example= "group"
    ),
    user:str = Query(
      description= "User name. This is used to identify the user of the audio files.",
      example= "user"
    ),
    language:str|None = Query(
      default = None,
      description= "Language of the audio file. Default is None.",
      example= "ko"
    )
  ):
    self.audio = audio
    self.group = group
    self.user = user
    self.language = language

  async def get_audio(self, sr):
    byte_audio = base64.b64decode(self.audio.encode("utf-8"))
    # byte_audio, _ = decompress_from_opus(byte_audio)
    np_audio = bytes_to_np(byte_audio, sr)
    np_audio = np_audio.astype(np.float32)
    return np.mean(np_audio, axis=1) if np_audio.ndim > 1 else np_audio