import asyncio
from typing import Any
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
        self.llm_service = None

    async def init(self):
        await super().init()
        self.llm_service = LLMService.get_instance()
        await asyncio.gather(*self.llm_service.init())
        await asyncio.gather(*self.llm_service.run())

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
            await self.llm_service.request(
                LLMInput(
                    uuid=sid,
                    group_id=llm_metadata.group_id,
                    mode=UPDATE,
                    agenda=llm_metadata.agenda,
                    num_people=llm_metadata.num_people,
                    meeting_topic=llm_metadata.meeting_topic,
                )
            )
            logger.debug(f"llm register metadata")
        elif flag == CONTEXT:
            await self.llm_service.request(
                LLMInput(
                    uuid=sid,
                    group_id=llm_metadata.group_id,
                    mode=REQUEST,
                )
            )
            logger.debug(f"llm register context")
        elif flag == CONTEXT_DONE:
            await self.llm_service.request(
                LLMInput(
                    uuid=sid,
                    group_id=llm_metadata.group_id,
                    mode=DONE,
                )
            )
            logger.debug(f"llm register context done")

        return True

    # override
    def _diarization_sending_process(self, web_socket: WebSocket, sid: Any):
        dsp = super()._diarization_sending_process(web_socket, sid)

        async def llm_register(Y: RTDiarizationOutput):
            if Y.uuid == sid and Y.completed:
                await self.llm_service.request(
                    LLMInput(
                        uuid=Y.uuid,
                        group_id=Y.group_id,
                        mode=UPDATE,
                        conversation="\n".join(
                            f"{s.user_id}: {s.sentence.text}" for s in Y.completed
                        ),
                    )
                )
            await dsp(Y)

        return llm_register

    def _llm_sending_process(self, web_socket: WebSocket, sid: Any):
        async def llm_sending_process(Y: LLMOutput):
            if Y.uuid == sid:
                await web_socket.send_bytes(
                    self._pack_func[sid]["dumps"](
                        LLMResponse.from_llm_output(Y).model_dump()
                    )
                )

        return llm_sending_process

    # override
    async def disconnect(self, web_socket: WebSocket, sid: Any):
        await super().disconnect(web_socket, sid)
        await self.llm_service.remove_callback(sid)

    # override
    async def _transceive(self, web_socket: WebSocket, sid: Any):
        await self.llm_service.add_callback(
            sid, self._llm_sending_process(web_socket, sid)
        )

        await super()._transceive(web_socket, sid)

    # override
    async def close(self):
        await self.llm_service.close()
        super().close()
