import asyncio
from asyncio import Queue, get_running_loop
import logging
from typing import Any
from google.generativeai import ChatSession
import ray

from core import Settings
from util import LRUDict

from .dto import LLMContext, LLMInput, LLMOutput
from .dto.flag import UPDATE


@ray.remote(num_cpus=1)
class LLM:
    def __init__(
        self,
        # 만약, Diarization 의 멀티프로세서 개수가 많아지면 문제 생길 수 있음
        MAX_STORAGE_SIZE: int = Settings.MAX_STORAGE_SIZE,
        MAX_CACHE_SIZE: int = Settings.MAX_CACHE_SIZE,
    ):
        self.gemini = None
        self.logger = None

        self.__storage = None
        self.__queue = None
        self.__result = None

        self.__task = None

        self.__MAX_STORAGE_SIZE = MAX_STORAGE_SIZE
        self.__MAX_CACHE_SIZE = MAX_CACHE_SIZE

    def init(
        self,
    ):
        from models import Gemini
        from core import logging_manager

        self.gemini = Gemini.get_instance()
        self.logger = logging_manager.generate("llm", logging.INFO)

        self.__storage = LRUDict(self.__MAX_STORAGE_SIZE)
        self.__queue = Queue(maxsize=self.__MAX_STORAGE_SIZE)
        self.__result = Queue(maxsize=self.__MAX_STORAGE_SIZE)
        self.__semaphore = asyncio.Semaphore(self.__MAX_STORAGE_SIZE)

        self.__task = None

        self.__MAX_CACHE_SIZE = self.__MAX_CACHE_SIZE

    def run(self):
        if self.__task is not None:
            raise RuntimeError("LLM is already running")
        self.__task = get_running_loop().create_task(self.__run())

    async def __run(self):
        self.logger.info("LLM consumer started")
        try:
            while True:
                X: LLMInput = await self.__queue.get()
                if X == "END":
                    break
                self.logger.debug(f"LLM X received")

                if X.mode == UPDATE and not X.conversation:
                    self.logger.warning("No conversation found")
                    continue

                context = self.__get_context(X)
                context.update(X)

                if (
                    context.mode == UPDATE
                    and len(context.conversation) < self.__MAX_CACHE_SIZE
                ):
                    self.logger.debug(f"Updated conversation")
                    continue

                prompt = context.get_prompt()
                context.conversation = ""

                await self.__semaphore.acquire()
                asyncio.create_task(
                    self.__process_request(
                        context.model, X.uuid, X.group_id, prompt, X.must_return
                    )
                )

                self.logger.debug(f"LLM processed")
        except BaseException as e:
            self.logger.error(f"LLM consumer error: {e}")
        self.logger.info("LLM consumer stopped")

    async def __process_request(
        self,
        model: ChatSession,
        uuid: str,
        group_id: str,
        prompt: str,
        must_return: bool,
    ):
        try:
            response = await model.send_message_async(prompt)
            self.logger.debug(f"Prompt: {prompt}")
            self.logger.debug(f"Response: {response.text}")

            Y = LLMOutput.from_context_and_response(uuid, group_id, response.text)

            if must_return or Y.context or Y.agenda or Y.feedback:
                await self.__result.put(Y)
        except Exception as e:
            self.logger.error(f"LLM processing error: {e}")
            if must_return:
                await self.__result.put(
                    LLMOutput(
                        uuid=uuid,
                        group_id=group_id,
                    )
                )
        self.__semaphore.release()

    def __get_context(self, X: LLMInput):
        group_id = X.group_id
        if group_id in self.__storage:
            return self.__storage[group_id]
        context = LLMContext(
            uuid=X.uuid, group_id=X.group_id, model=self.gemini.generate()
        )
        self.__storage[group_id] = context
        return context

    async def register(self, X: LLMInput):
        await self.__queue.put(X)

    async def get_result(self):
        return await self.__result.get()

    async def send_sig_to_result_queue(self, sig: Any):
        await self.__result.put(sig)

    async def close(self):
        await self.__queue.put("END")
        await self.__task
        ray.actor.exit_actor()
