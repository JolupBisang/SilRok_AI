from typing import Callable
from fastapi import WebSocket
from dto.response import ErrorResponse, LLMContextResponse, LLMResponse
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
        llm_service: LLMService,
        **kwargs,
    ):
        if not isinstance(llm_service, LLMService):
            raise TypeError("llm_service must be an instance of LLMService")

        super().__init__(*args, **kwargs)
        self.llm_service = llm_service
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
    async def _run(self, web_socket: WebSocket, sid: str, metadata: Metadata) -> bool:
        if await super()._run(web_socket, sid, metadata):
            return True
        flag = metadata.flag
        if flag not in LLM_FLAGS:
            return False

        llm_metadata = LLMMetadata.from_metadata(metadata)

        if flag == METADATA:
            self.__request_metadata(llm_metadata, self.__callbacks[sid]["general"])
            self.logger.debug(f"{sid}: llm register metadata")
        elif flag == CONTEXT:
            self.__request_context(llm_metadata, self.__callbacks[sid]["general"])
            self.logger.debug(f"{sid}: llm register context")
        elif flag == CONTEXT_DONE:
            self.__request_context_done(llm_metadata, self.__callbacks[sid]["context"])
            self.logger.debug(f"{sid}: llm register context done")

        return True

    # override
    def _diarization_sending_process(self, web_socket: WebSocket, sid: str):
        dsp = super()._diarization_sending_process(web_socket, sid)

        async def llm_register(Y: RTDiarizationOutput | None, e: Exception | None):
            if e is not None and Y.uuid == sid and Y.completed:
                self.__request_update(Y, self.__callbacks[sid])
            await dsp(Y, e)

        return llm_register

    def _llm_sending_process(self, web_socket: WebSocket, sid: str):
        async def llm_sending_process(Y: LLMOutput | None, e: Exception | None):
            await web_socket.send_bytes(
                LLMResponse.from_llm_output(Y).to_bytes(self._pack_func[sid]["dumps"])
                if e is None
                else ErrorResponse(error=str(e)).to_bytes(self._pack_func[sid]["dumps"])
            )

        return llm_sending_process

    def _llm_context_sending_process(self, web_socket: WebSocket, sid: str):
        async def llm_context_context_sending_process(
            Y: LLMOutput | None, e: Exception | None
        ):
            await web_socket.send_bytes(
                LLMContextResponse.from_llm_output(Y).to_byte(
                    self._pack_func[sid]["dumps"]
                )
                if e is None
                else ErrorResponse(error=str(e)).to_bytes(self._pack_func[sid]["dumps"])
            )

        return llm_context_context_sending_process

    # override
    async def disconnect(self, web_socket: WebSocket, sid: str):
        await super().disconnect(web_socket, sid)
        if sid in self.__callbacks:
            del self.__callbacks[sid]

    # override
    async def _transceive(self, web_socket: WebSocket, sid: str):
        self.__callbacks[sid] = {
            "general": self._llm_sending_process(web_socket, sid),
            "context": self._llm_context_sending_process(web_socket, sid),
        }
        await super()._transceive(web_socket, sid)
