from fastapi import UploadFile, File, Form
import numpy as np

from util.util import bytes_to_np


class SttFile:
    def __init__(
        self,
        audio: UploadFile = File(description="Audio file.", example="audio_bytes"),
        prompt: str | None = Form(
            default=None,
            description="Prompt for the audio file. Default is None.",
            example="prompt",
        ),
        language: str | None = Form(
            default=None,
            description="Language of the audio file. Default is None.",
            example="ko",
        ),
    ):
        self.audio = audio
        self.prompt = prompt
        self.language = language

    async def get_audio(self, sr):
        byte_audio = await self.audio.read()
        np_audio = bytes_to_np(byte_audio, sr)
        return np.mean(np_audio, axis=1) if np_audio.ndim > 1 else np_audio
