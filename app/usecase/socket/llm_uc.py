import asyncio
from typing import Any
from fastapi import WebSocket
from core import logger
from services.llm import LLMInput, LLMOutput, LLMService
from services.rt_diarization import RTDiarizationOutput
from services.llm.dto.flag import *

from .diarization_uc import DiarizationUC
from .dto import Metadata
from .dto.flag import *


class LLMUC(DiarizationUC):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.llm_service = None
        self.__callbacks = {}

    async def init(self):
        await super().init()
        self.llm_service = LLMService.get_instance()
        await asyncio.gather(*self.llm_service.init())
        await asyncio.gather(*self.llm_service.run())
        self.__callbacks = {}

    # override
    async def _run(
        self, web_socket: WebSocket, sid: Any, storage: dict, metadata: Metadata
    ) -> bool:
        if await super()._run(web_socket, sid, storage, metadata):
            return True

        if metadata.flag == METADATA:
            llm_input = LLMInput(
                uuid=sid,
                group_id=metadata.group_id,
                mode=UPDATE,
                agenda=metadata.metadata["agenda"],
                num_people=metadata.metadata["num_people"],
                meeting_topic=metadata.metadata["meeting_topic"],
            )
            await self.llm_service.request(llm_input)
            logger.debug(f"llm register metadata")
        elif metadata.flag == CONTEXT:
            await self.llm_service.request(
                LLMInput(
                    uuid=sid,
                    group_id=metadata.group_id,
                    mode=REQUEST,
                )
            )
            logger.debug(f"llm register context")
        elif metadata.flag == CONTEXT_DONE:
            await self.llm_service.request(
                LLMInput(
                    uuid=sid,
                    group_id=metadata.group_id,
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
                            [f"{s.user_id}: {s.sentence.text}" for s in Y.completed]
                        ),
                    )
                )
            await dsp(Y)

        return llm_register

    def _llm_sending_process(self, web_socket: WebSocket, sid: Any):
        async def llm_sending_process(Y: LLMOutput):
            if Y.uuid == sid:
                await web_socket.send_bytes(
                    self._dumps(
                        {
                            "group_id": Y.group_id,
                            "context": Y.context,
                            "agenda": Y.agenda,
                            "feedback": Y.feedback,
                        }
                    )
                )

        return llm_sending_process

    # override
    async def disconnect(self, web_socket: WebSocket, sid: Any):
        await super().disconnect(web_socket, sid)
        if sid in self.__callbacks:
            callback = self.__callbacks.pop(sid)
            await self.llm_service.remove_callback(sid)

    # override
    async def _transceive(self, web_socket: WebSocket, sid: Any):
        callback = self._llm_sending_process(web_socket, sid)
        self.__callbacks[sid] = callback
        await self.llm_service.add_callback(sid, callback)

        await super()._transceive(web_socket, sid)

    # override
    async def close(self):
        await self.llm_service.close()
        super().close()
