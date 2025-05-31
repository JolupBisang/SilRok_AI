import asyncio
import ray

from .dto import EmbedInput, EmbedOutput


@ray.remote(num_cpus=1, num_gpus=0.08)
class Embed:
    def __init__(self):
        self.pyannote = None

    def init(self):
        from containers import Container

        manager = Container.get_manager()
        manager.init_embed()

        self.pyannote = manager.container.pyannote()

    async def request(self, X: EmbedInput):
        return EmbedOutput(
            user_id=X.user_id,
            embedding=await self.pyannote.get_embeddings(X.audio, X.sample_rate),
        )

    async def close(self):
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        ray.actor.exit_actor()
