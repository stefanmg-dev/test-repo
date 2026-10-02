from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


QualityStatus = Literal[
    "accepted",
    "review",
]


ProcessingStatus = Literal[
    "accepted",
    "review",
    "invalid",
]


class QualityWarningModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    code: str = Field(
        min_length=1,
        description=(
            "Stable machine-readable warning code produced by "
            "input quality or profile resolution checks."
        ),
        examples=["low_resolution"],
    )

    message: str = Field(
        min_length=1,
        description=(
            "Human-readable explanation of the quality warning."
        ),
        examples=["The document resolution may reduce OCR accuracy."],
    )


class ImageQualityInputModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    format: str = Field(
        description="Detected image format.",
        examples=["PNG"],
    )

    width: int = Field(
        gt=0,
        description="Image width in pixels.",
        examples=[1652],
    )

    height: int = Field(
        gt=0,
        description="Image height in pixels.",
        examples=[2338],
    )

    short_edge: int = Field(
        gt=0,
        description="Shorter image edge in pixels.",
        examples=[1652],
    )

    long_edge: int = Field(
        gt=0,
        description="Longer image edge in pixels.",
        examples=[2338],
    )

    pixel_count: int = Field(
        gt=0,
        description="Total number of image pixels.",
        examples=[3862376],
    )

    mode: str | None = Field(
        default=None,
        description=(
            "Image color mode when available, for example RGB or L."
        ),
        examples=["RGB"],
    )

    dpi: list[float] | None = Field(
        default=None,
        description=(
            "Horizontal and vertical dots-per-inch values when "
            "present in the source metadata."
        ),
        examples=[[150.0, 150.0]],
    )


class PdfPageQualityInputModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    format: str = Field(
        description="Detected image format.",
        examples=["PNG"],
    )

    width: int = Field(
        gt=0,
        description="Image width in pixels.",
        examples=[1652],
    )

    height: int = Field(
        gt=0,
        description="Image height in pixels.",
        examples=[2338],
    )

    short_edge: int = Field(
        gt=0,
        description="Shorter image edge in pixels.",
        examples=[1652],
    )

    long_edge: int = Field(
        gt=0,
        description="Longer image edge in pixels.",
        examples=[2338],
    )

    pixel_count: int = Field(
        gt=0,
        description="Total number of image pixels.",
        examples=[3862376],
    )

    mode: str | None = Field(
        default=None,
        description=(
            "Image color mode when available, for example RGB or L."
        ),
        examples=["RGB"],
    )

    dpi: list[float] | None = Field(
        default=None,
        description=(
            "Horizontal and vertical dots-per-inch values when "
            "present in the source metadata."
        ),
        examples=[[150.0, 150.0]],
    )


class PdfQualityInputModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    format: Literal["PDF"] = Field(
        description="Normalized input format for PDF documents.",
        examples=["PDF"],
    )

    source: Literal[
        "native_pdf",
        "scanned_pdf",
    ] = Field(
        description=(
            "Text acquisition path: native_pdf contains a text "
            "layer; scanned_pdf is processed page-by-page with OCR."
        ),
        examples=["scanned_pdf"],
    )

    page_count: int = Field(
        ge=0,
        description="Number of rendered PDF pages.",
        examples=[2],
    )

    pages: list[
        PdfPageQualityInputModel
    ] | None = Field(
        default=None,
        description=(
            "Per-page image quality metadata for scanned PDFs. "
            "The field is omitted for native PDFs."
        ),
    )


class InputQualityModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    status: QualityStatus = Field(
        description=(
            "Input quality decision: accepted or review."
        ),
        examples=["accepted"],
    )
    requires_review: bool = Field(
        description=(
            "Whether input quality or profile resolution requires "
            "human review."
        ),
        examples=[False],
    )

    input: (
        ImageQualityInputModel
        | PdfQualityInputModel
    ) = Field(
        description=(
            "Technical metadata used to assess the uploaded image "
            "or PDF."
        ),
    )

    warnings: list[
        QualityWarningModel
    ] = Field(
        default_factory=list,
        description=(
            "Non-fatal quality and profile resolution warnings."
        ),
    )


class FieldEvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str = Field(
        min_length=1,
        description="Configured extraction strategy used for the field.",
        examples=["regex"],
    )
    matched: bool = Field(
        description="Whether the configured strategy produced a value.",
        examples=[True],
    )
    normalized: bool = Field(
        description="Whether normalization changed the extracted value.",
        examples=[False],
    )
    occurrence: Literal["first", "last"] | None = Field(
        default=None,
        description="Configured match occurrence when applicable.",
    )
    rule_index: int | None = Field(
        default=None,
        ge=0,
        description="Zero-based matching rule index for regex_list fields.",
    )
    anchor_found: bool | None = Field(
        default=None,
        description="Whether the configured nearby anchor was found.",
    )
    direction: Literal["before", "after", "both"] | None = Field(
        default=None,
        description="Configured nearby search direction.",
    )
    window_size: int | None = Field(
        default=None,
        gt=0,
        description="Configured nearby search window in characters.",
    )
    failure_reason: str | None = Field(
        default=None,
        description="Stable reason code when no value was produced.",
        examples=["pattern_not_matched"],
    )


class ExtractionValidationModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    valid: bool = Field(
        description=(
            "True when all configured validation rules in this "
            "validation scope passed."
        ),
        examples=[True],
    )

    errors: dict[
        str,
        list[str]
    ] = Field(
        default_factory=dict,
        description=(
            "Validation messages grouped by scalar field or "
            "collection item path. Empty when valid is true."
        ),
        examples=[{}],
    )


class ApiErrorResponseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    detail: str = Field(
        min_length=1,
        description="Human-readable API error detail.",
        examples=["Document type was not found"],
    )


class DocumentInputErrorResponseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    detail: str = Field(
        min_length=1,
        description="Human-readable API error detail.",
        examples=["Document type was not found"],
    )


class RequestValidationIssueModel(BaseModel):
    model_config = ConfigDict(
        extra="allow"
    )

    type: str = Field(
        description="Stable validation issue type.",
        examples=["missing"],
    )
    loc: list[str | int] = Field(
        description=(
            "Request location of the invalid value, such as body, "
            "form field, query parameter, or path parameter."
        ),
        examples=[["body", "file"]],
    )
    msg: str = Field(
        description="Human-readable validation message.",
        examples=["Field required"],
    )
    input: Any = Field(
        default=None,
        description=(
            "Rejected input value when FastAPI exposes it."
        ),
    )
    ctx: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional structured context for the validation issue."
        ),
    )


class RequestValidationErrorResponseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    detail: list[RequestValidationIssueModel] = Field(
        description="Request validation issues returned by FastAPI."
    )


class ExtractionResponseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    document_type: str = Field(
        min_length=1,
        description=(
            "Configured document type used to resolve extraction "
            "fields and validation rules."
        ),
        examples=["invoice"],
    )

    processing_status: ProcessingStatus = Field(
        description=(
            "Final processing decision: accepted, review, or "
            "invalid. Review means processing completed but human "
            "verification is required."
        ),
        examples=["accepted"],
    )

    profile: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description=(
            "Resolved supplier profile. Null when the document type "
            "has no profiles or no profile could be selected."
        ),
        examples=["telecom_a1"],
    )

    quality: InputQualityModel = Field(
        description=(
            "Input quality assessment and any non-fatal warnings."
        ),
    )

    raw_text: str = Field(
        description=(
            "Combined native PDF and/or OCR text used by the "
            "extraction pipeline. May contain sensitive document "
            "content."
        ),
        examples=["Synthetic invoice OCR text"],
    )

    llm_values: dict[
        str,
        Any
    ] = Field(
        default_factory=dict,
        description=(
            "Raw values returned by the optional LLM extraction "
            "stage before deterministic rules and validation."
        ),
        examples=[{}],
    )

    final_values: dict[
        str,
        Any
    ] = Field(
        default_factory=dict,
        description=(
            "Final scalar values after profile resolution, rule "
            "application, and value normalization. Keys depend on "
            "the configured document type."
        ),
        examples=[{"invoice_number": "INV-SYNTH-001"}],
    )

    field_evidence: dict[str, FieldEvidenceModel] = Field(
        default_factory=dict,
        description=(
            "Per-field extraction evidence without raw document "
            "fragments or matched sensitive values."
        ),
        examples=[{
            "invoice_number": {
                "method": "regex",
                "matched": True,
                "normalized": False,
                "occurrence": "first",
            }
        }],
    )

    collections: dict[
        str,
        list[dict[str, Any]]
    ] = Field(
        default_factory=dict,
        description=(
            "Extracted repeated structures grouped by configured "
            "collection name, such as services, meters, or "
            "consumption_items."
        ),
        examples=[{"services": []}],
    )

    collection_validation: ExtractionValidationModel = Field(
        default_factory=lambda: ExtractionValidationModel(
            valid=True,
            errors={},
        ),
        description=(
            "Validation result for extracted collection items and "
            "collection summary rules."
        ),
    )

    validation: ExtractionValidationModel = Field(
        description=(
            "Validation result for final scalar extraction values."
        ),
    )
