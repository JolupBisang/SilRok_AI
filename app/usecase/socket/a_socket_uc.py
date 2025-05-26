from abc import ABC, abstractmethod
import asyncio
import json
from typing import Any
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import msgpack

from core import Settings, Singleton, logger
from util import LRUDict

from .dto import Metadata

MSGPACK = "msgpack"
JSON = "json"
TYPES = [MSGPACK, JSON]

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

        self._pack_func = {}

    async def init(self):
        pass

    @abstractmethod
    async def _run(
        self, web_socket: WebSocket, sid: Any, storage: dict, metadata: Metadata
    ):
        pass

    def _storage_init(self, storage: dict, metadata: Metadata):
        storage[metadata.group_id] = {}

    async def _transceive(self, web_socket: WebSocket, sid: Any):
        storage = LRUDict(self.__MAX_BUFFER)
        while True:
            byte = await web_socket.receive_bytes()
            logger.debug(f"WebSocket received")
            metadata = Metadata.from_byte(byte, self._pack_func[sid]["loads"])

            if metadata.group_id not in storage:
                self._storage_init(storage, metadata)

            await self._run(web_socket, sid, storage, metadata)

    async def disconnect(self, web_socket: WebSocket, sid: Any):
        self.__remaining_connections += 1
        if web_socket.client_state == WebSocketState.CONNECTED:
            await web_socket.close()
        del self._pack_func[sid]
        logger.info(f"WebSocket disconnected, remain {self.__remaining_connections}")

    async def add(self, web_socket: WebSocket, type_: str = MSGPACK):
        if self.__remaining_connections <= 0:
            await web_socket.close()
            logger.warning("WebSocket connection limit reached")
            return None

        self.__remaining_connections -= 1
        try:
            await web_socket.accept()
            sid = dict(web_socket.headers).get("sec-websocket-key", str(uuid.uuid4()))
            logger.info(f"WebSocket connected, remain {self.__remaining_connections}")

            dumps, loads = self.__get_dump_func_and_load_func(type_)
            self._pack_func[sid] = {
                "dumps":dumps,
                "loads": loads
            }
            await self._transceive(web_socket, sid)

        except WebSocketDisconnect:
            return await self.disconnect(web_socket, sid)
        except BaseException as e:
            await self.disconnect(web_socket, sid)
            raise e

    def __get_dump_func_and_load_func(self, type_: str):
        if type_ == MSGPACK:
            return msgpack.dumps, msgpack.loads
        elif type_ == JSON:
            return (
                lambda x:json.dumps(x).encode("utf-8"),
                lambda x:json.loads(x.decode("utf-8"))
            )
        else:
            raise ValueError(f"Unknown type: {type_}")
