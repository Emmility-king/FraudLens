from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import Flag, Transaction
from app.schemas import (
    FlagDetailResponse,
    FlagListResponse,
    FlagRow,
    FlagStatsResponse,
    HistogramBin,
    XaiSignal,
)

router = APIRouter()

Db = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/stats", response_model=FlagStatsResponse)
async def flag_stats(db: Db) -> FlagStatsResponse:
    total_tx = int((await db.execute(select(func.count()).select_from(Transaction))).scalar_one())
    flagged = int((await db.execute(select(func.count()).select_from(Flag))).scalar_one())

    amt_stmt = (
        select(func.coalesce(func.sum(Transaction.amount), 0.0))
        .select_from(Flag)
        .join(Transaction, Transaction.id == Flag.transaction_id)
        .where(Flag.band.in_(("medium", "high")))
    )
    flagged_amount_sum = float((await db.execute(amt_stmt)).scalar_one())

    high_ct = int(
        (
            await db.execute(select(func.count()).select_from(Flag).where(Flag.band == "high"))
        ).scalar_one()
    )

    edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.01]
    labels = ["0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"]
    histogram: list[HistogramBin] = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if i < len(edges) - 2:
            cond = (Flag.risk_score >= lo) & (Flag.risk_score < hi)
        else:
            cond = (Flag.risk_score >= lo) & (Flag.risk_score <= 1.0)
        cnt = int((await db.execute(select(func.count()).select_from(Flag).where(cond))).scalar_one())
        histogram.append(HistogramBin(range=labels[i], count=cnt))

    return FlagStatsResponse(
        total_transactions=total_tx,
        flagged_count=flagged,
        flagged_amount_sum=flagged_amount_sum,
        open_high_risk=high_ct,
        histogram=histogram,
    )


@router.get("", response_model=FlagListResponse)
async def list_flags(
    db: Db,
    skip: int = 0,
    limit: int = 50,
    min_risk: float | None = None,
    dataset_id: str | None = None,
) -> FlagListResponse:
    filters = []
    if min_risk is not None:
        filters.append(Flag.risk_score >= min_risk)
    if dataset_id is not None:
        filters.append(Transaction.dataset_id == dataset_id)

    count_base = select(func.count()).select_from(Flag).join(Transaction, Transaction.id == Flag.transaction_id)
    if filters:
        count_base = count_base.where(*filters)
    total = int((await db.execute(count_base)).scalar_one())

    stmt = (
        select(Transaction, Flag)
        .join(Flag, Flag.transaction_id == Transaction.id)
        .order_by(Flag.risk_score.desc())
        .offset(skip)
        .limit(limit)
    )
    if filters:
        stmt = stmt.where(*filters)
    rows = (await db.execute(stmt)).all()

    items = [
        FlagRow(
            id=tx.id,
            dataset_id=tx.dataset_id,
            occurred_at=tx.occurred_at,
            amount=tx.amount,
            merchant=tx.merchant,
            channel=tx.channel,
            risk_score=fl.risk_score,
            band=fl.band,  # type: ignore[arg-type]
        )
        for tx, fl in rows
    ]
    return FlagListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{transaction_id}", response_model=FlagDetailResponse)
async def get_flag(transaction_id: str, db: Db) -> FlagDetailResponse:
    stmt = select(Transaction, Flag).join(Flag, Flag.transaction_id == Transaction.id).where(
        Transaction.id == transaction_id
    )
    row = (await db.execute(stmt)).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Flagged transaction not found.")
    tx, fl = row
    signals: list[XaiSignal] = []
    if fl.xai_json:
        for s in fl.xai_json:
            signals.append(
                XaiSignal(
                    feature=str(s.get("feature", "")),
                    contribution=float(s.get("contribution", 0.0)),
                    note=str(s.get("note", "")),
                )
            )
    return FlagDetailResponse(
        transaction_id=tx.id,
        dataset_id=tx.dataset_id,
        occurred_at=tx.occurred_at,
        amount=tx.amount,
        merchant=tx.merchant,
        channel=tx.channel,
        risk_score=fl.risk_score,
        band=fl.band,  # type: ignore[arg-type]
        xai_signals=signals,
    )
