import asyncio
from pyannote.audio import Inference
import torch
import numpy as np

from ServerObject import ServerObject
from core import settings


class Pyannote(ServerObject):
    def __init__(
        self,
        SAMPLE_RATE: int = settings.MODEL_SAMPLE_RATE,
        hf_token: str = settings.HF_TOKEN,
    ):
        super().__init__()

        self.__SAMPLE_RATE = SAMPLE_RATE
        self.__embedding_model = Inference(
            model="pyannote/embedding",
            window="whole",
            use_auth_token=hf_token,
            device=torch.device("cuda"),
        )
        self.__lock = asyncio.Lock()

    async def get_embeddings(self, audio: np.ndarray):
        waveform = torch.from_numpy(audio).unsqueeze(0)
        async with self.__lock:
            return self.__embedding_model(
                {"waveform": waveform, "sample_rate": self.__SAMPLE_RATE}
            )
