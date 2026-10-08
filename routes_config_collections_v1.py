
from fastapi import APIRouter, Depends, HTTPException, Path, status

from config_models import (
    AddCollectionRequest,
    AddFieldRequest,
    AddSummaryValidationRequest,
    OperationResponse,
    UpdateCollectionRequest,
    UpdateFieldRequest,
    UpdateSummaryValidationRequest,
)
from config_collection_service import (
    add_document_collection,
    add_document_collection_field as add_document_field,
    add_profile_collection_field as add_profile_field,
    add_profile_collection_mutation,
    add_profile_summary_validation,
    delete_document_collection,
    delete_document_collection_field as delete_document_field,
    delete_profile_collection_field as delete_profile_field,
    delete_profile_collection_mutation,
    delete_profile_summary_validation,
    update_document_collection,
    update_document_collection_field as update_document_field,
    update_profile_collection_field as update_profile_field,
    update_profile_collection_mutation,
    update_profile_summary_validation,
)
from config_store import load_config
from configuration_revision import enforce_configuration_revision
from security_scopes import enforce_config_scope


router = APIRouter(
    prefix="/api/v1/config",
    tags=["Configuration API v1"],
    dependencies=[
        Depends(enforce_config_scope),
        Depends(enforce_configuration_revision),
    ],
)


