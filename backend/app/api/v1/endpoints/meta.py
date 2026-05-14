from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas import MetaResponse

router = APIRouter(tags=["meta"])


@router.get("/meta", response_model=MetaResponse)
async def meta() -> MetaResponse:
    s = get_settings()
    return MetaResponse(api_version=s.api_version, model_version=s.model_version)
