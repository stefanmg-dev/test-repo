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
    review_status: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    created_at: datetime


class ProcessingRunDetailModel(ProcessingRunListItemModel):
    step_timings: dict[str, int] | None = None
    quality: dict[str, Any] | None = None
    final_values: dict[str, Any] | None = None
    corrected_values: dict[str, Any] | None = None
    configuration_hash: str | None = None
    configuration_snapshot: dict[str, Any] | None = None
    configuration_schema_version: str | None = None
    invoice_schema_version: str | None = None
    invoice_shadow_validation_status: Literal[
        "succeeded",
        "failed",
        "not_applicable",
    ] | None = None
    invoice_shadow_validation_reason: Literal[
        "validation_error",
        "mapper_error",
    ] | None = None
    review_comment: str | None = None
    reviewed_at: datetime | None = None
    reviewed_by_type: str | None = None
    reviewed_by_subject: str | None = None
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


class InvoiceShadowSchemaVersionSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str
    total: int = Field(ge=0)
    succeeded: int = Field(ge=0)
    failed: int = Field(ge=0)


class InvoiceShadowFailureReasonSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: Literal[
        "validation_error",
        "mapper_error",
    ]
    count: int = Field(ge=0)


class InvoiceShadowSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total: int = Field(ge=0)
    succeeded: int = Field(ge=0)
    failed: int = Field(ge=0)
    not_applicable: int = Field(ge=0)
    success_rate: float | None = Field(default=None, ge=0, le=1)
    schema_versions: list[InvoiceShadowSchemaVersionSummaryModel]
    failure_reasons: list[
        InvoiceShadowFailureReasonSummaryModel
    ]


class ProcessingRunRetentionPreviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    retention_days: int = Field(ge=30, le=3650)
    cutoff: datetime
    candidate_count: int = Field(ge=0)
    oldest_candidate_completed_at: datetime | None = None
    newest_candidate_completed_at: datetime | None = None


class ProcessingRunRetentionExecuteRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmation: Literal["DELETE"]
    limit: int = Field(default=100, ge=1, le=1000)


class ProcessingRunRetentionExecuteModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    retention_days: int = Field(ge=30, le=3650)
    cutoff: datetime
    limit: int = Field(ge=1, le=1000)
    deleted_count: int = Field(ge=0)


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


class ProcessingRunReviewSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_requiring_review: int = Field(ge=0)
    pending: int = Field(ge=0)
    approved: int = Field(ge=0)
    corrected: int = Field(ge=0)
    rejected: int = Field(ge=0)
    average_review_duration_ms: int | None = Field(
        default=None,
        ge=0,
    )


class ExtractionQualityFieldCorrectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_name: str
    corrections: int = Field(ge=0)


class ExtractionQualityFieldCountsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    unchanged: int = Field(ge=0)
    changed: int = Field(ge=0)
    added: int = Field(ge=0)
    removed: int = Field(ge=0)


class ExtractionQualityGroupModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str
    profile: str | None
    configuration_hash: str | None
    corrected_runs: int = Field(ge=0)
    field_counts: ExtractionQualityFieldCountsModel
    corrections: int = Field(ge=0)
    correction_rate: float = Field(ge=0, le=1)
    field_corrections: list[
        ExtractionQualityFieldCorrectionModel
    ]


class ExtractionQualityAnalysisModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corrected_runs: int = Field(ge=0)
    groups: list[ExtractionQualityGroupModel]
