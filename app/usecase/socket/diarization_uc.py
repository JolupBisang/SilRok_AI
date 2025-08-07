from __future__ import annotations
from typing import TYPE_CHECKING

from typing import Callable
from fastapi import WebSocket
from fastapi.websockets import WebSocketState

from util import LRUDict
from dto.response import DiarizationResponse, DiarizationEmbedResponse, ErrorResponse

from usecase.socket.a_socket_uc import ASocketUC
from usecase.socket.dto import DiarizationMetadata, Metadata
from usecase.socket.dto.flag import *

if TYPE_CHECKING:
    from services.embed import EmbedService, EmbedInput, EmbedOutput
    from services.rt_diarization import (
        RTDiarizationService,
        RTDiarizationInput,
        RTDiarizationOutput
    )


class DiarizationUC(ASocketUC):
    def __init__(
        self,
        *args,
        rt_diarization_service: RTDiarizationService,
        embed_service: EmbedService,
        MAX_BUFFER_SIZE: int,
        **kwargs,
    ):
        # if not isinstance(rt_diarization_service, RTDiarizationService):
        #     raise TypeError(
        #         "rt_diarization_service must be an instance of RTDiarizationService"
        #     )
        # if not isinstance(embed_service, EmbedService):
        #     raise TypeError("embed_service must be an instance of EmbedService")
        if not isinstance(MAX_BUFFER_SIZE, int) or MAX_BUFFER_SIZE <= 1:
            raise ValueError(
                "MAX_BUFFER_SIZE must be a positive integer greater than 1"
            )

        super().__init__(*args, **kwargs)
        self.rt_diarization_service = rt_diarization_service
        self.embed_service = embed_service
        self.__callbacks: dict[str, Callable[[EmbedOutput], None]] = {}
        self.__storage: dict[str, LRUDict] = {}

        self.__MAX_BUFFER_SIZE = MAX_BUFFER_SIZE

    def _storage_init(self, sid: str, metadata: DiarizationMetadata):
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

        dm = DiarizationMetadata.from_metadata(metadata)

        if flag == DIARIZATION_EMBED:
            self.embed_service.request_with_callback(
                dm.to_embed_input(),
                self.__callbacks[sid]
            )
            return True
        else:
            group_id = dm.group_id
            storage = self.__storage[sid]
            if group_id not in storage:
                self._storage_init(sid, dm)
            if flag == DIARIZATION_REFER:
                storage[group_id]["refer"] = dm.to_refer()
                storage[group_id]["users"].clear()
                self.logger.debug(f"diarization register refer")
                return True
            elif flag == DIARIZATION:
                user_id = dm.user_id
                refer = {}
                if user_id not in storage[group_id]["users"]:
                    refer = storage[group_id]["refer"]
                    storage[group_id]["users"].add(user_id)
                await self.rt_diarization_service.request(
                    dm.to_rt_diarization_input(sid, refer)
                )
                self.logger.debug(f"diarization service")
                return True
        return False

    def _diarization_sending_process(self, web_socket: WebSocket, sid: str):
        async def diarization_sending_process(
            Y: RTDiarizationOutput | None, e: Exception | None
        ):
            if web_socket.client_state != WebSocketState.CONNECTED:
                self.logger.debug(
                    f"WebSocket {sid} is not connected, skipping sending response."
                )
                return
            if Y is not None:
                self.logger.info(
                    f"completed: {[(speak.sentence.order, speak.sentence.text) for speak in Y.completed]}\n-candidate: {[(speak.sentence.order, speak.sentence.text) for speak in Y.candidate]}"
                )
                await web_socket.send_bytes(
                    DiarizationResponse.from_rt_diarization_output(Y).to_bytes(
                        self._pack_func[sid]["dumps"]
                    )
                )
            # await web_socket.send_bytes(
            #     DiarizationResponse.from_rt_diarization_output(Y).to_bytes(
            #         self._pack_func[sid]["dumps"]
            #     )
            #     if e is None
            #     else ErrorResponse(error=str(e)).to_bytes(self._pack_func[sid]["dumps"])
            # )

        return diarization_sending_process

    def _embed_sending_process(self, web_socket: WebSocket, sid: str):
        async def llm_sending_process(Y: EmbedOutput | None, e: Exception | None):
            if web_socket.client_state != WebSocketState.CONNECTED:
                self.logger.debug(
                    f"WebSocket {sid} is not connected, skipping sending response."
                )
                return
            if Y is not None:
                await web_socket.send_bytes(
                    DiarizationEmbedResponse.from_embed_output(Y).to_bytes(
                        self._pack_func[sid]["dumps"]
                    )
                )
            # await web_socket.send_bytes(
            #     DiarizationEmbedResponse.from_embed_output(Y).to_bytes(
            #         self._pack_func[sid]["dumps"]
            #     )
            #     if e is None
            #     else ErrorResponse(error=str(e)).to_bytes(self._pack_func[sid]["dumps"])
            # )

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
