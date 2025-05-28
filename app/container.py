import inspect
from types import coroutine
from dependency_injector.containers import DeclarativeContainer
from dependency_injector import providers

from models import Gemini, Pyannote
from services.embed import EmbedService
from services.llm import LLMService
from services.rt_diarization import RTDiarizationService
from usecase.diarization import DiarizationUC
from usecase.llm import LLMUC
from usecase.socket import SocketUC

from core import logger


class Container(DeclarativeContainer):
    implementation: "Container" = None
    config = providers.Configuration()
    logger = logger

    # model
    gemini = providers.Singleton(
        Gemini,
        GOOGLE_API_KEY=config.api.google_key,
    )

    pyannote = providers.Singleton(
        Pyannote,
        hf_token=config.api.hf_token,
    )

    # service
    embed_service = providers.Singleton(
        EmbedService,
        pyannote=pyannote,
    )

    llm_service = providers.Resource(
        LLMService,
        logger=logger,
        MAX_STORAGE_SIZE=config.service.llm.max_storage_size,
        MAX_CACHE_SIZE=config.service.llm.max_cache_size,
    )

    rt_diarization_service = providers.Resource(
        RTDiarizationService,
        logger=logger,
        NUM_CONSUMERS=config.service.rt_diarization.num_consumers,
        MAX_QUEUE_SIZE=config.service.rt_diarization.max_queue_size,
        MAX_STORAGE_SIZE=config.service.rt_diarization.max_storage_size,
        MIN_AUDIO_DURATION=config.service.rt_diarization.min_audio_duration,
        SAMPLE_RATE=config.service.sample_rate,
    )

    # usecase
    diarization_uc = providers.Singleton(
        DiarizationUC,
        embed_service=embed_service,
        rt_diarization_service=rt_diarization_service,
        llm_service=llm_service,
        SAMPLE_RATE=config.service.sample_rate,
    )

    llm_uc = providers.Singleton(
        LLMUC,
        llm_service=llm_service,
    )

    socket_uc = providers.Singleton(
        SocketUC,
        logger=logger,
        llm_service=llm_service,
        rt_diarization_service=rt_diarization_service,
        MAX_CONNECTIONS=config.service.socket.max_connections,
        MAX_BUFFER_SIZE=config.service.socket.max_buffer_size,
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if Container.implementation is not None:
            raise Exception(
                f" container is a singleton class. Use Container.get_instance() instead."
            )

    @staticmethod
    async def init_all():
        if Container.implementation is None:
            raise Exception(
                "Container is not initialized. Use Container.get_instance() first."
            )

        # TODO 메인 프로세서가 안쓰는 것도 컨테이너가 초기화 한다. 이는 문제가 있음.
        # 각 프로세서가 초기화 하는 것으로 변경 필요. 즉 Container도 분리
        for namer, provider in Container.implementation.providers.items():
            if isinstance(provider, providers.Resource):
                init = provider.init()
                if inspect.iscoroutine(init):
                    await provider.init()
            provider()

    @staticmethod
    async def shutdown_resources():
        if Container.implementation is None:
            raise Exception(
                "Container is not initialized. Use Container.get_instance() first."
            )
        await Container.implementation.shutdown_resources()

    @staticmethod
    def get_instance(*args, **kwargs) -> "Container":
        if Container.implementation is None:
            Container.implementation = Container(*args, **kwargs)
        return Container.implementation
