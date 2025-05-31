from abc import ABC
import inspect
from dependency_injector.containers import DeclarativeContainer
from dependency_injector import providers


class ContainerManager(ABC):
    def __init__(self, container: DeclarativeContainer) -> None:
        self.container: DeclarativeContainer = container

    async def init_main(self):
        self.container.embed_service()
        await self.container.llm_service.init()
        await self.container.rt_diarization_service.init()
        self.container.diarization_uc()
        self.container.llm_uc()
        self.container.socket_uc()

    def init_llm(self):
        self.container.gemini()

    def init_diarization(self):
        self.container.pyannote()

    def init_embed(self):
        self.container.pyannote()

    async def init_all(self):
        for provider in self.container.providers.values():
            if isinstance(provider, providers.Resource):
                init = provider.init()
                if inspect.iscoroutine(init):
                    await provider.init()
            provider()

    async def shutdown_resources(self):
        await self.container.shutdown_resources()
