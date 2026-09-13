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


class QualityWarningModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    code: str = Field(
        min_length=1
    )

    message: str = Field(
        min_length=1
    )


class ImageQualityInputModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    format: str

    width: int = Field(
        gt=0
    )

    height: int = Field(
        gt=0
    )

    short_edge: int = Field(
        gt=0
    )

    long_edge: int = Field(
        gt=0
    )

    pixel_count: int = Field(
        gt=0
    )

    mode: str | None = None

    dpi: list[float] | None = None


class PdfPageQualityInputModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    format: str

    width: int = Field(
        gt=0
    )

    height: int = Field(
        gt=0
    )

    short_edge: int = Field(
        gt=0
    )

    long_edge: int = Field(
        gt=0
    )

    pixel_count: int = Field(
        gt=0
    )

    mode: str | None = None

    dpi: list[float] | None = None


class PdfQualityInputModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    format: Literal["PDF"]

    source: Literal[
        "native_pdf",
        "scanned_pdf",
    ]

    page_count: int = Field(
        ge=0
    )

    pages: list[
        PdfPageQualityInputModel
    ] | None = None


class InputQualityModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    status: QualityStatus
    requires_review: bool

    input: (
        ImageQualityInputModel
        | PdfQualityInputModel
    )

    warnings: list[
        QualityWarningModel
    ] = Field(
        default_factory=list
    )


class ExtractionValidationModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    valid: bool

    errors: dict[
        str,
        list[str]
    ] = Field(
        default_factory=dict
    )


class ExtractionResponseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    document_type: str = Field(
        min_length=1
    )

    profile: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )

    quality: InputQualityModel

    raw_text: str

    llm_values: dict[
        str,
        Any
    ] = Field(
        default_factory=dict
    )

    final_values: dict[
        str,
        Any
    ] = Field(
        default_factory=dict
    )

    validation: ExtractionValidationModel