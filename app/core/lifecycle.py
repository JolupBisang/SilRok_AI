from fastapi import FastAPI


async def startup(app: FastAPI):
    from . import logger
    from container import Container

    await Container.init_all()

    # logging.getLogger("uvicorn").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    logger.info("🚀 FastAPI 서버 시작!")


async def shutdown(app: FastAPI):
    from . import logger
    from container import Container

    await Container.get_instance().shutdown_resources()
    logger().info("🛑 FastAPI 서버 종료!")
