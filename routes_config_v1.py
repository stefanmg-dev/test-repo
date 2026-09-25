from copy import deepcopy

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Response,
    status,
)

from config_models import (
    AddFieldRequest,
    AddProfileRequest,
    ConfigResponse,
    CreateDocumentTypeRequest,
    DocumentTypeModel,
    OperationResponse,
    RenameDocumentTypeRequest,
    UpdateFieldRequest,
)
from config_api_helpers import (
    ensure_profile_based_config,
    find_field_index,
    get_document_type_or_404,
    get_profile_or_404,
    save_validated_config,
)
from config_store import load_config
from security_scopes import enforce_config_scope
from document_config_resolver import resolve_document_fields
from document_status import build_document_type_metadata


router = APIRouter(
    prefix="/api/v1/config",
    tags=["Configuration API v1"],
    dependencies=[Depends(enforce_config_scope)],
)


def build_all_document_type_metadata(
    config: dict,
) -> dict:
    return {
        document_type: build_document_type_metadata(
            document_config
        )
        for document_type, document_config
        in config.items()
    }


def build_resolved_document_types(
    config: dict,
) -> dict:
    resolved_document_types = {}

    for document_type, document_config in config.items():
        resolved_document_types[document_type] = {
            "profile": document_config.get("default_profile"),
            "fields": resolve_document_fields(document_config),
        }

    return resolved_document_types


@router.get(
    "/document-types",
    response_model=ConfigResponse,
    response_model_exclude_none=True,
)
def get_document_types():
    config = load_config()

    document_type_metadata = (
        build_all_document_type_metadata(config)
    )

    resolved_document_types = (
        build_resolved_document_types(config)
    )

    return {
        "document_types": config,
        "resolved_document_types": (
            resolved_document_types
        ),
        "document_type_metadata": (
            document_type_metadata
        ),
    }


@router.get(
    "/document-types/{document_type}",
    response_model=DocumentTypeModel,
    response_model_exclude_none=True,
)
def get_document_type(document_type: str):
    config = load_config()

    return get_document_type_or_404(
        config=config,
        document_type=document_type,
    )


@router.post(
    "/document-types",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document_type(
    request: CreateDocumentTypeRequest,
):
    config = load_config()

    document_type = request.document_type

    if document_type in config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Document type '{document_type}' "
                f"already exists"
            ),
        )

    updated_config = deepcopy(config)

    if request.configuration_mode == "profile":
        updated_config[document_type] = {
            "common_fields": [],
            "profiles": {},
            "collections": {},
        }
    else:
        updated_config[document_type] = {
            "fields": []
        }

    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": (
            f"Document type '{document_type}' created"
        ),
    }


@router.put(
    "/document-types/{document_type}/rename",
    response_model=OperationResponse,
)
def rename_document_type(
    document_type: str,
    request: RenameDocumentTypeRequest,
):
    config = load_config()

    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )

    new_document_type = request.new_document_type

    if new_document_type == document_type:
        return {
            "status": "ok",
            "message": (
                f"Document type remains "
                f"'{document_type}'"
            ),
        }

    if new_document_type in config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Document type '{new_document_type}' "
                f"already exists"
            ),
        )

    updated_config = deepcopy(config)

    updated_config[new_document_type] = deepcopy(
        document_config
    )

    del updated_config[document_type]

    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": (
            f"Document type '{document_type}' renamed "
            f"to '{new_document_type}'"
        ),
    }


@router.delete(
    "/document-types/{document_type}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document_type(
    document_type: str,
):
    config = load_config()

    get_document_type_or_404(
        config=config,
        document_type=document_type,
    )

    updated_config = deepcopy(config)

    del updated_config[document_type]

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The last remaining document type "
                "cannot be deleted"
            ),
        )

    save_validated_config(updated_config)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/document-types/{document_type}/fields",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_field(
    document_type: str,
    request: AddFieldRequest,
):
    config = load_config()

    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )

    fields = document_config.get(
        "fields",
        []
    )

    field_data = request.field.model_dump(
        exclude_none=True
    )

    field_name = field_data["name"]

    if find_field_index(
        fields,
        field_name,
    ) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Field '{field_name}' already exists "
                f"in document type '{document_type}'"
            ),
        )

    updated_config = deepcopy(config)

    updated_config[document_type]["fields"].append(
        field_data
    )

    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": (
            f"Field '{field_name}' added to "
            f"document type '{document_type}'"
        ),
    }


