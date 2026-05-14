from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import Job
from app.schemas import JobStatusResponse

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db_session)) -> JobStatusResponse:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusResponse(
        job_id=job.id,
        dataset_id=job.dataset_id,
        status=job.status,  # type: ignore[arg-type]
        error_message=job.error_message,
    )
