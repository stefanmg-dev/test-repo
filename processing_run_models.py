from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProcessingRunListItemModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID = Field(
        description="Unique processing run identifier.",
        examples=["00000000-0000-4000-8000-000000000001"],
    )
    document_type: str = Field(
        description="Configured document type used for extraction.",
        examples=["invoice"],
    )
    profile: str | None = Field(
        default=None,
        description="Resolved supplier profile, when applicable.",
        examples=["telecom_a1"],
    )
    filename: str = Field(
        description="Original uploaded filename.",
        examples=["synthetic-invoice.pdf"],
    )
    input_format: str = Field(
        description="Normalized uploaded file format.",
        examples=["pdf"],
    )
    processing_status: str = Field(
        description=(
            "Current or final lifecycle status, such as processing, "
            "accepted, review, invalid, or failed."
        ),
        examples=["accepted"],
    )
    requires_review: bool = Field(
        description="Whether the run requires human review.",
        examples=[False],
    )
    review_status: str | None = Field(
        default=None,
        description=(
            "Review workflow state: pending, approved, corrected, "
            "or rejected. Null when review does not apply."
        ),
        examples=["pending"],
    )
    started_at: datetime = Field(
        description="UTC timestamp when processing started."
    )
    completed_at: datetime | None = Field(
        default=None,
        description=(
            "UTC timestamp when processing completed. Null while the "
            "run is still processing."
        ),
    )
    duration_ms: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Total processing duration in milliseconds. Null until "
            "processing completes."
        ),
        examples=[1250],
    )
    created_at: datetime = Field(
        description="UTC timestamp when the processing run was created."
    )


class ProcessingRunDetailModel(ProcessingRunListItemModel):
    step_timings: dict[str, int] | None = Field(
        default=None,
        description="Pipeline step durations in milliseconds.",
        examples=[{"document_input_ms": 120}],
    )
    quality: dict[str, Any] | None = Field(
        default=None,
        description="Persisted input-quality result and warnings."
    )
    final_values: dict[str, Any] | None = Field(
        default=None,
        description="Persisted final scalar extraction values."
    )
    corrected_values: dict[str, Any] | None = Field(
        default=None,
        description="Reviewer-supplied corrected values, when present."
    )
    configuration_hash: str | None = Field(
        default=None,
        description="SHA-256 identifier of the resolved configuration snapshot."
    )
    configuration_snapshot: dict[str, Any] | None = Field(
        default=None,
        description="Resolved extraction configuration used by this run."
    )
    configuration_schema_version: str | None = Field(
        default=None,
        description="Schema version of the persisted configuration snapshot."
    )
    invoice_schema_version: str | None = Field(
        default=None,
        description="Universal Invoice schema version used for invoice shadow validation."
    )
    invoice_shadow_validation_status: Literal[
        "succeeded",
        "failed",
        "not_applicable",
    ] | None = Field(
        default=None,
        description="Universal Invoice shadow-validation outcome."
    )
    invoice_shadow_validation_reason: Literal[
        "validation_error",
        "mapper_error",
    ] | None = Field(
        default=None,
        description="Safe failure reason code when shadow validation failed."
    )
    review_comment: str | None = Field(
        default=None,
        description="Optional human-review comment."
    )
    reviewed_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of the recorded review decision."
    )
    reviewed_by_type: str | None = Field(
        default=None,
        description="Principal type that recorded the review decision."
    )
    reviewed_by_subject: str | None = Field(
        default=None,
        description="Authenticated subject that recorded the review decision."
    )
    collections: dict[str, Any] | None = Field(
        default=None,
        description="Persisted repeated extraction collections."
    )
    validation: dict[str, Any] | None = Field(
        default=None,
        description="Persisted scalar and collection validation metadata."
    )
    error: dict[str, Any] | None = Field(
        default=None,
        description="Safe structured processing failure metadata."
    )
    updated_at: datetime = Field(
        description="UTC timestamp of the most recent persisted update."
    )


class ProcessingRunListResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProcessingRunListItemModel] = Field(
        description="Processing runs in the requested page."
    )
    total: int = Field(
        ge=0,
        description="Total number of matching tenant-owned runs.",
        examples=[42],
    )
    offset: int = Field(
        ge=0,
        description="Number of matching runs skipped before this page.",
        examples=[0],
    )
    limit: int = Field(
        ge=1,
        le=100,
        description="Maximum number of runs requested for this page.",
        examples=[20],
    )

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