@router.put(
    "/document-types/{document_type}/fields/{field_name}",
    response_model=OperationResponse,
)
def update_field(
    document_type: str,
    field_name: str,
    request: UpdateFieldRequest,
):
    config = load_config()

    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )

    fields = document_config.get(
        "fields",
        []
    )

    field_index = find_field_index(
        fields=fields,
        field_name=field_name,
    )

    if field_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Field '{field_name}' was not found "
                f"in document type '{document_type}'"
            ),
        )

    field_data = request.field.model_dump(
        exclude_none=True
    )

    new_field_name = field_data["name"]

    if new_field_name != field_name:
        existing_index = find_field_index(
            fields=fields,
            field_name=new_field_name,
        )

        if existing_index is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Field '{new_field_name}' already "
                    f"exists in document type "
                    f"'{document_type}'"
                ),
            )

    updated_config = deepcopy(config)

    updated_config[document_type]["fields"][
        field_index
    ] = field_data

    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": (
            f"Field '{field_name}' updated in "
            f"document type '{document_type}'"
        ),
    }


@router.delete(
    "/document-types/{document_type}/fields/{field_name}",
    response_model=OperationResponse,
)
def delete_field(
    document_type: str,
    field_name: str,
):
    config = load_config()

    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )

    fields = document_config.get(
        "fields",
        []
    )

    field_index = find_field_index(
        fields=fields,
        field_name=field_name,
    )

    if field_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Field '{field_name}' was not found "
                f"in document type '{document_type}'"
            ),
        )

    updated_config = deepcopy(config)

    del updated_config[document_type]["fields"][
        field_index
    ]

    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": (
            f"Field '{field_name}' deleted from "
            f"document type '{document_type}'"
        ),
    }


@router.post(
    "/document-types/{document_type}/profiles/{profile_name}",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_profile(
    document_type: str,
    request: AddProfileRequest,
    profile_name: str = Path(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    ),
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    ensure_profile_based_config(document_config)

    profiles = document_config.get("profiles", {})
    if profile_name in profiles:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Profile '{profile_name}' already exists",
        )

    profile_data = request.profile.model_dump(
        exclude_none=True
    )
    updated_config = deepcopy(config)
    updated_config[document_type]["profiles"][
        profile_name
    ] = profile_data
    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": f"Profile '{profile_name}' added",
    }


@router.delete(
    "/document-types/{document_type}/profiles/{profile_name}",
    response_model=OperationResponse,
)
def delete_profile(
    document_type: str,
    profile_name: str = Path(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    ),
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    ensure_profile_based_config(document_config)
    get_profile_or_404(document_config, profile_name)

    if document_config.get("default_profile") == profile_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Profile '{profile_name}' is the default profile "
                "and cannot be deleted"
            ),
        )

    updated_config = deepcopy(config)
    del updated_config[document_type]["profiles"][
        profile_name
    ]
    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": f"Profile '{profile_name}' deleted",
    }


# Profile-aware field endpoints

def ensure_field_name_available(
    document_config: dict,
    field_name: str,
    ignored_field_name: str | None = None,
) -> None:
    field_groups = [
        document_config.get("common_fields", []),
    ]

    profiles = document_config.get("profiles", {})
    if isinstance(profiles, dict):
        field_groups.extend(
            profile_config.get("fields", [])
            for profile_config in profiles.values()
            if isinstance(profile_config, dict)
        )

    for fields in field_groups:
        for field in fields:
            existing_name = field.get("name")
            if existing_name == ignored_field_name:
                continue
            if existing_name == field_name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Field '{field_name}' already exists "
                        "in the resolved document configuration"
                    ),
                )


