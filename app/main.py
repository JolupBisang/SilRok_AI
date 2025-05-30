from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.lifecycle import lifespan
from api import api_router, wire_modules
from containers import Container
from core.logging_manager import setup_main_logging
from docs import DESCRIPTION


def server() -> FastAPI:
    setup_main_logging()  # 로깅 설정
    manager = Container.get_manager()  # 컨테이너 인스턴스 가져오기
    manager.container.wire(modules=wire_modules)  # 의존성 주입 설정
    config = manager.container.config

    # FastAPI 앱 생성
    app = FastAPI(
        title = config.server.name(),  # 프로젝트 이름
        version=config.server.version(),  # 프로젝트 버전
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    # app.container = container

    # CORS 설정 (프론트엔드 연동할 때 필요)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 모든 도메인 허용 (운영환경에서는 제한 필요)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록 (API 엔드포인트)
    app.include_router(api_router, prefix="")

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
