
from fastapi import APIRouter, Depends, HTTPException, status

from config_models import (
    AddCollectionRequest,
    AddFieldRequest,
    OperationResponse,
    UpdateCollectionRequest,
    UpdateFieldRequest,
)
from config_collection_service import (
    add_document_collection,
    add_document_collection_field as add_document_field,
    add_profile_collection_field as add_profile_field,
    add_profile_collection_mutation,
    delete_document_collection,
    delete_document_collection_field as delete_document_field,
    delete_profile_collection_field as delete_profile_field,
    delete_profile_collection_mutation,
    update_document_collection,
    update_document_collection_field as update_document_field,
    update_profile_collection_field as update_profile_field,
    update_profile_collection_mutation,
)
from config_store import load_config
from security_scopes import enforce_config_scope


router = APIRouter(
    prefix="/api/v1/config",
    tags=["Configuration API v1"],
    dependencies=[Depends(enforce_config_scope)],
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
    collection_data = request.collection.model_dump(
        exclude_none=True
    )
    add_document_collection(
        config=config,
        document_type=document_type,
        collection_name=collection_name,
        collection_data=collection_data,
    )
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
    collection_data = request.collection.model_dump(
        exclude_none=True
    )
    update_document_collection(
        config=config,
        document_type=document_type,
        collection_name=collection_name,
        collection_data=collection_data,
    )
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
    delete_document_collection(
        config=config,
        document_type=document_type,
        collection_name=collection_name,
    )
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
    field_data = request.field.model_dump(exclude_none=True)
    field_name = field_data["name"]
    add_document_field(
        config=config,
        document_type=document_type,
        collection_name=collection_name,
        field_data=field_data,
    )
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
    field_data = request.field.model_dump(exclude_none=True)
    update_document_field(
        config=config,
        document_type=document_type,
        collection_name=collection_name,
        field_name=field_name,
        field_data=field_data,
    )
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
    delete_document_field(
        config=config,
        document_type=document_type,
        collection_name=collection_name,
        field_name=field_name,
    )
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
    collection_data = request.collection.model_dump(
        exclude_none=True
    )
    add_profile_collection_mutation(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
        collection_name=collection_name,
        collection_data=collection_data,
    )
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
    collection_data = request.collection.model_dump(
        exclude_none=True
    )
    update_profile_collection_mutation(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
        collection_name=collection_name,
        collection_data=collection_data,
    )
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
    delete_profile_collection_mutation(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
        collection_name=collection_name,
    )
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
    field_data = request.field.model_dump(exclude_none=True)
    field_name = field_data["name"]
    add_profile_field(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
        collection_name=collection_name,
        field_data=field_data,
    )
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
    field_data = request.field.model_dump(exclude_none=True)
    update_profile_field(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
        collection_name=collection_name,
        field_name=field_name,
        field_data=field_data,
    )
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
    delete_profile_field(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
        collection_name=collection_name,
        field_name=field_name,
    )
    return {
        "status": "ok",
        "message": (
            f"Field '{field_name}' deleted from profile collection "
            f"'{collection_name}'"
        ),
    }
