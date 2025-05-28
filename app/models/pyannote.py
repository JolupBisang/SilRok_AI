import asyncio
from pyannote.audio import Inference
import torch
import numpy as np


class Pyannote:
    def __init__(self, hf_token: str):
        if not hf_token:
            raise ValueError("Hugging Face token is required for Pyannote model")
        if not isinstance(hf_token, str):
            raise TypeError("Hugging Face token must be a string")

        super().__init__()

        self.__embedding_model = Inference(
            model="pyannote/embedding",
            window="whole",
            use_auth_token=hf_token,
            device=torch.device("cuda"),
        )
        self.__lock = asyncio.Lock()

    async def get_embeddings(self, audio: np.ndarray, sample_rate: int):
        waveform = torch.from_numpy(audio).unsqueeze(0)
        async with self.__lock:
            return self.__embedding_model(
                {"waveform": waveform, "sample_rate": sample_rate}
            )
