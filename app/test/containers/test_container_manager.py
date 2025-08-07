import inspect
from dependency_injector.containers import DeclarativeContainer
from dependency_injector import providers


class TestContainerManager:
    def __init__(self, container: DeclarativeContainer) -> None:
        self.container: DeclarativeContainer = container

    async def init_test(self):
        self.container.test_embed_service()
        self.container.test_llm_service()
        self.container.test_rt_diarization_service()
        self.container.test_diarization_uc()
        self.container.test_llm_uc()
        self.container.test_socket_uc()

    async def init_all(self):
        for provider in self.container.providers.values():
            if isinstance(provider, providers.Resource):
                init = provider.init()
                if inspect.iscoroutine(init):
                    await provider.init()
            provider()

    async def shutdown_resources(self):
        await self.container.shutdown_resources()

__all__ = ["TestContainerManager"]
