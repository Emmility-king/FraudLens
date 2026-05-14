from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.root import router as root_router
from app.api.v1.router import api_router as v1_router
from app.core.config import get_settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Fine-Guard AI",
        description="Fraud detection API (school project — SQLite + stub scorer).",
        version=settings.api_version,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(root_router)
    application.include_router(v1_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
