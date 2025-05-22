import asyncio
from pyannote.audio import Inference
import torch
import numpy as np

from core import Settings, Singleton


class Pyannote(Singleton):
    def __init__(
        self,
        hf_token: str = Settings.HF_TOKEN,
    ):
        super().__init__()

        self.__embedding_model = Inference(
            model="pyannote/embedding",
            window="whole",
            use_auth_token=hf_token,
            device=torch.device("cuda"),
        )
        self.__lock = asyncio.Lock()

    async def get_embeddings(self, audio: np.ndarray, sample_rate:int):
        waveform = torch.from_numpy(audio).unsqueeze(0)
        async with self.__lock:
            return self.__embedding_model(
                {"waveform": waveform, "sample_rate": sample_rate}
            )
