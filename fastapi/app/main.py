from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles

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
        docs_url=None,  # 禁用默认CDN，使用本地文件
        redoc_url=None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载静态文件目录
    application.mount("/static", StaticFiles(directory="static"), name="static")

    application.include_router(health.router, prefix=settings.API_V1_PREFIX)
    application.include_router(git_repo.router, prefix=settings.API_V1_PREFIX)
    application.include_router(commit.router, prefix=settings.API_V1_PREFIX)
    application.include_router(path_config.router, prefix=settings.API_V1_PREFIX)

    return application


app = create_app()


@app.get("/", include_in_schema=False)
async def root():
    return {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "redoc": "/redoc",
        "api_prefix": settings.API_V1_PREFIX,
    }


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} - API Docs",
        swagger_js_url="/static/swagger/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger/swagger-ui.css",
        swagger_favicon_url="",
    )


@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} - ReDoc",
    )
