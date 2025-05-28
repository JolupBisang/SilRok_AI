from typing import Any
from fastapi import WebSocket

from dto.response import DiarizationResponse
from services.rt_diarization import (
    RTDiarizationService,
    RTDiarizationInput,
    RTDiarizationOutput,
)

from .a_socket_uc import ASocketUC
from .dto import DiarizeMetadata, Metadata
from .dto.flag import *


class DiarizationUC(ASocketUC):
    def __init__(
        self,
        *args,
        rt_diarization_service: RTDiarizationService,
        **kwargs,
    ):
        if not isinstance(rt_diarization_service, RTDiarizationService):
            raise TypeError(
                "rt_diarization_service must be an instance of RTDiarizationService"
            )

        super().__init__(*args, **kwargs)
        self.rt_diarization_service = rt_diarization_service

    # override
    def _storage_init(self, storage: dict, metadata: Metadata):
        super()._storage_init(storage, metadata)
        storage[metadata.group_id]["refer"] = {}
        # FIXME this storage is not memory safe.
        storage[metadata.group_id]["users"] = set()

    # override
    async def _run(
        self, web_socket: WebSocket, sid: Any, storage: dict, metadata: Metadata
    ) -> bool:
        flag = metadata.flag
        if flag not in DIARIZE_FLAGS:
            return False

        diarize_metadata = DiarizeMetadata.from_metadata(metadata)
        group_id = diarize_metadata.group_id

        if flag == DIARIZATION_REFER:
            storage[group_id]["refer"] = diarize_metadata.refer(
                self._pack_func[sid]["loads"]
            )
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

    def _diarization_sending_process(self, web_socket: WebSocket, sid: Any):
        async def diarization_sending_process(Y: RTDiarizationOutput):
            await web_socket.send_bytes(
                self._pack_func[sid]["dumps"](
                    DiarizationResponse.from_rt_diarization_output(Y).model_dump()
                )
            )

        return diarization_sending_process

    # override
    async def disconnect(self, web_socket: WebSocket, sid: Any):
        await super().disconnect(web_socket, sid)
        await self.rt_diarization_service.remove_callback(sid)

    # override
    async def _transceive(self, web_socket: WebSocket, sid: Any):
        await self.rt_diarization_service.add_callback(
            sid, self._diarization_sending_process(web_socket, sid)
        )

        await super()._transceive(web_socket, sid)
