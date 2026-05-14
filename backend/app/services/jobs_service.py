import math
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session_maker
from app.models import Flag, Job, Transaction


def _stub_risk_score(amount: float, merchant: str, channel: str) -> float:
    base = abs(math.sin(amount + len(merchant))) * 0.55 + 0.15
    ch = channel.lower()
    if ch in ("wire", "digital", "swift", "international"):
        base = min(0.99, base + 0.12)
    return round(min(0.99, base), 4)


def _band_for(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _stub_xai(amount: float, merchant: str, channel: str, risk: float) -> list[dict[str, Any]]:
    return [
        {
            "feature": "amount",
            "contribution": round(min(0.5, risk * 0.45), 4),
            "note": f"Amount {amount:.2f} — heuristic stub (not real SHAP).",
        },
        {
            "feature": "channel",
            "contribution": 0.22 if channel else 0.05,
            "note": f"Channel `{channel or 'unknown'}` vs. peer baseline (stub).",
        },
        {
            "feature": "merchant_profile",
            "contribution": 0.12,
            "note": f"Merchant string length {len(merchant)} — placeholder signal.",
        },
    ]


async def run_stub_scoring_job(job_id: str, dataset_id: str) -> None:
    maker = get_session_maker()
    async with maker() as db:
        job = await db.get(Job, job_id)
        if not job:
            return
        job.status = "running"
        await db.flush()
        try:
            res = await db.execute(select(Transaction).where(Transaction.dataset_id == dataset_id))
            txs = list(res.scalars())
            tid_subq = select(Transaction.id).where(Transaction.dataset_id == dataset_id)
            await db.execute(delete(Flag).where(Flag.transaction_id.in_(tid_subq)))
            for tx in txs:
                risk = _stub_risk_score(tx.amount, tx.merchant, tx.channel)
                band = _band_for(risk)
                xai = _stub_xai(tx.amount, tx.merchant, tx.channel, risk)
                db.add(
                    Flag(
                        transaction_id=tx.id,
                        risk_score=risk,
                        band=band,
                        reconstruction_error=None,
                        xai_json=xai,
                    )
                )
            job.status = "succeeded"
            job.finished_at = datetime.now(timezone.utc)
            job.error_message = None
            await db.commit()
        except Exception as e:
            await db.rollback()
            async with maker() as db2:
                job2 = await db2.get(Job, job_id)
                if job2:
                    job2.status = "failed"
                    job2.error_message = str(e)
                    job2.finished_at = datetime.now(timezone.utc)
                    await db2.commit()
