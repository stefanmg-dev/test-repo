from copy import deepcopy

from fastapi import APIRouter, HTTPException, Response, status

from config_models import (
    AddFieldRequest,
    ConfigResponse,
    CreateDocumentTypeRequest,
    DocumentTypeModel,
    OperationResponse,
    RenameDocumentTypeRequest,
    UpdateFieldRequest,
)
from config_store import load_config, save_config
from config_validator import ConfigValidationError


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


@router.get(
    "/document-types",
    response_model=ConfigResponse,
)
def get_document_types():
    config = load_config()

    return {
        "document_types": config
    }


@router.get(
    "/document-types/{document_type}",
    response_model=DocumentTypeModel,
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

    fields = document_config.get("fields", [])

    field_data = request.field.model_dump(
        exclude_none=True
    )

    field_name = field_data["name"]

    if find_field_index(fields, field_name) is not None:
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

    fields = document_config.get("fields", [])

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

    fields = document_config.get("fields", [])

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

    if len(fields) == 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The last field of a document type "
                "cannot be deleted"
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