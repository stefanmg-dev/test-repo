import re
import unicodedata
from dataclasses import dataclass
from typing import Any


TELECOM_A1_PROFILE = "telecom_a1"


@dataclass(frozen=True)
class SupplierMatchResult:
    profile_name: str | None
    evidence: tuple[str, ...]


class SupplierMatcherError(ValueError):
    pass


def normalize_supplier_text(
    text: str,
) -> str:
    if not isinstance(text, str):
        raise SupplierMatcherError(
            "Supplier text must be a string"
        )

    normalized = unicodedata.normalize(
        "NFKC",
        text,
    )

    normalized = normalized.casefold()

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


def match_supplier(
    text: str,
) -> SupplierMatchResult:
    normalized_text = normalize_supplier_text(
        text
    )

    if not normalized_text:
        return SupplierMatchResult(
            profile_name=None,
            evidence=(),
        )

    evidence = _find_a1_evidence(
        normalized_text
    )

    if not evidence:
        return SupplierMatchResult(
            profile_name=None,
            evidence=(),
        )

    return SupplierMatchResult(
        profile_name=TELECOM_A1_PROFILE,
        evidence=tuple(evidence),
    )


def get_matched_profile_name(
    text: str,
) -> str | None:
    return match_supplier(
        text
    ).profile_name


def _find_a1_evidence(
    normalized_text: str,
) -> list[str]:
    evidence = []

    strong_patterns = (
        (
            "a1_bulgaria_company",
            re.compile(
                r"\b[aа]\s*1\s+"
                r"(?:bulgaria|българия)"
                r"(?:\s*[\"„“']*)?"
                r"\s+(?:ead|еад)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "a1_bulgaria",
            re.compile(
                r"\b[aа]\s*1\s+"
                r"(?:bulgaria|българия)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "a1_bulgaria_company_reversed",
            re.compile(
                r"\b(?:bulgaria|българия)"
                r"\s+(?:ead|еад)"
                r"\s+\b[aа]\s*1\b",
                re.IGNORECASE,
            ),
        ),
        (
            "a1_official_domain",
            re.compile(
                r"(?<![\w.-])"
                r"(?:https?://)?"
                r"(?:www\.)?"
                r"a1\.bg"
                r"(?![\w.-])",
                re.IGNORECASE,
            ),
        ),
    )

    for evidence_code, pattern in strong_patterns:
        if pattern.search(normalized_text):
            evidence.append(
                evidence_code
            )

    return evidence