from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


FieldType = Literal[
    "constant",
    "regex",
    "regex_list",
    "nearby",
    "llm",
]

OccurrenceType = Literal["first", "last"]
DirectionType = Literal["before", "after", "both"]
ValidationType = Literal["required", "regex", "date", "decimal"]
DocumentStatusType = Literal["draft", "ready"]
CollectionCardinalityType = Literal[
    "zero_or_more",
    "one_or_more",
    "exactly_one",
]


class ValidationRuleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ValidationType
    message: str | None = None
    pattern: str | None = None
    format: str | None = None
    minimum: str | int | float | None = None
    maximum: str | int | float | None = None


class DocumentFieldModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    type: FieldType
    label: dict[str, str] | None = None
    value: Any | None = None
    rule: str | None = None
    rules: list[str] | None = None
    anchor: str | None = None
    pattern: str | None = None
    occurrence: OccurrenceType | None = None
    direction: DirectionType | None = None
    window_size: int | None = Field(default=None, gt=0, le=10000)
    validation: list[ValidationRuleModel] = Field(default_factory=list)


class DocumentCollectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cardinality: CollectionCardinalityType = "zero_or_more"
    start_pattern: str | None = None
    fields: list[DocumentFieldModel] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_field_names(self):
        field_names: set[str] = set()
        for field in self.fields:
            if field.name in field_names:
                raise ValueError(
                    "Duplicate collection field "
                    f"'{field.name}'"
                )
            field_names.add(field.name)
        return self


class DocumentProfileModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: list[DocumentFieldModel] = Field(default_factory=list)
    collections: dict[
        str,
        DocumentCollectionModel,
    ] | None = None


class DocumentTypeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: list[DocumentFieldModel] | None = None
    default_profile: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    common_fields: list[DocumentFieldModel] | None = None
    profiles: dict[str, DocumentProfileModel] | None = None
    collections: dict[
        str,
        DocumentCollectionModel,
    ] | None = None

    @model_validator(mode="after")
    def validate_configuration_shape(self):
        uses_legacy = self.fields is not None
        uses_profiles = (
            self.default_profile is not None
            or self.common_fields is not None
            or self.profiles is not None
        )

        if uses_legacy and uses_profiles:
            raise ValueError(
                "Legacy 'fields' cannot be combined with "
                "'default_profile', 'common_fields' or 'profiles'"
            )

        if not uses_legacy and not uses_profiles:
            raise ValueError(
                "Document type must define either 'fields' "
                "or profile-based configuration"
            )

        if uses_profiles and self.common_fields is None:
            self.common_fields = []

        if uses_profiles and self.profiles is None:
            self.profiles = {}

        if (
            self.default_profile is not None
            and self.default_profile not in self.profiles
        ):
            raise ValueError(
                "default_profile must reference an existing profile"
            )

        return self


class DocumentTypeMetadataModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: DocumentStatusType
    ready: bool
    field_count: int = Field(ge=0)


class CreateDocumentTypeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )


class RenameDocumentTypeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_document_type: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )


class AddFieldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: DocumentFieldModel


class UpdateFieldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: DocumentFieldModel


class ResolvedDocumentTypeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: str | None = None
    fields: list[DocumentFieldModel] = Field(default_factory=list)


class ConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_types: dict[str, DocumentTypeModel]
    resolved_document_types: dict[
        str,
        ResolvedDocumentTypeModel,
    ] = Field(default_factory=dict)
    document_type_metadata: dict[
        str,
        DocumentTypeMetadataModel,
    ] = Field(default_factory=dict)


class OperationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    message: str
