from typing import Final

from fastapi import Header, HTTPException, Request, status

from configuration_identity import configuration_sha256
from config_store import load_config


SAFE_METHODS: Final = {
    "GET",
    "HEAD",
    "OPTIONS",
}


def configuration_revision(
    config: dict,
) -> str:
    return configuration_sha256(config)


def configuration_etag(
    revision: str,
) -> str:
    return f'"{revision}"'


def revision_matches_if_match(
    if_match: str,
    current_revision: str,
) -> bool:
    tokens = {
        token.strip()
        for token in if_match.split(",")
        if token.strip()
    }

    if "*" in tokens:
        return True

    expected = configuration_etag(
        current_revision
    )

    return expected in tokens


def enforce_configuration_revision(
    request: Request,
    if_match: str | None = Header(
        default=None,
        alias="If-Match",
        description=(
            "Optional strong configuration ETag. "
            "A stale value rejects the mutation."
        ),
    ),
) -> None:
    if request.method in SAFE_METHODS:
        return

    # Backward-compatible foundation.
    # A later checkpoint will require this header.
    if if_match is None:
        return

    current_revision = configuration_revision(
        load_config()
    )

    if revision_matches_if_match(
        if_match,
        current_revision,
    ):
        return

    raise HTTPException(
        status_code=(
            status.HTTP_412_PRECONDITION_FAILED
        ),
        detail=(
            "Configuration revision is stale. "
            "Reload the configuration and retry."
        ),
        headers={
            "ETag": configuration_etag(
                current_revision
            ),
        },
    )