@router.post(
    "/document-types/{document_type}/common-fields",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_common_field(
    document_type: str,
    request: AddFieldRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(config, document_type)
    ensure_profile_based_config(document_config)

    field_data = request.field.model_dump(exclude_none=True)
    field_name = field_data["name"]
    ensure_field_name_available(document_config, field_name)

    updated_config = deepcopy(config)
    updated_config[document_type].setdefault("common_fields", []).append(
        field_data
    )
    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": f"Common field '{field_name}' added",
    }


@router.put(
    "/document-types/{document_type}/common-fields/{field_name}",
    response_model=OperationResponse,
)
def update_common_field(
    document_type: str,
    field_name: str,
    request: UpdateFieldRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(config, document_type)
    ensure_profile_based_config(document_config)
    fields = document_config.get("common_fields", [])
    field_index = find_field_index(fields, field_name)

    if field_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Common field '{field_name}' was not found",
        )

    field_data = request.field.model_dump(exclude_none=True)
    ensure_field_name_available(
        document_config,
        field_data["name"],
        ignored_field_name=field_name,
    )

    updated_config = deepcopy(config)
    updated_config[document_type]["common_fields"][field_index] = field_data
    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": f"Common field '{field_name}' updated",
    }


@router.delete(
    "/document-types/{document_type}/common-fields/{field_name}",
    response_model=OperationResponse,
)
def delete_common_field(
    document_type: str,
    field_name: str,
):
    config = load_config()
    document_config = get_document_type_or_404(config, document_type)
    ensure_profile_based_config(document_config)
    fields = document_config.get("common_fields", [])
    field_index = find_field_index(fields, field_name)

    if field_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Common field '{field_name}' was not found",
        )

    updated_config = deepcopy(config)
    del updated_config[document_type]["common_fields"][field_index]
    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": f"Common field '{field_name}' deleted",
    }


@router.post(
    "/document-types/{document_type}/profiles/{profile_name}/fields",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_profile_field(
    document_type: str,
    profile_name: str,
    request: AddFieldRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(config, document_type)
    ensure_profile_based_config(document_config)
    get_profile_or_404(document_config, profile_name)

    field_data = request.field.model_dump(exclude_none=True)
    field_name = field_data["name"]
    ensure_field_name_available(document_config, field_name)

    updated_config = deepcopy(config)
    updated_config[document_type]["profiles"][profile_name]["fields"].append(
        field_data
    )
    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": f"Field '{field_name}' added to profile '{profile_name}'",
    }


@router.put(
    "/document-types/{document_type}/profiles/{profile_name}/fields/{field_name}",
    response_model=OperationResponse,
)
def update_profile_field(
    document_type: str,
    profile_name: str,
    field_name: str,
    request: UpdateFieldRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(config, document_type)
    ensure_profile_based_config(document_config)
    profile_config = get_profile_or_404(document_config, profile_name)
    fields = profile_config.get("fields", [])
    field_index = find_field_index(fields, field_name)

    if field_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Field '{field_name}' was not found "
                f"in profile '{profile_name}'"
            ),
        )

    field_data = request.field.model_dump(exclude_none=True)
    ensure_field_name_available(
        document_config,
        field_data["name"],
        ignored_field_name=field_name,
    )

    updated_config = deepcopy(config)
    updated_config[document_type]["profiles"][profile_name]["fields"][
        field_index
    ] = field_data
    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": f"Field '{field_name}' updated in profile '{profile_name}'",
    }


@router.delete(
    "/document-types/{document_type}/profiles/{profile_name}/fields/{field_name}",
    response_model=OperationResponse,
)
def delete_profile_field(
    document_type: str,
    profile_name: str,
    field_name: str,
):
    config = load_config()
    document_config = get_document_type_or_404(config, document_type)
    ensure_profile_based_config(document_config)
    profile_config = get_profile_or_404(document_config, profile_name)
    fields = profile_config.get("fields", [])
    field_index = find_field_index(fields, field_name)

    if field_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Field '{field_name}' was not found "
                f"in profile '{profile_name}'"
            ),
        )

    updated_config = deepcopy(config)
    del updated_config[document_type]["profiles"][profile_name]["fields"][
        field_index
    ]
    save_validated_config(updated_config)

    return {
        "status": "ok",
        "message": f"Field '{field_name}' deleted from profile '{profile_name}'",
    }
