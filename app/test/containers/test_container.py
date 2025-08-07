from functools import lru_cache
from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from core.config import Config
from core.logging_manager import logger
from usecase.diarization import DiarizationUC
from usecase.llm import LLMUC
from usecase.socket import SocketUC
from test.services.rt_diarization import TestRTDiarizationService
from test.services.llm import TestLLMService
from test.services.embed import TestEmbedService

from test.containers.test_container_manager import TestContainerManager


class TestContainer(DeclarativeContainer):
    manager: TestContainerManager = None
    config = providers.Configuration()
    logger = logger

    # test - service
    test_embed_service = providers.Resource(TestEmbedService)

    test_llm_service = providers.Resource(TestLLMService)

    test_rt_diarization_service = providers.Resource(TestRTDiarizationService)

    # test - usecase
    test_diarization_uc = providers.Singleton(
        DiarizationUC,
        embed_service=test_embed_service,
        rt_diarization_service=test_rt_diarization_service,
        llm_service=test_llm_service,
        SAMPLE_RATE=config.service.sample_rate,
    )

    test_llm_uc = providers.Singleton(
        LLMUC,
        llm_service=test_llm_service,
    )

    test_socket_uc = providers.Singleton(
        SocketUC,
        logger=logger,
        llm_service=test_llm_service,
        rt_diarization_service=test_rt_diarization_service,
        embed_service=test_embed_service,
        MAX_CONNECTIONS=config.service.socket.max_connections,
        MAX_BUFFER_SIZE=config.service.socket.max_buffer_size,
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if TestContainer.manager is not None:
            raise Exception(
                f"MainContainer is a singleton class. Use MainContainer.get_manager() instead."
            )

    @lru_cache(maxsize=1)
    @staticmethod
    def get_manager(*args, **kwargs):
        if TestContainer.manager is None:
            container = TestContainer(*args, **kwargs)
            container.config.update(Config.get_instance().dict)
            TestContainer.manager = TestContainerManager(container)
        return TestContainer.manager


__all__ = ["TestContainer"]
