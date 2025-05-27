from core import Singleton
from dto.request import LLMContextRequest, LLMMetadataRequest
from dto.response import LLMResponse
from services.llm import LLMInput, LLMService
from services.llm.dto.flag import REQUEST, UPDATE, DONE


class LLMUC(Singleton):
    @LLMService.object
    def __init__(self, llm_service: LLMService):
        super().__init__()
        self.llm_service = llm_service

    async def metadata(self, llm_metadata_request: LLMMetadataRequest):
        await self.llm_service.request(
            LLMInput(
                group_id=llm_metadata_request.group_id,
                mode=UPDATE,
                agenda=llm_metadata_request.agenda,
                num_people=llm_metadata_request.num_people,
                meeting_topic=llm_metadata_request.meeting_topic,
            )
        )

    async def context(self, llm_context_request: LLMContextRequest):
        return LLMResponse.from_llm_output(
            await self.llm_service.request(
                LLMInput(group_id=llm_context_request.group_id, mode=REQUEST)
            )
        )

    async def context_done(self, llm_context_request: LLMContextRequest):
        return LLMResponse.from_llm_output(
            await self.llm_service.request(
                LLMInput(group_id=llm_context_request.group_id, mode=DONE)
            )
        )
