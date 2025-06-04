from typing import Callable
from fastapi import WebSocket

from dto.response import DiarizationResponse, DiarizationEmbedResponse, ErrorResponse
from services.embed import EmbedInput, EmbedOutput, EmbedService
from services.rt_diarization import (
    RTDiarizationService,
    RTDiarizationInput,
    RTDiarizationOutput,
)
from util import LRUDict

from .a_socket_uc import ASocketUC
from .dto import DiarizeMetadata, Metadata
from .dto.flag import *


class DiarizationUC(ASocketUC):
    def __init__(
        self,
        *args,
        rt_diarization_service: RTDiarizationService,
        embed_service: EmbedService,
        SAMPLE_RATE: int,
        MAX_BUFFER_SIZE: int,
        **kwargs,
    ):
        if not isinstance(rt_diarization_service, RTDiarizationService):
            raise TypeError(
                "rt_diarization_service must be an instance of RTDiarizationService"
            )
        if not isinstance(embed_service, EmbedService):
            raise TypeError("embed_service must be an instance of EmbedService")
        if not isinstance(MAX_BUFFER_SIZE, int) or MAX_BUFFER_SIZE <= 1:
            raise ValueError(
                "MAX_BUFFER_SIZE must be a positive integer greater than 1"
            )

        super().__init__(*args, **kwargs)
        self.rt_diarization_service = rt_diarization_service
        self.embed_service = embed_service
        self.__callbacks: dict[str, Callable[[EmbedOutput], None]] = {}
        self.__storage: dict[str, LRUDict] = {}

        self.__SAMPLE_RATE = SAMPLE_RATE
        self.__MAX_BUFFER_SIZE = MAX_BUFFER_SIZE

    def _storage_init(self, sid: str, metadata: DiarizeMetadata):
        # FIXME this storage is not memory safe.
        self.__storage[sid][metadata.group_id] = {
            "refer": {},
            "users": set(),
        }

    # override
    async def _run(self, web_socket: WebSocket, sid: str, metadata: Metadata) -> bool:
        flag = metadata.flag
        if flag not in DIARIZE_FLAGS:
            return False

        diarize_metadata = DiarizeMetadata.from_metadata(metadata)

        if flag == DIARIZATION_EMBED:
            self.embed_service.request_with_callback(
                EmbedInput(
                    user_id=diarize_metadata.user_id,
                    audio=diarize_metadata.audio,
                    sample_rate=self.__SAMPLE_RATE,
                ),
                self.__callbacks[sid],
            )
            return True
        else:
            group_id = diarize_metadata.group_id
            storage = self.__storage[sid]
            if group_id not in storage:
                self._storage_init(sid, diarize_metadata)

            if flag == DIARIZATION_REFER:
                storage[group_id]["refer"] = diarize_metadata.refer()
                storage[group_id]["users"].clear()
                self.logger.debug(f"diarization register refer")
                return True
            elif flag == DIARIZATION:
                user_id = diarize_metadata.user_id
                refer = {}
                if user_id not in storage[group_id]["users"]:
                    refer = storage[group_id]["refer"]
                    storage[group_id]["users"].add(user_id)
                await self.rt_diarization_service.request(
                    RTDiarizationInput(
                        uuid=sid,
                        audio=diarize_metadata.audio,
                        group_id=diarize_metadata.group_id,
                        user_id=diarize_metadata.user_id,
                        refer_dict=refer,
                        sc_offset=diarize_metadata.sc_offset,
                    )
                )
                self.logger.debug(f"diarization service")
                return True
        return False

    def _diarization_sending_process(self, web_socket: WebSocket, sid: str):
        async def diarization_sending_process(
            Y: RTDiarizationOutput | None, e: Exception | None
        ):
            await web_socket.send_bytes(
                DiarizationResponse.from_rt_diarization_output(Y).to_bytes(
                    self._pack_func[sid]["dumps"]
                )
                if e is None
                else ErrorResponse(error=str(e)).to_bytes(self._pack_func[sid]["dumps"])
            )

        return diarization_sending_process

    def _embed_sending_process(self, web_socket: WebSocket, sid: str):
        async def llm_sending_process(Y: EmbedOutput | None, e: Exception | None):
            await web_socket.send_bytes(
                DiarizationEmbedResponse.from_embed_output(Y).to_bytes(
                    self._pack_func[sid]["dumps"]
                )
                if e is None
                else ErrorResponse(error=str(e)).to_bytes(self._pack_func[sid]["dumps"])
            )

        return llm_sending_process

    # override
    async def disconnect(self, web_socket: WebSocket, sid: str):
        await super().disconnect(web_socket, sid)
        await self.rt_diarization_service.remove_callback(sid)
        if sid in self.__callbacks:
            del self.__callbacks[sid]
        del self.__storage[sid]

    # override
    async def _transceive(self, web_socket: WebSocket, sid: str):
        self.__storage[sid] = LRUDict(self.__MAX_BUFFER_SIZE)
        self.__callbacks[sid] = self._embed_sending_process(web_socket, sid)
        await self.rt_diarization_service.add_callback(
            sid, self._diarization_sending_process(web_socket, sid)
        )
        await super()._transceive(web_socket, sid)
