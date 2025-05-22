import numpy as np
from core import Singleton
from models import Pyannote

from .dto import EmbedInput, EmbedOutput


class EmbedService(Singleton):
    @Pyannote.object
    def __init__(self, pyannote: Pyannote):
        super().__init__()
        self.pyannote = pyannote

    async def embed(self, embed_input: EmbedInput):
        return EmbedOutput(
            embedding=await self.pyannote.get_embeddings(
                embed_input.audio, embed_input.sample_rate
            )
        )
