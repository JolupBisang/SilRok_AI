import asyncio
from services.LLM import LLMService
from services import ThreadManagerService
from services.LLM.dto import LLMContext

from .dto import Metadata, AlignedRedisContext


class LLMSub:
    @LLMService.object
    @ThreadManagerService.object
    def __init__(
        self,
        llm_service: LLMService,
        thread_manager_service: ThreadManagerService,
    ):
        self.llm_service = llm_service
        self.thread_manager_service = thread_manager_service

    def service(self, llm_context: LLMContext, arc: AlignedRedisContext):
        llm_context.conversation = [f"{s.user_id}: {s.sentence.text}" for s in arc.speaks]
        self.llm_service.send_msg(llm_context)

    def async_service(
        self, llm_context: LLMContext, arc: AlignedRedisContext, callback: callable
    ):
        fut = self.thread_manager_service.submit_to_executor(
            self.service, llm_context, arc
        )
        fut.add_done_callback(lambda _: callback(llm_context.to_dict()))

    def update(self, metadata: Metadata, llm_context: LLMContext):
        llm_context.update(
            agenda=metadata.metadata["agenda"],
            num_people=metadata.metadata["num_people"],
            meeting_topic=metadata.metadata["meeting_topic"],
        )
