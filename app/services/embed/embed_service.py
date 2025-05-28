from models import Pyannote

from .dto import EmbedInput, EmbedOutput


class EmbedService:
    def __init__(self, pyannote: Pyannote):
        if not isinstance(pyannote, Pyannote):
            raise TypeError("pyannote must be an instance of Pyannote model")

        super().__init__()
        self.pyannote = pyannote

    async def embed(self, embed_input: EmbedInput):
        return EmbedOutput(
            embedding=await self.pyannote.get_embeddings(
                embed_input.audio, embed_input.sample_rate
            )
        )
