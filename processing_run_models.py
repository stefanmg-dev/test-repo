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
    field_evidence: dict[str, Any] | None = Field(
        default=None,
        description="Persisted safe scalar extraction evidence."
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
    collection_evidence: dict[str, Any] | None = Field(
        default=None,
        description="Persisted safe collection extraction evidence."
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

    schema_version: str = Field(
        description="Universal Invoice schema version.",
        examples=["1"],
    )
    total: int = Field(
        ge=0,
        description="Invoice runs evaluated with this schema version.",
        examples=[4],
    )
    succeeded: int = Field(
        ge=0,
        description="Runs whose shadow validation succeeded.",
        examples=[3],
    )
    failed: int = Field(
        ge=0,
        description="Runs whose shadow validation failed.",
        examples=[1],
    )


class InvoiceShadowFailureReasonSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: Literal[
        "validation_error",
        "mapper_error",
    ] = Field(
        description="Safe shadow-validation failure reason code.",
        examples=["validation_error"],
    )
    count: int = Field(
        ge=0,
        description="Number of failed runs with this reason.",
        examples=[1],
    )


class InvoiceShadowSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(
        ge=0,
        description="Tenant-owned runs included in the summary.",
        examples=[5],
    )
    succeeded: int = Field(
        ge=0,
        description="Invoice runs with successful shadow validation.",
        examples=[3],
    )
    failed: int = Field(
        ge=0,
        description="Invoice runs with failed shadow validation.",
        examples=[1],
    )
    not_applicable: int = Field(
        ge=0,
        description="Runs for which invoice shadow validation did not apply.",
        examples=[1],
    )
    success_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description=(
            "Succeeded divided by succeeded plus failed. Null when no "
            "applicable invoice runs exist."
        ),
        examples=[0.75],
    )
    schema_versions: list[InvoiceShadowSchemaVersionSummaryModel] = Field(
        description="Applicable invoice results grouped by schema version."
    )
    failure_reasons: list[
        InvoiceShadowFailureReasonSummaryModel
    ] = Field(
        description="Failed invoice results grouped by safe reason code."
    )

class ProcessingRunRetentionPreviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retention_days: int = Field(
        ge=30,
        le=3650,
        description="Configured completed-run retention period in days.",
        examples=[365],
    )
    cutoff: datetime = Field(
        description=(
            "UTC completion-time cutoff. Completed runs older than this "
            "timestamp are eligible for deletion."
        )
    )
    candidate_count: int = Field(
        ge=0,
        description="Tenant-owned completed runs currently eligible for deletion.",
        examples=[2],
    )
    oldest_candidate_completed_at: datetime | None = Field(
        default=None,
        description=(
            "Oldest eligible completion timestamp, or null when there are "
            "no candidates."
        ),
    )
    newest_candidate_completed_at: datetime | None = Field(
        default=None,
        description=(
            "Newest eligible completion timestamp, or null when there are "
            "no candidates."
        ),
    )


class ProcessingRunRetentionExecuteRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation: Literal["DELETE"] = Field(
        description=(
            "Exact irreversible-operation confirmation. The only accepted "
            "value is DELETE."
        ),
        examples=["DELETE"],
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum eligible runs to delete in this execution.",
        examples=[100],
    )


class ProcessingRunRetentionExecuteModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retention_days: int = Field(
        ge=30,
        le=3650,
        description="Configured completed-run retention period in days.",
        examples=[365],
    )
    cutoff: datetime = Field(
        description="UTC completion-time cutoff used by this execution."
    )
    limit: int = Field(
        ge=1,
        le=1000,
        description="Maximum deletion count requested for this execution.",
        examples=[100],
    )
    deleted_count: int = Field(
        ge=0,
        description="Tenant-owned processing runs deleted atomically.",
        examples=[2],
    )

class ProcessingRunReviewRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "approved",
        "corrected",
        "rejected",
    ] = Field(
        description=(
            "Terminal review decision. Use corrected when corrected_values "
            "contains reviewer-approved replacements."
        ),
        examples=["corrected"],
    )
    corrected_values: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Reviewer-approved scalar values. Required by business rules "
            "for a corrected decision and omitted otherwise."
        ),
        examples=[{"invoice_number": "INV-SYNTH-002"}],
    )
    comment: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional review note, limited to 2000 characters.",
        examples=["Verified against the synthetic document."],
    )


class ProcessingRunReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    processing_run_id: UUID = Field(
        description="Unique identifier of the reviewed processing run.",
        examples=["00000000-0000-4000-8000-000000000001"],
    )
    status: str | None = Field(
        default=None,
        description=(
            "Current review state. Null before the review workflow starts."
        ),
        examples=["corrected"],
    )
    original_values: dict[str, Any] | None = Field(
        default=None,
        description="Original final extraction values preserved for audit."
    )
    corrected_values: dict[str, Any] | None = Field(
        default=None,
        description="Reviewer-supplied corrected values, when present."
    )
    effective_values: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Values consumers should use after review: corrected values "
            "for corrected reviews, otherwise original values."
        ),
    )
    comment: str | None = Field(
        default=None,
        description="Optional reviewer comment."
    )
    reviewed_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the review decision was recorded."
    )
    reviewed_by_type: str | None = Field(
        default=None,
        description="Authenticated principal type that recorded the review."
    )
    reviewed_by_subject: str | None = Field(
        default=None,
        description="Authenticated subject that recorded the review."
    )

class ProcessingRunReviewSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_requiring_review: int = Field(
        ge=0,
        description="Tenant-owned runs that entered the review workflow.",
        examples=[10],
    )
    pending: int = Field(
        ge=0,
        description="Review-required runs without a terminal decision.",
        examples=[4],
    )
    approved: int = Field(
        ge=0,
        description="Runs approved without corrected values.",
        examples=[2],
    )
    corrected: int = Field(
        ge=0,
        description="Runs completed with reviewer-corrected values.",
        examples=[3],
    )
    rejected: int = Field(
        ge=0,
        description="Runs rejected during review.",
        examples=[1],
    )
    average_review_duration_ms: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Average elapsed milliseconds from run completion to terminal "
            "review. Null when no completed reviews are available."
        ),
        examples=[1500],
    )

class ExtractionQualityFieldCorrectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_name: str = Field(
        description="Configured scalar field name.",
        examples=["invoice_number"],
    )
    corrections: int = Field(
        ge=0,
        description="Corrected runs in which this field changed.",
        examples=[1],
    )


class ExtractionQualityFieldCountsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0, description="Compared field occurrences.")
    unchanged: int = Field(ge=0, description="Field occurrences left unchanged.")
    changed: int = Field(ge=0, description="Existing field values changed.")
    added: int = Field(ge=0, description="Values added by reviewers.")
    removed: int = Field(ge=0, description="Values removed by reviewers.")


class ExtractionQualityGroupModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str = Field(
        description="Document type represented by this quality group.",
        examples=["invoice"],
    )
    profile: str | None = Field(
        default=None,
        description="Resolved supplier profile, or null when not applicable.",
        examples=["telecom_a1"],
    )
    configuration_hash: str | None = Field(
        default=None,
        description="Configuration snapshot hash used by the corrected runs.",
        examples=["hash-synthetic"],
    )
    corrected_runs: int = Field(
        ge=0,
        description="Corrected runs included in this group.",
        examples=[1],
    )
    field_counts: ExtractionQualityFieldCountsModel = Field(
        description="Compared field occurrences by change category."
    )
    corrections: int = Field(
        ge=0,
        description="Changed, added, and removed field occurrences.",
        examples=[1],
    )
    correction_rate: float = Field(
        ge=0,
        le=1,
        description="Corrections divided by compared field occurrences.",
        examples=[0.5],
    )
    field_corrections: list[
        ExtractionQualityFieldCorrectionModel
    ] = Field(
        description="Correction counts grouped by configured field name."
    )


class ExtractionQualityAnalysisModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corrected_runs: int = Field(
        ge=0,
        description="Tenant-owned corrected runs included in the analysis.",
        examples=[1],
    )
    groups: list[ExtractionQualityGroupModel] = Field(
        description=(
            "Quality groups partitioned by document type, profile, and "
            "configuration hash."
        )
    )
