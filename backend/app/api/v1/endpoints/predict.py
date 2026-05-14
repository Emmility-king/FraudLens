from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import Dataset, Transaction
from app.services.model import predict_df

router = APIRouter()


@router.post("/predict/{dataset_id}")
async def predict_dataset(dataset_id: str, db: Annotated[AsyncSession, Depends(get_db_session)]):
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    q = await db.execute(
        Transaction.__table__.select().where(Transaction.dataset_id == dataset_id).limit(10000)
    )
    rows = q.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No transactions found for dataset")

    # build a dataframe expected by the model service
    import pandas as pd

    df = pd.DataFrame([{"amount": r.amount, "merchant": r.merchant, "channel": r.channel} for r in rows])

    try:
        scores = predict_df(df)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    # attach score to the first few rows in response
    items = []
    for i, r in enumerate(rows[:100]):
        items.append({"transaction_id": r.id, "score": float(scores[i])})

    return {"dataset_id": dataset_id, "preview": items, "total": len(rows)}
