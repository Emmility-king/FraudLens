import asyncio
import io
import math
import uuid
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import Dataset, Job, Transaction
from app.schemas import DatasetUploadResponse, JobCreateResponse
from app.services.jobs_service import run_stub_scoring_job

router = APIRouter()

MAX_ROWS = 200_000


def _normalize_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    cols = {str(c).lower().strip(): c for c in df.columns}

    def pick(*names: str) -> str | None:
        for n in names:
            if n in cols:
                return cols[n]
        return None

    tcol = pick("occurred_at", "timestamp", "datetime", "date", "time", "txn_time")
    acol = pick("amount", "value", "amt", "transaction_amount", "payment_amount")
    mcol = pick("merchant", "description", "payee", "merchant_name", "name")
    ccol = pick("channel", "type", "txn_type", "payment_type", "transaction_type")

    if tcol:
        dt = pd.to_datetime(df[tcol], utc=True, errors="coerce")
    else:
        warnings.append("No time column found; using current UTC time.")
        dt = pd.Series([datetime.now(timezone.utc)] * len(df), dtype="datetime64[ns, UTC]")

    if acol:
        amt = pd.to_numeric(df[acol], errors="coerce").fillna(0.0)
    else:
        warnings.append("No amount column found; defaulting to 0.0.")
        amt = pd.Series([0.0] * len(df))

    mer = df[mcol].astype(str) if mcol else pd.Series([""] * len(df))
    ch = df[ccol].astype(str) if ccol else pd.Series(["unknown"] * len(df))

    out = pd.DataFrame({"occurred_at": dt, "amount": amt.astype(float), "merchant": mer, "channel": ch})
    return out, warnings


@router.post("/", response_model=DatasetUploadResponse)
async def upload_dataset(
    db: AsyncSession = Depends(get_db_session),
    file: UploadFile = File(...),
) -> DatasetUploadResponse:
    filename = file.filename or "dataset.csv"
    lower = filename.lower()
    if not (lower.endswith(".csv") or lower.endswith(".xlsx") or lower.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Upload must be a .csv or .xlsx file.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        if lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw))
        else:
            df = pd.read_excel(io.BytesIO(raw), engine="openpyxl")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}") from e

    if len(df) > MAX_ROWS:
        raise HTTPException(status_code=400, detail=f"File exceeds max rows ({MAX_ROWS}).")

    norm, warnings = _normalize_dataframe(df)
    ds_id = str(uuid.uuid4())
    column_json = {"source_columns": [str(c) for c in df.columns.tolist()]}

    dataset = Dataset(
        id=ds_id,
        filename=filename,
        row_count=len(norm),
        status="ready",
        column_json=column_json,
    )
    db.add(dataset)

    for _, row in norm.iterrows():
        ts = row["occurred_at"]
        if pd.isna(ts):
            ts = datetime.now(timezone.utc)
        elif getattr(ts, "tzinfo", None) is None:
            ts = pd.Timestamp(ts).tz_localize("UTC").to_pydatetime()
        else:
            ts = pd.Timestamp(ts).to_pydatetime()
        tx = Transaction(
            id=str(uuid.uuid4()),
            dataset_id=ds_id,
            occurred_at=ts,
            amount=float(row["amount"]),
            merchant=str(row["merchant"])[:512],
            channel=str(row["channel"])[:128],
            raw_json=None,
        )
        db.add(tx)

    await db.commit()

    return DatasetUploadResponse(
        dataset_id=ds_id,
        filename=filename,
        row_count=len(norm),
        status="ready",
        warnings=warnings,
    )


@router.post("/{dataset_id}/score", response_model=JobCreateResponse)
async def score_dataset(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> JobCreateResponse:
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, dataset_id=dataset_id, status="queued")
    db.add(job)
    await db.commit()

    background_tasks.add_task(run_stub_scoring_job, job_id, dataset_id)
    return JobCreateResponse(job_id=job_id, status="queued")
