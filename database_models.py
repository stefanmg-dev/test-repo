from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProcessingRun(Base):
    __tablename__ = "processing_runs"
    __table_args__ = (
        CheckConstraint(
            "duration_ms IS NULL OR duration_ms >= 0",
            name="ck_processing_runs_duration_ms_nonnegative",
        ),
        Index(
            "ix_processing_runs_document_type_created_at",
            "document_type",
            "created_at",
        ),
        Index(
            "ix_processing_runs_status_created_at",
            "processing_status",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    profile: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    input_format: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    processing_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    requires_review: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    step_timings: Mapped[dict[str, int] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    quality: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    final_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    collections: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    validation: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    error: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
