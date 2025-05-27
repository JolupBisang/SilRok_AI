from typing import Any, Callable
from fastapi import WebSocket
from core import logger
from dto.response.llm_response import LLMResponse
from services.rt_diarization import RTDiarizationOutput
from services.llm import LLMInput, LLMOutput, LLMService
from services.llm.dto.flag import *

from .diarization_uc import DiarizationUC
from .dto import LLMMetadata, Metadata
from .dto.flag import *


class LLMUC(DiarizationUC):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.llm_service = LLMService.get_instance()
        self.__callbacks: dict[str, Callable[[LLMOutput], None]] = {}

    def __request_update(
        self, Y: RTDiarizationOutput, callback: Callable[[LLMOutput], None]
    ):
        self.llm_service.request_with_callback(
            LLMInput(
                group_id=Y.group_id,
                mode=UPDATE,
                conversation="\n".join(
                    f"{s.user_id}: {s.sentence.text}" for s in Y.completed
                ),
            ),
            callback,
        )

    def __request_metadata(
        self, llm_metadata: LLMMetadata, callback: Callable[[LLMOutput], None]
    ):
        self.llm_service.request_with_callback(
            LLMInput(
                group_id=llm_metadata.group_id,
                mode=UPDATE,
                agenda=llm_metadata.agenda,
                num_people=llm_metadata.num_people,
                meeting_topic=llm_metadata.meeting_topic,
            ),
            callback,
        )

    def __request_context(
        self, llm_metadata: LLMMetadata, callback: Callable[[LLMOutput], None]
    ):
        self.llm_service.request_with_callback(
            LLMInput(
                group_id=llm_metadata.group_id,
                mode=REQUEST,
            ),
            callback,
        )

    def __request_context_done(
        self, llm_metadata: LLMMetadata, callback: Callable[[LLMOutput], None]
    ):
        self.llm_service.request_with_callback(
            LLMInput(
                group_id=llm_metadata.group_id,
                mode=DONE,
            ),
            callback,
        )

    # override
    async def _run(
        self, web_socket: WebSocket, sid: Any, storage: dict, metadata: Metadata
    ) -> bool:
        if await super()._run(web_socket, sid, storage, metadata):
            return True
        flag = metadata.flag
        if flag not in LLM_FLAGS:
            return False

        llm_metadata = LLMMetadata.from_metadata(metadata)

        if flag == METADATA:
            self.__request_metadata(llm_metadata, self.__callbacks[sid])
            logger.debug(f"{sid}: llm register metadata")
        elif flag == CONTEXT:
            self.__request_context(llm_metadata, self.__callbacks[sid])
            logger.debug(f"{sid}: llm register context")
        elif flag == CONTEXT_DONE:
            self.__request_context_done(llm_metadata, self.__callbacks[sid])
            logger.debug(f"{sid}: llm register context done")

        return True

    # override
    def _diarization_sending_process(self, web_socket: WebSocket, sid: Any):
        dsp = super()._diarization_sending_process(web_socket, sid)

        async def llm_register(Y: RTDiarizationOutput):
            if Y.uuid == sid and Y.completed:
                self.__request_update(Y, self.__callbacks[sid])
            await dsp(Y)

        return llm_register

    def _llm_sending_process(self, web_socket: WebSocket, sid: Any):
        async def llm_sending_process(Y: LLMOutput):
            await web_socket.send_bytes(
                self._pack_func[sid]["dumps"](
                    LLMResponse.from_llm_output(Y).model_dump()
                )
            )

        return llm_sending_process

    # override
    async def disconnect(self, web_socket: WebSocket, sid: str):
        await super().disconnect(web_socket, sid)
        if sid in self.__callbacks:
            del self.__callbacks[sid]

    # override
    async def _transceive(self, web_socket: WebSocket, sid: str):
        self.__callbacks[sid] = self._llm_sending_process(web_socket, sid)
        await super()._transceive(web_socket, sid)

    # override
    async def close(self):
        await self.llm_service.close()
        super().close()
