from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RiskBand = Literal["low", "medium", "high"]


class HealthResponse(BaseModel):
    status: str = "ok"


class ReadyResponse(BaseModel):
    status: str
    database: str


class MetaResponse(BaseModel):
    api_version: str
    model_version: str


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    row_count: int
    status: str
    warnings: list[str] = Field(default_factory=list)


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    dataset_id: str
    status: str
    error_message: str | None = None


class FlagRow(BaseModel):
    id: str
    dataset_id: str
    occurred_at: datetime | None
    amount: float
    merchant: str
    channel: str
    risk_score: float
    band: RiskBand


class FlagListResponse(BaseModel):
    items: list[FlagRow]
    total: int
    skip: int
    limit: int


class HistogramBin(BaseModel):
    range: str
    count: int


class FlagStatsResponse(BaseModel):
    total_transactions: int
    flagged_count: int
    flagged_amount_sum: float
    open_high_risk: int
    histogram: list[HistogramBin]


class XaiSignal(BaseModel):
    feature: str
    contribution: float
    note: str


class FlagDetailResponse(BaseModel):
    transaction_id: str
    dataset_id: str
    occurred_at: datetime | None
    amount: float
    merchant: str
    channel: str
    risk_score: float
    band: RiskBand
    xai_signals: list[XaiSignal]
