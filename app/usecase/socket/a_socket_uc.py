from abc import ABC, abstractmethod
import json
from logging import Logger
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import msgpack

from dto.response import ErrorResponse

from .dto import Metadata

MSGPACK = "msgpack"
JSON = "json"
TYPES = [MSGPACK, JSON]


class ASocketUC(ABC):
    def __init__(
        self,
        logger: Logger,
        MAX_CONNECTIONS: int,
    ):
        if not isinstance(logger, Logger):
            raise TypeError("logger must be an instance of logging.Logger")
        if not isinstance(MAX_CONNECTIONS, int) or MAX_CONNECTIONS <= 0:
            raise ValueError("MAX_CONNECTIONS must be a positive integer")

        super().__init__()
        self.logger = logger
        self.__remaining_connections = MAX_CONNECTIONS

        self._pack_func = {}

    @abstractmethod
    async def _run(self, web_socket: WebSocket, sid: str, metadata: Metadata):
        pass

    async def _transceive(self, web_socket: WebSocket, sid: str):
        while True:
            try:
                byte = await web_socket.receive_bytes()
                self.logger.debug(f"WebSocket received")
                metadata = Metadata.from_byte(byte, self._pack_func[sid]["loads"])

                await self._run(web_socket, sid, metadata)
            except Exception as e:
                web_socket.send_bytes(
                    self._pack_func[sid]["dumps"](ErrorResponse(str(e)))
                )

    async def disconnect(self, web_socket: WebSocket, sid: str):
        self.__remaining_connections += 1
        if web_socket.client_state == WebSocketState.CONNECTED:
            await web_socket.close()
        del self._pack_func[sid]
        self.logger.info(
            f"WebSocket disconnected, remain {self.__remaining_connections}"
        )

    async def add(self, web_socket: WebSocket, type_: str = MSGPACK):
        if self.__remaining_connections <= 0:
            await web_socket.close()
            self.logger.warning("WebSocket connection limit reached")
            return None

        self.__remaining_connections -= 1
        try:
            await web_socket.accept()
            sid = dict(web_socket.headers).get("sec-websocket-key", str(uuid.uuid4()))
            self.logger.info(
                f"WebSocket connected, remain {self.__remaining_connections}"
            )

            dumps, loads = self.__get_dump_func_and_load_func(type_)
            self._pack_func[sid] = {"dumps": dumps, "loads": loads}
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
                lambda x: json.dumps(x).encode("utf-8"),
                lambda x: json.loads(x.decode("utf-8")),
            )
        else:
            raise ValueError(f"Unknown type: {type_}")
