from copy import deepcopy

from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
)

from config_models import (
    AddCollectionRequest,
    AddFieldRequest,
    ConfigResponse,
    CreateDocumentTypeRequest,
    DocumentTypeModel,
    OperationResponse,
    RenameDocumentTypeRequest,
    UpdateCollectionRequest,
    UpdateFieldRequest,
)
from config_store import load_config, save_config
from config_validator import ConfigValidationError
from document_config_resolver import resolve_document_fields
from document_status import build_document_type_metadata


router = APIRouter(
    prefix="/api/v1/config",
    tags=["Configuration API v1"],
)


def save_validated_config(config: dict) -> None:
    try:
        save_config(config)

    except ConfigValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def get_document_type_or_404(
    config: dict,
    document_type: str,
) -> dict:
    document_config = config.get(document_type)

    if document_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Document type '{document_type}' "
                f"was not found"
            ),
        )

    return document_config


def find_field_index(
    fields: list[dict],
    field_name: str,
) -> int | None:
    for index, field in enumerate(fields):
        if field.get("name") == field_name:
            return index

    return None


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


# Profile-aware field endpoints

def get_profile_or_404(
    document_config: dict,
    profile_name: str,
) -> dict:
    profiles = document_config.get("profiles")

    if not isinstance(profiles, dict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document type does not use profile configuration",
        )

    profile_config = profiles.get(profile_name)

    if profile_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_name}' was not found",
        )

    return profile_config


def ensure_profile_based_config(
    document_config: dict,
) -> None:
    if "fields" in document_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document type uses legacy fields configuration",
        )


def ensure_field_name_available(
    document_config: dict,
    field_name: str,
    ignored_field_name: str | None = None,
) -> None:
    resolved_fields = resolve_document_fields(document_config)

    for field in resolved_fields:
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



@router.post(
    "/document-types/{document_type}/collections/{collection_name}",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_collection(
    document_type: str,
    collection_name: str,
    request: AddCollectionRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    collections = document_config.get("collections", {})
    if collection_name in collections:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Collection '{collection_name}' already exists "
                f"in document type '{document_type}'"
            ),
        )

    collection_data = request.collection.model_dump(
        exclude_none=True
    )
    updated_config = deepcopy(config)
    updated_config[document_type].setdefault(
        "collections",
        {},
    )[collection_name] = collection_data
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Collection '{collection_name}' added to "
            f"document type '{document_type}'"
        ),
    }


@router.put(
    "/document-types/{document_type}/collections/{collection_name}",
    response_model=OperationResponse,
)
def update_collection(
    document_type: str,
    collection_name: str,
    request: UpdateCollectionRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    collections = document_config.get("collections", {})
    if collection_name not in collections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Collection '{collection_name}' was not found "
                f"in document type '{document_type}'"
            ),
        )

    collection_data = request.collection.model_dump(
        exclude_none=True
    )
    updated_config = deepcopy(config)
    updated_config[document_type]["collections"][
        collection_name
    ] = collection_data
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Collection '{collection_name}' updated in "
            f"document type '{document_type}'"
        ),
    }


@router.delete(
    "/document-types/{document_type}/collections/{collection_name}",
    response_model=OperationResponse,
)
def delete_collection(
    document_type: str,
    collection_name: str,
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    collections = document_config.get("collections", {})
    if collection_name not in collections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Collection '{collection_name}' was not found "
                f"in document type '{document_type}'"
            ),
        )

    updated_config = deepcopy(config)
    updated_collections = updated_config[document_type][
        "collections"
    ]
    del updated_collections[collection_name]
    if not updated_collections:
        del updated_config[document_type]["collections"]
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Collection '{collection_name}' deleted from "
            f"document type '{document_type}'"
        ),
    }



def get_collection_or_404(
    document_config: dict,
    collection_name: str,
) -> dict:
    collections = document_config.get("collections", {})
    collection_config = collections.get(collection_name)
    if collection_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Collection '{collection_name}' was not found"
            ),
        )
    return collection_config


@router.post(
    "/document-types/{document_type}/collections/"
    "{collection_name}/fields",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_collection_field(
    document_type: str,
    collection_name: str,
    request: AddFieldRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    collection_config = get_collection_or_404(
        document_config=document_config,
        collection_name=collection_name,
    )
    fields = collection_config.get("fields", [])
    field_data = request.field.model_dump(
        exclude_none=True
    )
    field_name = field_data["name"]
    if find_field_index(fields, field_name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Field '{field_name}' already exists in "
                f"collection '{collection_name}'"
            ),
        )

    updated_config = deepcopy(config)
    updated_config[document_type]["collections"][
        collection_name
    ].setdefault("fields", []).append(field_data)
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Field '{field_name}' added to collection "
            f"'{collection_name}'"
        ),
    }


