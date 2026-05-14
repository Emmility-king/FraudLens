from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import Job
from app.schemas import JobStatusResponse
import json
from pathlib import Path

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db_session)) -> JobStatusResponse:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    # try to read progress file
    prog = None
    try:
        prog_file = Path("data") / "job_progress" / f"{job_id}.json"
        if prog_file.exists():
            with open(prog_file, "r", encoding="utf-8") as pf:
                d = json.load(pf)
                prog = float(d.get("progress"))
    except Exception:
        prog = None

    return JobStatusResponse(
        job_id=job.id,
        dataset_id=job.dataset_id,
        status=job.status,  # type: ignore[arg-type]
        error_message=job.error_message,
        progress=prog,
    )
