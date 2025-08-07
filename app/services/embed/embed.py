import asyncio
import ray

from services.embed.dto import EmbedInput, EmbedOutput


@ray.remote(num_cpus=1, num_gpus=0.08)
class Embed:
    def __init__(self):
        self.pyannote = None
        self.logger = None

    def init(self):
        from containers import Container
        from core import logging_manager

        manager = Container.get_manager()
        manager.init_embed()

        self.pyannote = manager.container.pyannote()
        self.logger = logging_manager.generate("embed")

        self.logger.info("Embed service initialized")

    async def request(self, X: EmbedInput):
        self.logger.debug(f"Received request: {X}")
        Y = EmbedOutput(
            user_id=X.user_id,
            embedding=await self.pyannote.get_embeddings(X.audio, X.sample_rate),
        )
        self.logger.debug(f"Processed request: {Y}")
        return Y

    async def close(self):
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        ray.actor.exit_actor()
        self.logger.info("Embed service closed")
