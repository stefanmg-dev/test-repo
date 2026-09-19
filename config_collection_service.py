from copy import deepcopy

from fastapi import HTTPException, status

from config_api_helpers import (
    ensure_profile_based_config,
    find_field_index,
    get_document_type_or_404,
    get_profile_or_404,
    save_validated_config,
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


def add_document_collection(
    config: dict,
    document_type: str,
    collection_name: str,
    collection_data: dict,
) -> None:
    _, collections = resolve_document_collection_target(
        config=config,
        document_type=document_type,
    )
    if collection_name in collections:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Collection '{collection_name}' already exists "
                f"in document type '{document_type}'"
            ),
        )
    updated_config = deepcopy(config)
    updated_config[document_type].setdefault(
        "collections",
        {},
    )[collection_name] = collection_data
    save_validated_config(updated_config)


def update_document_collection(
    config: dict,
    document_type: str,
    collection_name: str,
    collection_data: dict,
) -> None:
    _, collections = resolve_document_collection_target(
        config=config,
        document_type=document_type,
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
    updated_config[document_type]["collections"][
        collection_name
    ] = collection_data
    save_validated_config(updated_config)


def delete_document_collection(
    config: dict,
    document_type: str,
    collection_name: str,
) -> None:
    _, collections = resolve_document_collection_target(
        config=config,
        document_type=document_type,
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


def add_profile_collection_mutation(
    config: dict,
    document_type: str,
    profile_name: str,
    collection_name: str,
    collection_data: dict,
) -> None:
    _, _, collections = resolve_profile_collection_target(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
    )
    if collection_name in collections:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Collection '{collection_name}' already exists "
                f"in profile '{profile_name}'"
            ),
        )
    updated_config = deepcopy(config)
    updated_config[document_type]["profiles"][
        profile_name
    ].setdefault("collections", {})[
        collection_name
    ] = collection_data
    save_validated_config(updated_config)


def update_profile_collection_mutation(
    config: dict,
    document_type: str,
    profile_name: str,
    collection_name: str,
    collection_data: dict,
) -> None:
    _, _, collections = resolve_profile_collection_target(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
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
    updated_config[document_type]["profiles"][profile_name][
        "collections"
    ][collection_name] = collection_data
    save_validated_config(updated_config)


def delete_profile_collection_mutation(
    config: dict,
    document_type: str,
    profile_name: str,
    collection_name: str,
) -> None:
    _, _, collections = resolve_profile_collection_target(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
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


def add_document_collection_field(
    config: dict,
    document_type: str,
    collection_name: str,
    field_data: dict,
) -> None:
    document_config = get_document_type_or_404(
        config=config,
        document_type=document_type,
    )
    collection_config = get_collection_or_404(
        document_config=document_config,
        collection_name=collection_name,
    )
    fields = collection_config.get("fields", [])
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


def update_document_collection_field(
    config: dict,
    document_type: str,
    collection_name: str,
    field_name: str,
    field_data: dict,
) -> None:
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
    new_field_name = field_data["name"]
    if new_field_name != field_name:
        existing_index = find_field_index(
            fields,
            new_field_name,
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


def delete_document_collection_field(
    config: dict,
    document_type: str,
    collection_name: str,
    field_name: str,
) -> None:
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


def add_profile_collection_field(
    config: dict,
    document_type: str,
    profile_name: str,
    collection_name: str,
    field_data: dict,
) -> None:
    _, profile_config, _ = resolve_profile_collection_target(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
    )
    collection_config = get_profile_collection_or_404(
        profile_config=profile_config,
        collection_name=collection_name,
    )
    fields = collection_config.get("fields", [])
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


def update_profile_collection_field(
    config: dict,
    document_type: str,
    profile_name: str,
    collection_name: str,
    field_name: str,
    field_data: dict,
) -> None:
    _, profile_config, _ = resolve_profile_collection_target(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
    )
    collection_config = get_profile_collection_or_404(
        profile_config=profile_config,
        collection_name=collection_name,
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
    new_field_name = field_data["name"]
    if new_field_name != field_name:
        existing_index = find_field_index(
            fields,
            new_field_name,
        )
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


def delete_profile_collection_field(
    config: dict,
    document_type: str,
    profile_name: str,
    collection_name: str,
    field_name: str,
) -> None:
    _, profile_config, _ = resolve_profile_collection_target(
        config=config,
        document_type=document_type,
        profile_name=profile_name,
    )
    collection_config = get_profile_collection_or_404(
        profile_config=profile_config,
        collection_name=collection_name,
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
