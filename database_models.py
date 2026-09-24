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
    tenant_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="default",
        server_default="default",
        index=True,
    )
    created_by_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="system",
        server_default="system",
    )
    created_by_subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="legacy",
        server_default="legacy",
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


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        CheckConstraint(
            "expires_at IS NULL OR expires_at > created_at",
            name="ck_api_keys_expiry_after_creation",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    secret_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    secret_prefix: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        unique=True,
        index=True,
    )
    scopes: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
