from abc import ABC, abstractmethod
import asyncio
from typing import Any
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import msgpack

from core import Settings, Singleton, logger
from util import LRUDict

from .dto import Metadata


class ASocketUC(ABC, Singleton):
    def __init__(
        self,
        MAX_CONNECTIONS: int = Settings.SOCKET_UC_MAX_CONNECTIONS,
        MAX_BUFFER: int = Settings.SOCKET_UC_MAX_BUFFER,
    ):
        super().__init__()
        self.logger = None
        self.__remaining_connections = MAX_CONNECTIONS
        self.__MAX_BUFFER = MAX_BUFFER

    async def init(self):
        pass

    @abstractmethod
    async def _run(
        self, web_socket: WebSocket, sid: Any, storage: dict, metadata: Metadata
    ):
        pass

    def _dumps(self, msg: dict) -> bytes:
        return msgpack.dumps(msg)

    def _storage_init(self, storage: dict, metadata: Metadata):
        storage[metadata.group_id] = {}

    async def _transceive(self, web_socket: WebSocket, sid: Any):
        storage = LRUDict(self.__MAX_BUFFER)
        while True:
            await asyncio.sleep(0)
            byte = await web_socket.receive_bytes()
            logger.debug(f"WebSocket received")
            metadata = Metadata.from_byte(byte)

            if metadata.group_id not in storage:
                self._storage_init(storage, metadata)

            await self._run(web_socket, sid, storage, metadata)

    async def disconnect(self, web_socket: WebSocket, sid: Any):
        if web_socket.client_state == WebSocketState.CONNECTED:
            await web_socket.close()
        self.__remaining_connections += 1
        logger.info(f"WebSocket disconnected, remain {self.__remaining_connections}")

    async def add(self, web_socket: WebSocket):
        if self.__remaining_connections <= 0:
            await web_socket.close()
            logger.warning("WebSocket connection limit reached")
            return None

        self.__remaining_connections -= 1
        try:
            await web_socket.accept()
            # await asyncio.sleep(0.1)  # connection 하는 context switching
            sid = dict(web_socket.headers).get("sec-websocket-key", str(uuid.uuid4()))
            logger.info(f"WebSocket connected, remain {self.__remaining_connections}")

            await self._transceive(web_socket, sid)

        except WebSocketDisconnect:
            await self.disconnect(web_socket, sid)
            return
        except BaseException as e:
            self.__remaining_connections += 1
            await self.disconnect(web_socket, sid)
            raise e
