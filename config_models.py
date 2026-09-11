from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


FieldType = Literal[
    "constant",
    "regex",
    "regex_list",
    "nearby",
    "llm",
]

OccurrenceType = Literal[
    "first",
    "last",
]

DirectionType = Literal[
    "before",
    "after",
    "both",
]

ValidationType = Literal[
    "required",
    "regex",
    "date",
    "decimal",
]


class ValidationRuleModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    type: ValidationType
    message: str | None = None

    pattern: str | None = None
    format: str | None = None

    minimum: str | int | float | None = None
    maximum: str | int | float | None = None


class DocumentFieldModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    name: str = Field(
        min_length=1,
        max_length=100
    )

    type: FieldType

    label: dict[str, str] | None = None

    value: Any | None = None

    rule: str | None = None
    rules: list[str] | None = None

    anchor: str | None = None
    pattern: str | None = None

    occurrence: OccurrenceType | None = None
    direction: DirectionType | None = None

    window_size: int | None = Field(
        default=None,
        gt=0,
        le=10000
    )

    validation: list[ValidationRuleModel] = Field(
        default_factory=list
    )


class DocumentTypeModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    fields: list[DocumentFieldModel] = Field(
        default_factory=list
    )


class CreateDocumentTypeRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    document_type: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$"
    )


class RenameDocumentTypeRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    new_document_type: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$"
    )


class AddFieldRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    field: DocumentFieldModel


class UpdateFieldRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    field: DocumentFieldModel


class ConfigResponse(BaseModel):
    document_types: dict[str, DocumentTypeModel]


class OperationResponse(BaseModel):
    status: Literal["ok"]
    message: str