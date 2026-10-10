import re
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
ConfigurationModeType = Literal["legacy", "profile"]
CollectionCardinalityType = Literal[
    "zero_or_more",
    "one_or_more",
    "exactly_one",
]


class ValidationRuleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ValidationType = Field(
        description="Validation rule type: required, regex, date, or decimal.",
        examples=["required"],
    )
    message: str | None = Field(
        default=None,
        description="Optional human-readable validation failure message.",
        examples=["Synthetic invoice number is required"],
    )
    pattern: str | None = Field(
        default=None,
        description="Regular expression used by a regex validation rule.",
        examples=[r"^INV-SYNTH-[0-9]+$"],
    )
    format: str | None = Field(
        default=None,
        description="Expected date format used by a date validation rule.",
        examples=["%Y-%m-%d"],
    )
    minimum: str | int | float | None = Field(
        default=None,
        description="Inclusive minimum used by a decimal validation rule.",
        examples=["0.01"],
    )
    maximum: str | int | float | None = Field(
        default=None,
        description="Inclusive maximum used by a decimal validation rule.",
        examples=["999999.99"],
    )


class DocumentFieldModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Unique extraction field name within its configuration scope.",
        examples=["synthetic_invoice_number"],
    )
    type: FieldType = Field(
        description=(
            "Extraction strategy: constant, regex, regex_list, nearby, or llm."
        ),
        examples=["regex"],
    )
    label: dict[str, str] | None = Field(
        default=None,
        description="Optional localized display labels keyed by language code.",
        examples=[{"en": "Synthetic invoice number"}],
    )
    value: Any | None = Field(
        default=None,
        description="Constant value used when type is constant.",
        examples=["synthetic"],
    )
    rule: str | None = Field(
        default=None,
        description="Single extraction rule used by regex or nearby strategies.",
        examples=[r"Invoice\s+(INV-SYNTH-[0-9]+)"],
    )
    rules: list[str] | None = Field(
        default=None,
        description="Ordered extraction rules used by the regex_list strategy.",
        examples=[[r"Invoice\s+(INV-SYNTH-[0-9]+)"]],
    )
    anchor: str | None = Field(
        default=None,
        description="Anchor text used by the nearby extraction strategy.",
        examples=["Synthetic invoice"],
    )
    pattern: str | None = Field(
        default=None,
        description="Pattern applied within the nearby extraction window.",
        examples=[r"INV-SYNTH-[0-9]+"],
    )
    occurrence: OccurrenceType | None = Field(
        default=None,
        description="Selects the first or last matching occurrence.",
        examples=["last"],
    )
    direction: DirectionType | None = Field(
        default=None,
        description="Nearby search direction: before, after, or both.",
        examples=["after"],
    )
    window_size: int | None = Field(
        default=None,
        gt=0,
        le=10000,
        description="Maximum nearby search window size in characters.",
        examples=[250],
    )
    validation: list[ValidationRuleModel] = Field(
        default_factory=list,
        description="Validation rules applied to the extracted field value."
    )

class CollectionItemValidationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["difference_equals"] = Field(
        description="Collection item validation type.",
        examples=["difference_equals"],
    )
    minuend: str = Field(
        min_length=1,
        max_length=100,
        description="Field subtracted from when checking the difference.",
        examples=["current_reading"],
    )
    subtrahend: str = Field(
        min_length=1,
        max_length=100,
        description="Field subtracted from the minuend.",
        examples=["previous_reading"],
    )
    result: str = Field(
        min_length=1,
        max_length=100,
        description="Field expected to equal minuend minus subtrahend.",
        examples=["difference"],
    )
    message: str | None = Field(
        default=None,
        description="Optional validation failure message.",
        examples=["Synthetic reading difference is invalid"],
    )


class DocumentCollectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cardinality: CollectionCardinalityType = Field(
        default="zero_or_more",
        description=(
            "Required item count: zero_or_more, one_or_more, or exactly_one."
        ),
        examples=["one_or_more"],
    )
    start_pattern: str | None = Field(
        default=None,
        description="Optional pattern marking the start of each collection item.",
        examples=[r"^Synthetic meter"],
    )
    fields: list[DocumentFieldModel] = Field(
        default_factory=list,
        description="Extraction fields evaluated for every collection item."
    )
    item_validations: list[
        CollectionItemValidationModel
    ] = Field(
        default_factory=list,
        description="Validations evaluated within each collection item."
    )

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

        for validation in self.item_validations:
            referenced_fields = {
                validation.minuend,
                validation.subtrahend,
                validation.result,
            }

            missing_fields = (
                referenced_fields - field_names
            )

            if missing_fields:
                raise ValueError(
                    "Collection item validation references "
                    "unknown fields: "
                    f"{sorted(missing_fields)}"
                )

        return self

class CollectionSummaryValidationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["collection_sum_equals_field"] = Field(
        description="Collection summary validation type.",
        examples=["collection_sum_equals_field"],
    )
    collection: str = Field(
        min_length=1,
        max_length=100,
        description="Collection whose item values are summed.",
        examples=["synthetic_services"],
    )
    item_field: str = Field(
        min_length=1,
        max_length=100,
        description="Numeric collection item field included in the sum.",
        examples=["amount"],
    )
    target_field: str = Field(
        min_length=1,
        max_length=100,
        description="Document field expected to equal the collection sum.",
        examples=["synthetic_total_amount"],
    )
    message: str | None = Field(
        default=None,
        description="Optional validation failure message.",
        examples=["Synthetic service sum does not match the total"],
    )


class SupplierMatchRuleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Stable evidence code identifying one supplier match rule.",
        examples=["synthetic_provider_company"],
    )
    pattern: str = Field(
        min_length=1,
        description="Regular expression matched against normalized OCR text.",
        examples=[r"\bsynthetic provider ead\b"],
    )

    @model_validator(mode="after")
    def validate_pattern(self):
        try:
            re.compile(self.pattern)
        except re.error as exc:
            raise ValueError(
                f"Supplier matching pattern contains invalid regex: {exc}"
            ) from exc
        return self


class SupplierMatchingModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    any_of: list[SupplierMatchRuleModel] = Field(
        min_length=1,
        description=(
            "Supplier match rules where any matching pattern selects the profile."
        ),
    )

    @model_validator(mode="after")
    def validate_unique_codes(self):
        codes = [rule.code for rule in self.any_of]
        if len(codes) != len(set(codes)):
            raise ValueError("Supplier matching evidence codes must be unique")
        return self


class DocumentProfileModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matching: SupplierMatchingModel | None = Field(
        default=None,
        description="Optional configuration-driven supplier matching rules.",
    )
    fields: list[DocumentFieldModel] = Field(
        default_factory=list,
        description="Profile-specific extraction fields."
    )
    collections: dict[
        str,
        DocumentCollectionModel,
    ] | None = Field(
        default=None,
        description="Profile-specific collections keyed by collection name."
    )
    summary_validations: list[
        CollectionSummaryValidationModel
    ] = Field(
        default_factory=list,
        description="Cross-field collection summary validations."
    )


class DocumentTypeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: list[DocumentFieldModel] | None = Field(
        default=None,
        description="Legacy-mode extraction fields."
    )
    default_profile: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Default profile used to resolve effective fields.",
        examples=["synthetic_provider"],
    )
    common_fields: list[DocumentFieldModel] | None = Field(
        default=None,
        description="Fields shared by every profile."
    )
    profiles: dict[str, DocumentProfileModel] | None = Field(
        default=None,
        description="Profile configurations keyed by profile name."
    )
    collections: dict[
        str,
        DocumentCollectionModel,
    ] | None = Field(
        default=None,
        description="Document-level collections keyed by collection name."
    )

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

    status: DocumentStatusType = Field(
        description="Configuration lifecycle status: draft or ready.",
        examples=["ready"],
    )
    ready: bool = Field(
        description="Whether the document type has usable extraction fields.",
        examples=[True],
    )
    field_count: int = Field(
        ge=0,
        description="Number of resolved extraction fields.",
        examples=[5],
    )


class CreateDocumentTypeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="New document-type configuration key.",
        examples=["synthetic_contract"],
    )
    configuration_mode: ConfigurationModeType = Field(
        default="legacy",
        description=(
            "Initial configuration shape: legacy creates a fields list; "
            "profile creates common fields, profiles, and collections."
        ),
        examples=["profile"],
    )


class UpdateDefaultProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description=(
            "Existing profile name to assign as the document type default."
        ),
        examples=["synthetic_provider"],
    )


class AddProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: DocumentProfileModel = Field(
        description="Complete profile configuration to add."
    )


class UpdateProfileMatchingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matching: SupplierMatchingModel = Field(
        description=(
            "Complete replacement supplier matching configuration "
            "for one existing profile."
        )
    )


class RenameDocumentTypeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_document_type: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Replacement document-type configuration key.",
        examples=["synthetic_agreement"],
    )


class AddFieldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: DocumentFieldModel = Field(
        description="Extraction field configuration to add."
    )


class UpdateFieldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: DocumentFieldModel = Field(
        description="Complete replacement extraction field configuration."
    )


class AddCollectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collection: DocumentCollectionModel = Field(
        description="Complete collection configuration to add."
    )


class UpdateCollectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collection: DocumentCollectionModel = Field(
        description="Complete replacement collection configuration."
    )


class AddSummaryValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validation: CollectionSummaryValidationModel = Field(
        description="Profile summary validation configuration to add."
    )


class UpdateSummaryValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validation: CollectionSummaryValidationModel = Field(
        description=(
            "Complete replacement profile summary validation."
        )
    )


class ResolvedDocumentTypeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: str | None = Field(
        default=None,
        description="Default profile used to resolve the effective fields."
    )
    fields: list[DocumentFieldModel] = Field(
        default_factory=list,
        description="Effective extraction fields after profile resolution."
    )


class ConfigurationRestoreDryRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        description="Configuration snapshot schema version."
    )
    revision: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 revision declared by the snapshot.",
    )
    configuration: dict[str, dict[str, Any]] = Field(
        description="Complete candidate configuration to validate."
    )


class ConfigurationRestoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot: ConfigurationRestoreDryRunRequest = Field(
        description="Validated configuration snapshot to restore."
    )
    expected_current_revision: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Current configuration revision expected by the caller.",
    )
    confirmation: Literal["RESTORE"] = Field(
        description="Explicit destructive-operation confirmation."
    )


class ConfigurationRestoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    restore_applied: bool
    previous_revision: str = Field(min_length=64, max_length=64)
    restored_revision: str = Field(min_length=64, max_length=64)
    backup_revision: str = Field(min_length=64, max_length=64)
    backup_identifier: str
    configuration_write: Literal["PERFORMED"]


class ConfigurationRestoreDryRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool = Field(
        description="Whether the restore candidate is valid."
    )
    snapshot_revision: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Validated revision of the candidate configuration.",
    )
    current_revision: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Revision of the currently stored configuration.",
    )
    changes_detected: bool = Field(
        description="Whether the candidate differs from current configuration."
    )
    document_types: list[str] = Field(
        description="Sorted document-type keys in the candidate configuration."
    )


class ConfigurationSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        description="Configuration snapshot schema version."
    )
    revision: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 revision of the snapshot configuration.",
        examples=["0" * 64],
    )
    configuration: dict[str, dict] = Field(
        description=(
            "Complete stored configuration included in the snapshot without "
            "normalizing optional fields or inserting model defaults."
        )
    )


class ConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description=(
            "SHA-256 revision of the complete stored configuration."
        ),
        examples=["0" * 64],
    )
    document_types: dict[str, DocumentTypeModel] = Field(
        description="Stored document-type configurations keyed by name."
    )
    resolved_document_types: dict[
        str,
        ResolvedDocumentTypeModel,
    ] = Field(
        default_factory=dict,
        description="Effective default-profile fields keyed by document type."
    )
    document_type_metadata: dict[
        str,
        DocumentTypeMetadataModel,
    ] = Field(
        default_factory=dict,
        description="Readiness metadata keyed by document type."
    )


class OperationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = Field(
        description="Successful configuration operation status.",
        examples=["ok"],
    )
    message: str = Field(
        description="Human-readable result of the configuration operation.",
        examples=["Document type 'synthetic_contract' created"],
    )
