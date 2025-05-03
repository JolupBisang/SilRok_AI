from asyncio import Queue
import asyncio
from logging import Logger
from fastapi.websockets import WebSocketState
import msgpack
from fastapi import WebSocket, WebSocketDisconnect

from ServerObject import ServerObject
from core import settings
from services.LLM.dto import LLMContext
from services.asr.dto import ASRContext
from services.diarization.dto import DiarizationContext
from services import LoggerService
from services.diarization.dto.Speak import Speak
from services.redis import RedisService
from usecase.socket.dto import AlignedRedisContext, SpeakRedisContext
from util import LRUDict

from .ASRSub import ASRSub
from .LLMSub import LLMSub
from .DiarizationSub import DiarizationSub

from .dto import Metadata
from .dto.flag import *


class SocketUC(ServerObject):

    @RedisService.object
    def __init__(
        self,
        redis_service: RedisService,
        MAX_CONNECTIONS: int = settings.SOCKET_UC_MAX_CONNECTIONS,
        MAX_BUFFER: int = settings.SOCKET_UC_MAX_BUFFER,
        MAX_SPEAKS: int = settings.SOCKET_UC_MAX_SPEAKS,
        MAX_ALIGNED: int = settings.SOCKET_UC_MAX_ALIGNED,
    ):
        super().__init__()
        self.redis_service = redis_service

        self.asr = ASRSub()
        self.diarization = DiarizationSub()
        self.llm = LLMSub()

        self.__remaining_connections = MAX_CONNECTIONS
        self.__MAX_BUFFER = MAX_BUFFER
        self.__MAX_SPEAKS = MAX_SPEAKS
        self.__MAX_ALIGNED = MAX_ALIGNED

    # NOTE 공통 사항이 많지만, 너무 짧아서 따로 빼지 않음
    async def __update_aligned(self, metadata: dict):
        await self.__pop_speaks(metadata)
        self.__aligned(metadata)
        src: AlignedRedisContext = metadata["aligned"]
        src.speaks = metadata["speaks"].speaks
        await self.redis_service.append(src)
        # NOTE 이건 쓰레드 공유가 되야하지만, 현재로써는 보류
        metadata["n_aligned"] += 1

    async def __pop_aligned(self, metadata: dict):
        src: AlignedRedisContext = metadata["aligned"]
        await self.redis_service.pop(src)
        metadata["n_aligned"] = 0

    async def __update_speaks(self, metadata: dict, dc: DiarizationContext):
        src: SpeakRedisContext = metadata["speaks"]
        src.speaks = dc.completed
        await self.redis_service.append(src)
        # NOTE 이건 쓰레드 공유가 되야하지만, 현재로써는 보류
        metadata["n_speaks"] += 1

    async def __pop_speaks(self, metadata: dict):
        src: SpeakRedisContext = metadata["speaks"]
        await self.redis_service.pop(src)
        metadata["n_speaks"] = 0

    def __aligned(self, metadata: dict, boundary: int = 2):
        arc: SpeakRedisContext = metadata["speaks"]
        speaks: list[Speak] = arc.speaks
        speaks.sort(key=lambda x: x.sentence.tokens[0].start)

        # TODO  제대로된 정렬 및 선택 알고리즘 필요
        speaks_groups = [[speaks[0]]]
        cnt_idx = 0
        for speak in speaks[1:]:
            similarities = []
            for i in range(
                max(0, cnt_idx - boundary), min(cnt_idx + boundary, len(speaks_groups))
            ):
                similarities.append((i, speaks_groups[i][-1].similar(speak)))
            max_arg = max(range(len(similarities)), key=lambda x: similarities[x][1])
            if similarities[max_arg][1] < 0.5:
                speaks_groups.append([speak])
                cnt_idx += 1
            else:
                speaks_groups[max_arg].append(speak)

        speaks = [max(sg, key=lambda x: x.similarity) for sg in speaks_groups]
        arc.speaks = speaks

    async def __receiving_loop(self, web_socket: WebSocket, queue: Queue):
        metadata_dict = LRUDict(self.__MAX_BUFFER)
        response = None
        while True:
            metadata = Metadata.from_byte(await web_socket.receive_bytes())
            group_id = metadata.group_id
            user_id = metadata.user_id
            flag = metadata.flag

            if group_id not in metadata_dict:
                metadata_dict[group_id] = {
                    "llm": LLMContext(),
                    "speaks": SpeakRedisContext(group_id=group_id),
                    "aligned": AlignedRedisContext(group_id=group_id),
                    "n_speaks": 0,
                    "n_aligned": 0,
                }
            if user_id not in metadata_dict[group_id]:
                metadata_dict[group_id][user_id] = {
                    ASR: ASRContext(),
                    DIARIZED: DiarizationContext(user_id),
                }

            gdt = metadata_dict[group_id]
            dt = metadata_dict[group_id][user_id]

            if flag in DATA_IS_REFER:
                dt[DIARIZED] = self.diarization.get_diarization_context(metadata)
                continue
            if flag in DATA_IS_METADATA:
                self.llm.update(metadata, gdt["llm"])
                continue
            if flag in DATA_IS_AUDIO:
                response = await self.asr.service(metadata, dt[ASR])
                if flag == DIARIZED or flag == DIARIZED_DONE:
                    ac = dt[ASR]
                    dc = dt[DIARIZED]
                    response = await self.diarization.service(
                        metadata, ac.completed, ac.candidate, dc
                    )
                    if dc.completed:
                        await self.__update_speaks(gdt, dc)
                        dc.completed = []
            elif flag == CONTEXT or flag == CONTEXT_DONE:
                await self.__pop_aligned(gdt)
                self.llm.async_service(
                    gdt["llm"], gdt["aligned"], lambda x: queue.put_nowait(x)
                )

            # 아래 과정들 자체도 비동기적으로 처리해야 함
            if gdt["n_speaks"] >= self.__MAX_SPEAKS:
                await self.__update_aligned(gdt)

            if gdt["n_aligned"] >= self.__MAX_ALIGNED:
                await self.__pop_aligned(gdt)
                self.llm.async_service(gdt["llm"], gdt["aligned"], lambda _: None)

            if response is not None:
                await queue.put(response)

            if flag == ASR_DONE or flag == DIARIZED_DONE:
                await queue.put(DONE)
                return

    async def __sending_loop(self, web_socket: WebSocket, queue: Queue):
        while True:
            msg = await queue.get()
            if msg == DONE:
                return
            await web_socket.send_bytes(msgpack.packb(msg, use_bin_type=True))

    @LoggerService.object
    async def add(self, web_socket: WebSocket, logger_service: Logger):
        try:
            if self.__remaining_connections <= 0:
                await web_socket.close()
                logger_service.warning("WebSocket connection limit reached")
                return
            await web_socket.accept()
            self.__remaining_connections -= 1
            logger_service.info(
                f"WebSocket connected, remain {self.__remaining_connections}"
            )

            queue = Queue()

            await asyncio.gather(
                self.__receiving_loop(web_socket, queue),
                self.__sending_loop(web_socket, queue),
            )

            logger_service.info(f"ASR Done")
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger_service.error(f"WebSocket error: {e}")
            if web_socket.client_state == WebSocketState.CONNECTED:
                logger_service.info(
                    f"WebSocket disconnected, remain {self.__remaining_connections}"
                )
                await web_socket.close()
            self.__remaining_connections += 1
            raise e
        finally:
            if web_socket.client_state == WebSocketState.CONNECTED:
                logger_service.info(
                    f"WebSocket disconnected, remain {self.__remaining_connections}"
                )
                await web_socket.close()
            self.__remaining_connections += 1