@router.post(
    "/document-types/{document_type}/collections/{collection_name}",
    summary="Add a document collection",
    description=(
        "Adds one uniquely named repeating collection to a document type. "
        "Authenticated requests require the config:write scope."
    ),
    response_description="Collection creation result.",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_collection(
    request: AddCollectionRequest,
    document_type: str = Path(..., description="Document-type configuration key."),
    collection_name: str = Path(..., description="New collection name."),
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
    summary="Replace a document collection",
    description=(
        "Completely replaces one existing document-level collection. "
        "Authenticated requests require the config:write scope."
    ),
    response_description="Collection update result.",
    response_model=OperationResponse,
)
def update_collection(
    request: UpdateCollectionRequest,
    document_type: str = Path(..., description="Document-type configuration key."),
    collection_name: str = Path(..., description="Existing collection name."),
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
    summary="Delete a document collection",
    description=(
        "Deletes one existing document-level collection. Authenticated "
        "requests require the config:write scope."
    ),
    response_description="Collection deletion result.",
    response_model=OperationResponse,
)
def delete_collection(
    document_type: str = Path(..., description="Document-type configuration key."),
    collection_name: str = Path(..., description="Existing collection name."),
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
    summary="Add a document collection field",
    description=(
        "Adds one uniquely named extraction field to an existing document "
        "collection. Authenticated requests require the config:write scope."
    ),
    response_description="Collection field creation result.",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_collection_field(
    request: AddFieldRequest,
    document_type: str = Path(..., description="Document-type configuration key."),
    collection_name: str = Path(..., description="Existing collection name."),
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
    summary="Replace a document collection field",
    description=(
        "Completely replaces one existing collection field and may rename it "
        "when the new name is unique. Authenticated requests require the "
        "config:write scope."
    ),
    response_description="Collection field update result.",
    response_model=OperationResponse,
)
def update_collection_field(
    request: UpdateFieldRequest,
    document_type: str = Path(..., description="Document-type configuration key."),
    collection_name: str = Path(..., description="Existing collection name."),
    field_name: str = Path(..., description="Existing collection field name."),
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
    summary="Delete a document collection field",
    description=(
        "Deletes one existing field from an existing document collection. "
        "Authenticated requests require the config:write scope."
    ),
    response_description="Collection field deletion result.",
    response_model=OperationResponse,
)
def delete_collection_field(
    document_type: str = Path(..., description="Document-type configuration key."),
    collection_name: str = Path(..., description="Existing collection name."),
    field_name: str = Path(..., description="Existing collection field name."),
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
    summary="Add a profile collection",
    description=(
        "Adds one uniquely named repeating collection to an existing profile. "
        "Authenticated requests require the config:write scope."
    ),
    response_description="Profile collection creation result.",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_profile_collection(
    request: AddCollectionRequest,
    document_type: str = Path(..., description="Profile-based document-type key."),
    profile_name: str = Path(..., description="Existing profile name."),
    collection_name: str = Path(..., description="New profile collection name."),
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
    summary="Replace a profile collection",
    description=(
        "Completely replaces one existing profile collection. Authenticated "
        "requests require the config:write scope."
    ),
    response_description="Profile collection update result.",
    response_model=OperationResponse,
)
def update_profile_collection(
    request: UpdateCollectionRequest,
    document_type: str = Path(..., description="Profile-based document-type key."),
    profile_name: str = Path(..., description="Existing profile name."),
    collection_name: str = Path(..., description="Existing profile collection name."),
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
    summary="Delete a profile collection",
    description=(
        "Deletes one existing collection from an existing profile. "
        "Authenticated requests require the config:write scope."
    ),
    response_description="Profile collection deletion result.",
    response_model=OperationResponse,
)
def delete_profile_collection(
    document_type: str = Path(..., description="Profile-based document-type key."),
    profile_name: str = Path(..., description="Existing profile name."),
    collection_name: str = Path(..., description="Existing profile collection name."),
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
    summary="Add a profile collection field",
    description=(
        "Adds one uniquely named extraction field to an existing profile "
        "collection. Authenticated requests require the config:write scope."
    ),
    response_description="Profile collection field creation result.",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_profile_collection_field(
    request: AddFieldRequest,
    document_type: str = Path(..., description="Profile-based document-type key."),
    profile_name: str = Path(..., description="Existing profile name."),
    collection_name: str = Path(..., description="Existing profile collection name."),
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
    summary="Replace a profile collection field",
    description=(
        "Completely replaces one existing profile collection field and may "
        "rename it when the new name is unique. Authenticated requests "
        "require the config:write scope."
    ),
    response_description="Profile collection field update result.",
    response_model=OperationResponse,
)
def update_profile_collection_field(
    request: UpdateFieldRequest,
    document_type: str = Path(..., description="Profile-based document-type key."),
    profile_name: str = Path(..., description="Existing profile name."),
    collection_name: str = Path(..., description="Existing profile collection name."),
    field_name: str = Path(..., description="Existing profile collection field name."),
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
    summary="Delete a profile collection field",
    description=(
        "Deletes one existing field from an existing profile collection. "
        "Authenticated requests require the config:write scope."
    ),
    response_description="Profile collection field deletion result.",
    response_model=OperationResponse,
)
def delete_profile_collection_field(
    document_type: str = Path(..., description="Profile-based document-type key."),
    profile_name: str = Path(..., description="Existing profile name."),
    collection_name: str = Path(..., description="Existing profile collection name."),
    field_name: str = Path(..., description="Existing profile collection field name."),
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

@router.post(
    "/document-types/{document_type}/profiles/{profile_name}/"
    "summary-validations",
    summary="Add a profile summary validation",
    description=(
        "Adds one collection summary validation to an existing profile. "
        "Authenticated requests require the config:write scope."
    ),
    response_description="Summary validation creation result.",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_summary_validation(
    request: AddSummaryValidationRequest,
    document_type: str = Path(..., description="Profile-based document-type key."),
    profile_name: str = Path(..., description="Existing profile name."),
):
    config = load_config()
    add_profile_summary_validation(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
        validation_data=request.validation.model_dump(exclude_none=True),
    )
    return {
        "status": "ok",
        "message": f"Summary validation added to profile '{profile_name}'",
    }


@router.put(
    "/document-types/{document_type}/profiles/{profile_name}/"
    "summary-validations/{validation_index}",
    summary="Replace a profile summary validation",
    description=(
        "Completely replaces one profile summary validation by index. "
        "Authenticated requests require the config:write scope."
    ),
    response_description="Summary validation update result.",
    response_model=OperationResponse,
)
def update_summary_validation(
    request: UpdateSummaryValidationRequest,
    document_type: str = Path(..., description="Profile-based document-type key."),
    profile_name: str = Path(..., description="Existing profile name."),
    validation_index: int = Path(..., ge=0, description="Existing validation index."),
):
    config = load_config()
    update_profile_summary_validation(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
        validation_index=validation_index,
        validation_data=request.validation.model_dump(exclude_none=True),
    )
    return {
        "status": "ok",
        "message": (
            f"Summary validation '{validation_index}' updated in "
            f"profile '{profile_name}'"
        ),
    }


@router.delete(
    "/document-types/{document_type}/profiles/{profile_name}/"
    "summary-validations/{validation_index}",
    summary="Delete a profile summary validation",
    description=(
        "Deletes one profile summary validation by index. Authenticated "
        "requests require the config:write scope."
    ),
    response_description="Summary validation deletion result.",
    response_model=OperationResponse,
)
def delete_summary_validation(
    document_type: str = Path(..., description="Profile-based document-type key."),
    profile_name: str = Path(..., description="Existing profile name."),
    validation_index: int = Path(..., ge=0, description="Existing validation index."),
):
    config = load_config()
    delete_profile_summary_validation(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
        validation_index=validation_index,
    )
    return {
        "status": "ok",
        "message": (
            f"Summary validation '{validation_index}' deleted from "
            f"profile '{profile_name}'"
        ),
    }
