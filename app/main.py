from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from omegaconf import OmegaConf

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.lifecycle import shutdown, startup

    # 서버 시작 이벤트
    await startup(app)
    yield
    # 서버 종료 이벤트
    await shutdown(app)


def server() -> FastAPI:
    from config import Config
    from container import Container
    from core.logger_config import setup_main_logging
    from api import diarization, docs, llm, main, socket
    from docs import DESCRIPTION

    container = Container.get_instance()  # 컨테이너 인스턴스 가져오기
    container.config.update(Config.get_instance().dict)  # 설정 파일 로드
    container.wire(modules=[diarization, llm, main, socket, docs])  # 의존성 주입 설정
    setup_main_logging()  # 로깅 설정

    # FastAPI 앱 생성
    app = FastAPI(
        title=container.config.server.name(),  # 프로젝트 이름
        version=container.config.server.version(),  # 프로젝트 버전
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    app.container = container

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
    app.include_router(diarization.router, prefix="/diarization", tags=["Diarization"])
    app.include_router(llm.router, prefix="/llm", tags=["LLM"])
    app.include_router(socket.router, prefix="/socket", tags=["Socket"])
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
