from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.routers import health, git_repo, commit, path_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    yield
    # 关闭时断开数据库连接
    await close_db()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router, prefix=settings.API_V1_PREFIX)
    application.include_router(git_repo.router, prefix=settings.API_V1_PREFIX)
    application.include_router(commit.router, prefix=settings.API_V1_PREFIX)
    application.include_router(path_config.router, prefix=settings.API_V1_PREFIX)

    return application


app = create_app()
