from fastapi import Request
from pydantic import BaseModel
from core import Settings
from dto.request.annotations import AudioFile, SampleRate

class DiarizationEmbedRequest(BaseModel):
    audio: bytes
    sample_rate: SampleRate

    @classmethod
    async def as_file(
        cls,
        audio:AudioFile,
        sample_rate: SampleRate = Settings.MODEL_SAMPLE_RATE
    ):
        return cls(
            audio=audio,
            sample_rate=sample_rate,
        )

    @classmethod
    async def as_stream(
        cls,
        audio:Request,
        sample_rate: SampleRate = Settings.MODEL_SAMPLE_RATE
    ):
        return cls(
            audio=await audio.body(),
            sample_rate=sample_rate,
        )


class DiarizationEmbedFileRequest:
    def __init__(
        self,
        audio:AudioFile,
        sample_rate: SampleRate = Settings.MODEL_SAMPLE_RATE
    ):
        self.audio = audio
        self.sample_rate = sample_rate

    async def __call__(self):
        return DiarizationEmbedRequest(
            audio=await self.audio.read(),
            sample_rate=self.sample_rate,
        )


class DiarizationEmbedStreamRequest:
    def __init__(
        self,
        audio:Request,
        sample_rate: SampleRate = Settings.MODEL_SAMPLE_RATE
    ):
        self.audio = audio
        self.sample_rate = sample_rate

    async def __call__(self):
        return DiarizationEmbedRequest(
            audio=await self.audio.body(),
            sample_rate=self.sample_rate,
        )




