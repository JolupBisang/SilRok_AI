from fastapi import APIRouter, Depends, WebSocket
from dependency_injector.wiring import inject, Provide

from test.containers import TestContainer
from usecase.socket import SocketUC
from usecase.socket import TYPES, MSGPACK


router = APIRouter()


@router.websocket("/ws")
@inject
async def websocket(
    websocket: WebSocket,
    socket_uc: SocketUC = Depends(Provide[TestContainer.test_socket_uc]),
):
    await socket_uc.add(websocket)


@router.websocket("/ws/{type_}")
@inject
async def websocket_type(
    websocket: WebSocket,
    type_: str,
    socket_uc: SocketUC = Depends(Provide[TestContainer.test_socket_uc]),
):
    if type_ not in TYPES:
        type_ = MSGPACK
    await socket_uc.add(websocket, type_)

__all__ = ["router"]
