from fastapi import APIRouter

from app.api.v1.endpoints import datasets, flags, jobs, meta

api_router = APIRouter()
api_router.include_router(meta.router)
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(flags.router, prefix="/flags", tags=["flags"])
