from copy import deepcopy

from fastapi import APIRouter, HTTPException, status

from config_models import (
    AddCollectionRequest,
    AddFieldRequest,
    OperationResponse,
    UpdateCollectionRequest,
    UpdateFieldRequest,
)
from config_api_helpers import (
    ensure_profile_based_config,
    find_field_index,
    get_document_type_or_404,
    get_profile_or_404,
    save_validated_config,
)
from config_collection_service import (
    get_collection_or_404,
    get_profile_collection_or_404,
    resolve_document_collection_target,
    resolve_profile_collection_target,
)
from config_store import load_config


router = APIRouter(
    prefix="/api/v1/config",
    tags=["Configuration API v1"],
)


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
    document_config, collections = (
        resolve_document_collection_target(
            config=config,
            document_type=document_type,
        )
    )
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
    document_config, collections = (
        resolve_document_collection_target(
            config=config,
            document_type=document_type,
        )
    )
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
    document_config, collections = (
        resolve_document_collection_target(
            config=config,
            document_type=document_type,
        )
    )
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
    document_config, profile_config, collections = (
        resolve_profile_collection_target(
            config=config,
            document_type=document_type,
            profile_name=profile_name,
        )
    )
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
    document_config, profile_config, collections = (
        resolve_profile_collection_target(
            config=config,
            document_type=document_type,
            profile_name=profile_name,
        )
    )
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
    document_config, profile_config, collections = (
        resolve_profile_collection_target(
            config=config,
            document_type=document_type,
            profile_name=profile_name,
        )
    )
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


@router.post(
    "/document-types/{document_type}/profiles/{profile_name}/"
    "collections/{collection_name}/fields",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_profile_collection_field(
    document_type: str,
    profile_name: str,
    collection_name: str,
    request: AddFieldRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(config, document_type)
    ensure_profile_based_config(document_config)
    profile_config = get_profile_or_404(document_config, profile_name)
    collection_config = get_profile_collection_or_404(
        profile_config,
        collection_name,
    )
    fields = collection_config.get("fields", [])
    field_data = request.field.model_dump(exclude_none=True)
    field_name = field_data["name"]
    if find_field_index(fields, field_name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Field '{field_name}' already exists in "
                f"profile collection '{collection_name}'"
            ),
        )
    updated_config = deepcopy(config)
    updated_config[document_type]["profiles"][profile_name][
        "collections"
    ][collection_name].setdefault("fields", []).append(field_data)
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Field '{field_name}' added to profile collection "
            f"'{collection_name}'"
        ),
    }


@router.put(
    "/document-types/{document_type}/profiles/{profile_name}/"
    "collections/{collection_name}/fields/{field_name}",
    response_model=OperationResponse,
)
def update_profile_collection_field(
    document_type: str,
    profile_name: str,
    collection_name: str,
    field_name: str,
    request: UpdateFieldRequest,
):
    config = load_config()
    document_config = get_document_type_or_404(config, document_type)
    ensure_profile_based_config(document_config)
    profile_config = get_profile_or_404(document_config, profile_name)
    collection_config = get_profile_collection_or_404(
        profile_config,
        collection_name,
    )
    fields = collection_config.get("fields", [])
    field_index = find_field_index(fields, field_name)
    if field_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Field '{field_name}' was not found in "
                f"profile collection '{collection_name}'"
            ),
        )
    field_data = request.field.model_dump(exclude_none=True)
    new_field_name = field_data["name"]
    if new_field_name != field_name:
        existing_index = find_field_index(fields, new_field_name)
        if existing_index is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Field '{new_field_name}' already exists in "
                    f"profile collection '{collection_name}'"
                ),
            )
    updated_config = deepcopy(config)
    updated_config[document_type]["profiles"][profile_name][
        "collections"
    ][collection_name]["fields"][field_index] = field_data
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Field '{field_name}' updated in profile collection "
            f"'{collection_name}'"
        ),
    }


@router.delete(
    "/document-types/{document_type}/profiles/{profile_name}/"
    "collections/{collection_name}/fields/{field_name}",
    response_model=OperationResponse,
)
def delete_profile_collection_field(
    document_type: str,
    profile_name: str,
    collection_name: str,
    field_name: str,
):
    config = load_config()
    document_config = get_document_type_or_404(config, document_type)
    ensure_profile_based_config(document_config)
    profile_config = get_profile_or_404(document_config, profile_name)
    collection_config = get_profile_collection_or_404(
        profile_config,
        collection_name,
    )
    fields = collection_config.get("fields", [])
    field_index = find_field_index(fields, field_name)
    if field_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Field '{field_name}' was not found in "
                f"profile collection '{collection_name}'"
            ),
        )
    updated_config = deepcopy(config)
    del updated_config[document_type]["profiles"][profile_name][
        "collections"
    ][collection_name]["fields"][field_index]
    save_validated_config(updated_config)
    return {
        "status": "ok",
        "message": (
            f"Field '{field_name}' deleted from profile collection "
            f"'{collection_name}'"
        ),
    }
