from fastapi import APIRouter

from test.api import test_main, test_diarization, test_llm, test_socket


test_api_router = APIRouter()
test_wire_modules = [test_main, test_diarization, test_llm, test_socket]

test_api_router.include_router(test_main.router, prefix="", tags=["Users"])
test_api_router.include_router(
    test_diarization.router, prefix="/diarization", tags=["Diarization"]
)
test_api_router.include_router(test_llm.router, prefix="/llm", tags=["LLM"])
test_api_router.include_router(test_socket.router, prefix="/socket", tags=["Socket"])

__all__ = ["test_api_router", "test_wire_modules"]
