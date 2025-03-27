import io
from faster_whisper import WhisperModel, BatchedInferencePipeline

MODEL_SIZE = "large-v3"

LANGUAGE = {
  "ko": "This audio is in Korean. but, some English words are included.",
  "en": "This audio is in English."
}

class Whisper:
  def __init__(self):
    self.__model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="int8")
    self.__batched_model = BatchedInferencePipeline(self.__model)

  def translate(self, audio: bytes, language:str = "ko"):
    if language not in LANGUAGE:
      raise ValueError(f"Unsupported language: {language}")
 
    audio_stream = io.BytesIO(audio)

    return self.__batched_model.transcribe(
      audio_stream, batch_size=8, beam_size=5, language=language,
      word_timestamps=True, vad_filter=True,
      initial_prompt=LANGUAGE[language]
    )