@router.put(
    "/document-types/{document_type}/collections/"
    "{collection_name}/fields/{field_name}",
    response_model=OperationResponse,
)
def update_collection_field(
    document_type: str,
    collection_name: str,
    field_name: str,
    request: UpdateFieldRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    collection_config = get_collection_or_404(
        document_config=document_config,
        collection_name=collection_name,
    )
    fields = collection_config.get("fields", [])
    field_index = find_field_index(fields, field_name)
    if field_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Field '{field_name}' was not found in "
                f"collection '{collection_name}'"
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
                    f"Field '{new_field_name}' already exists "
                    f"in collection '{collection_name}'"
                ),
            )

    updated_config = deepcopy(config)
    updated_config[document_type]["collections"][
        collection_name
    ]["fields"][field_index] = field_data
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Field '{field_name}' updated in collection "
            f"'{collection_name}'"
        ),
    }


@router.delete(
    "/document-types/{document_type}/collections/"
    "{collection_name}/fields/{field_name}",
    response_model=OperationResponse,
)
def delete_collection_field(
    document_type: str,
    collection_name: str,
    field_name: str,
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    collection_config = get_collection_or_404(
        document_config=document_config,
        collection_name=collection_name,
    )
    fields = collection_config.get("fields", [])
    field_index = find_field_index(fields, field_name)
    if field_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Field '{field_name}' was not found in "
                f"collection '{collection_name}'"
            ),
        )

    updated_config = deepcopy(config)
    del updated_config[document_type]["collections"][
        collection_name
    ]["fields"][field_index]
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Field '{field_name}' deleted from collection "
            f"'{collection_name}'"
        ),
    }



@router.post(
    "/document-types/{document_type}/profiles/{profile_name}/"
    "collections/{collection_name}",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_profile_collection(
    document_type: str,
    profile_name: str,
    collection_name: str,
    request: AddCollectionRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    ensure_profile_based_config(document_config)
    profile_config = get_profile_or_404(
        document_config=document_config,
        profile_name=profile_name,
    )
    collections = profile_config.get("collections", {})
    if collection_name in collections:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Collection '{collection_name}' already exists "
                f"in profile '{profile_name}'"
            ),
        )

    collection_data = request.collection.model_dump(
        exclude_none=True
    )
    updated_config = deepcopy(config)
    updated_config[document_type]["profiles"][
        profile_name
    ].setdefault("collections", {})[
        collection_name
    ] = collection_data
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Collection '{collection_name}' added to "
            f"profile '{profile_name}'"
        ),
    }


@router.put(
    "/document-types/{document_type}/profiles/{profile_name}/"
    "collections/{collection_name}",
    response_model=OperationResponse,
)
def update_profile_collection(
    document_type: str,
    profile_name: str,
    collection_name: str,
    request: UpdateCollectionRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    ensure_profile_based_config(document_config)
    profile_config = get_profile_or_404(
        document_config=document_config,
        profile_name=profile_name,
    )
    collections = profile_config.get("collections", {})
    if collection_name not in collections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Collection '{collection_name}' was not found "
                f"in profile '{profile_name}'"
            ),
        )

    collection_data = request.collection.model_dump(
        exclude_none=True
    )
    updated_config = deepcopy(config)
    updated_config[document_type]["profiles"][profile_name][
        "collections"
    ][collection_name] = collection_data
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Collection '{collection_name}' updated in "
            f"profile '{profile_name}'"
        ),
    }


@router.delete(
    "/document-types/{document_type}/profiles/{profile_name}/"
    "collections/{collection_name}",
    response_model=OperationResponse,
)
def delete_profile_collection(
    document_type: str,
    profile_name: str,
    collection_name: str,
):
    config = load_config()
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    ensure_profile_based_config(document_config)
    profile_config = get_profile_or_404(
        document_config=document_config,
        profile_name=profile_name,
    )
    collections = profile_config.get("collections", {})
    if collection_name not in collections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Collection '{collection_name}' was not found "
                f"in profile '{profile_name}'"
            ),
        )

    updated_config = deepcopy(config)
    updated_profile = updated_config[document_type]["profiles"][
        profile_name
    ]
    del updated_profile["collections"][collection_name]
    if not updated_profile["collections"]:
        del updated_profile["collections"]
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Collection '{collection_name}' deleted from "
            f"profile '{profile_name}'"
        ),
    }
