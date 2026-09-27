from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProcessingRunListItemModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID
    document_type: str
    profile: str | None = None
    filename: str
    input_format: str
    processing_status: str
    requires_review: bool
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    created_at: datetime


class ProcessingRunDetailModel(ProcessingRunListItemModel):
    step_timings: dict[str, int] | None = None
    quality: dict[str, Any] | None = None
    final_values: dict[str, Any] | None = None
    collections: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    updated_at: datetime


class ProcessingRunListResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProcessingRunListItemModel]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class ProcessingRunReviewRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "approved",
        "corrected",
        "rejected",
    ]
    corrected_values: dict[str, Any] | None = None
    comment: str | None = Field(
        default=None,
        max_length=2000,
    )


class ProcessingRunReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    processing_run_id: UUID
    status: str | None
    original_values: dict[str, Any] | None
    corrected_values: dict[str, Any] | None
    effective_values: dict[str, Any] | None
    comment: str | None
    reviewed_at: datetime | None
    reviewed_by_type: str | None
    reviewed_by_subject: str | None
