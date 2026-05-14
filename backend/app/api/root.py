from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas import HealthResponse, ReadyResponse

router = APIRouter(tags=["system"])

Db = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=ReadyResponse)
async def ready(db: Db) -> ReadyResponse:
    await db.execute(text("SELECT 1"))
    return ReadyResponse(status="ok", database="connected")
