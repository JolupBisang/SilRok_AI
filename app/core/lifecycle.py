from contextlib import asynccontextmanager
from fastapi import FastAPI


async def startup(app: FastAPI):
    from . import logger
    from containers import Container

    try:
        await Container.get_manager().init_main()
    except Exception as e:
        raise SystemExit(f"❌ FastAPI 서버 시작 실패: {e}. ")

    # logging.getLogger("uvicorn").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    logger.info("🚀 FastAPI 서버 시작!")


async def shutdown(app: FastAPI):
    from . import logger
    from containers import Container

    await Container.get_manager().shutdown_resources()
    logger().info("🛑 FastAPI 서버 종료!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 이벤트
    await startup(app)
    yield
    # 서버 종료 이벤트
    await shutdown(app)
