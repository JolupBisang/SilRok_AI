from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from core import Config
from models import Gemini, Pyannote
from services.embed import EmbedService
from services.llm import LLMService
from services.rt_diarization import RTDiarizationService
from usecase.diarization import DiarizationUC
from usecase.llm import LLMUC
from usecase.socket import SocketUC
from core import logger

from .container_manager import ContainerManager


class Container(DeclarativeContainer):
    manager: ContainerManager = None
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
        if Container.manager is not None:
            raise Exception(
                f"MainContainer is a singleton class. Use MainContainer.get_manager() instead."
            )

    @staticmethod
    def get_manager(*args, **kwargs):
        if Container.manager is None:
            container = Container(*args, **kwargs)
            container.config.update(Config.get_instance().dict)
            Container.manager = ContainerManager(container)
        return Container.manager
