import io
import re
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
import subprocess

def camel_to_snake(name:str) -> str:
  s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def compress_to_opus(bytes: bytes) -> bytes:
  process = subprocess.Popen(
    ["ffmpeg", "-i", "pipe:0", "-c:a", "libopus", "-f", "opus", "pipe:1"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE # subprocess.DEVNULL 하면 속도 조금 더 빨라짐
  )

  out, err = process.communicate(input=bytes)
  return out, err 

def decompress_from_opus(bytes: bytes) -> bytes:
  process = subprocess.Popen(
    ["ffmpeg", "-i", "pipe:0", "-f", "wav", "pipe:1"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
  )
  out, err = process.communicate(input=bytes)
  return out, err

def audio_to_np(bytes:io.BytesIO, sample_rate:int) -> np.ndarray:
  with bytes as buffer:
    audio, sr = sf.read(buffer, dtype='float32')
  if sr != sample_rate:
    audio = resample_poly(audio, sample_rate, sr)
  return audio

def np_to_wav(audio: np.ndarray, sample_rate:int) -> bytes:
  buffer = io.BytesIO()
  sf.write(buffer, audio, sample_rate, format='wav')
  return buffer.getvalue()