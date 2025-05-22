
from fastapi import APIRouter, WebSocket

from usecase.socket import SocketUC
from usecase.socket import TYPES, MSGPACK


router = APIRouter()

@router.websocket("/ws")
async def websocket(websocket: WebSocket):
    await SocketUC.get_instance().add(websocket)


@router.websocket("/ws/{type_}")
async def socket(websocket: WebSocket, type_: str):
    if type_ not in TYPES:
        type_ = MSGPACK
    await SocketUC.get_instance().add(websocket, type_)
