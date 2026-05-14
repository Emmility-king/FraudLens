import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(512))
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(64), default="ready")
    column_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="dataset")
    jobs: Mapped[list["Job"]] = relationship(back_populates="dataset")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="jobs")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id"), index=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    merchant: Mapped[str] = mapped_column(String(512), default="")
    channel: Mapped[str] = mapped_column(String(128), default="")
    raw_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="transactions")
    flag: Mapped["Flag | None"] = relationship(back_populates="transaction", uselist=False)


class Flag(Base):
    __tablename__ = "flags"

    transaction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transactions.id"), primary_key=True
    )
    risk_score: Mapped[float] = mapped_column(Float)
    band: Mapped[str] = mapped_column(String(16))
    reconstruction_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    xai_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    transaction: Mapped["Transaction"] = relationship(back_populates="flag")
