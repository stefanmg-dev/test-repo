from typing import Any

from document_config_resolver import (
    resolve_document_fields,
)
from profile_selection import (
    select_document_profile,
)
from supplier_matcher import (
    match_supplier,
    match_supplier_from_config,
)


class SupplierProfilePipelineError(
    ValueError
):
    pass


def has_configured_supplier_matching(
    document_config: dict,
) -> bool:
    profiles = document_config.get("profiles", {})
    if not isinstance(profiles, dict):
        return False

    return any(
        isinstance(profile, dict)
        and profile.get("matching") is not None
        for profile in profiles.values()
    )


def resolve_supplier_profile_fields(
    document_config: Any,
    ocr_text: str,
) -> dict:
    if not isinstance(document_config, dict):
        raise SupplierProfilePipelineError(
            "Document configuration must "
            "be an object"
        )

    if has_configured_supplier_matching(document_config):
        supplier_match = match_supplier_from_config(
            document_config,
            ocr_text,
        )
    else:
        supplier_match = match_supplier(
            ocr_text
        )

    selection = select_document_profile(
        document_config=document_config,
        matched_profile_name=(
            supplier_match.profile_name
        ),
    )

    fields = resolve_document_fields(
        document_config=document_config,
        profile_name=selection["profile"],
        use_default_profile=selection[
            "use_default_profile"
        ],
    )

    return {
        "profile": selection["profile"],
        "fields": fields,
        "requires_review": selection[
            "requires_review"
        ],
        "warnings": selection["warnings"],
        "supplier_evidence": list(
            supplier_match.evidence
        ),
    }