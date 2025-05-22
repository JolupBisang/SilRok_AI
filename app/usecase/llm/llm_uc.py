import asyncio
import uuid
from core import Singleton
from dto.request import LLMContextRequest, LLMMetadataRequest
from dto.response import LLMResponse
from services.llm_ import LLMInput, LLMOutput, LLMService
from services.llm_.dto.flag import REQUEST, UPDATE, DONE


class LLMUC(Singleton):
    @LLMService.object
    def __init__(self, llm_service: LLMService):
        super().__init__()
        self.llm_service = llm_service

    async def __request(
        self,
        group_id: str,
        mode: str,
        agenda: list[str] = None,
        num_people: int = None,
        meeting_topic: str = None,
    ):
        uid = uuid.uuid4()
        X = LLMInput(
            uuid=uid,
            group_id=group_id,
            mode=mode,
            agenda=agenda,
            num_people=num_people,
            meeting_topic=meeting_topic,
            must_return=True,
        )
        fut = asyncio.get_running_loop().create_future()

        async def callback(Y: LLMOutput):
            fut.set_result(Y)

        await self.llm_service.add_callback(uid, callback)
        await self.llm_service.request(X)
        Y = await fut
        await self.llm_service.remove_callback(uid)
        return LLMResponse.from_llm_output(Y)

    async def metadata(self, llm_metadata_request: LLMMetadataRequest):
        await self.llm_service.request(
            LLMInput(
                uuid=uuid.uuid4(),
                group_id=llm_metadata_request.group_id,
                mode=UPDATE,
                agenda=llm_metadata_request.agenda,
                num_people=llm_metadata_request.num_people,
                meeting_topic=llm_metadata_request.meeting_topic,
            )
        )

    async def context(self, llm_context_request: LLMContextRequest):
        return await self.__request(
            group_id=llm_context_request.group_id,
            mode=REQUEST,
        )

    async def context_done(self, llm_context_request: LLMContextRequest):
        return await self.__request(
            group_id=llm_context_request.group_id,
            mode=DONE,
        )
