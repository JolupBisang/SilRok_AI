from fastapi import APIRouter, Depends, WebSocket
from dependency_injector.wiring import inject, Provide

from container import Container
from usecase.socket import SocketUC
from usecase.socket import TYPES, MSGPACK


router = APIRouter()


@router.websocket("/ws")
@inject
async def websocket(
    websocket: WebSocket, socket_uc: SocketUC = Depends(Provide[Container.socket_uc])
):
    await socket_uc.add(websocket)


@router.websocket("/ws/{type_}")
@inject
async def socket(
    websocket: WebSocket,
    type_: str,
    socket_uc: SocketUC = Depends(Provide[Container.socket_uc]),
):
    if type_ not in TYPES:
        type_ = MSGPACK
    await socket_uc.add(websocket, type_)
