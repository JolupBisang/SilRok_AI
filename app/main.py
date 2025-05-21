from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import asr, main, docs
from core.lifecycle import shutdown, startup
from core import Settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 이벤트
    await startup(app)
    yield
    # 서버 종료 이벤트
    await shutdown(app)


def server() -> FastAPI:
    # FastAPI 앱 생성
    app = FastAPI(
        title=Settings.PROJECT_NAME,  # 프로젝트 이름
        version=Settings.PROJECT_VERSION,
        lifespan=lifespan,
    )

    # CORS 설정 (프론트엔드 연동할 때 필요)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 모든 도메인 허용 (운영환경에서는 제한 필요)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록 (API 엔드포인트)
    app.include_router(main.router, prefix="", tags=["Users"])
    app.include_router(asr.router, prefix="/asr", tags=["AI"])
    app.include_router(docs.router, prefix="/docs", tags=["Docs"])
    return app


# FastAPI 실행 (uvicorn으로 실행하면 필요 없음)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        server(),
        host="0.0.0.0",
        port=8000,
        ws_ping_interval=30,
        ws_ping_timeout=None,  # 60
        # log_level="debug"
    )
