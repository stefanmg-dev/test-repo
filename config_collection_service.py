from fastapi import HTTPException, status

from config_api_helpers import (
    ensure_profile_based_config,
    get_document_type_or_404,
    get_profile_or_404,
)


def resolve_document_collection_target(
    config: dict,
    document_type: str,
) -> tuple[dict, dict]:
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    collections = document_config.get("collections", {})
    return document_config, collections


def resolve_profile_collection_target(
    config: dict,
    document_type: str,
    profile_name: str,
) -> tuple[dict, dict, dict]:
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
    return document_config, profile_config, collections


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


def get_profile_collection_or_404(
    profile_config: dict,
    collection_name: str,
) -> dict:
    collections = profile_config.get("collections", {})
    collection_config = collections.get(collection_name)
    if collection_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Collection '{collection_name}' was not found "
                "in profile"
            ),
        )
    return collection_config
