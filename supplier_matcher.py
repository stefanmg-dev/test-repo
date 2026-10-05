import re
import unicodedata
from dataclasses import dataclass


TELECOM_A1_PROFILE = "telecom_a1"
ELECTRICITY_ELECTROHOLD_PROFILE = (
    "electricity_electrohold"
)
HEATING_TOPLOFIKACIA_SOFIA_PROFILE = (
    "heating_toplofikacia_sofia"
)


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

    matches = []

    a1_evidence = _find_a1_evidence(
        normalized_text
    )

    if a1_evidence:
        matches.append(
            (
                TELECOM_A1_PROFILE,
                a1_evidence,
            )
        )

    electrohold_evidence = (
        _find_electrohold_evidence(
            normalized_text
        )
    )

    if electrohold_evidence:
        matches.append(
            (
                ELECTRICITY_ELECTROHOLD_PROFILE,
                electrohold_evidence,
            )
        )
    toplo_evidence = _find_toplofikacia_sofia_evidence(
        normalized_text
    )
    if toplo_evidence:
        matches.append(
            (
                HEATING_TOPLOFIKACIA_SOFIA_PROFILE,
                toplo_evidence,
            )
        )

    if len(matches) != 1:
        evidence = tuple(
            evidence_code
            for _, profile_evidence in matches
            for evidence_code in profile_evidence
        )

        return SupplierMatchResult(
            profile_name=None,
            evidence=evidence,
        )

    profile_name, evidence = matches[0]

    return SupplierMatchResult(
        profile_name=profile_name,
        evidence=tuple(evidence),
    )


def match_supplier_from_config(
    document_config: dict,
    text: str,
) -> SupplierMatchResult:
    if not isinstance(document_config, dict):
        raise SupplierMatcherError(
            "Document configuration must be an object"
        )

    profiles = document_config.get("profiles", {})
    if not isinstance(profiles, dict):
        raise SupplierMatcherError(
            "'profiles' must be an object"
        )

    normalized_text = normalize_supplier_text(text)
    if not normalized_text:
        return SupplierMatchResult(
            profile_name=None,
            evidence=(),
        )

    matches = []
    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            raise SupplierMatcherError(
                f"Profile '{profile_name}' must be an object"
            )

        matching = profile.get("matching")
        if matching is None:
            continue
        if not isinstance(matching, dict):
            raise SupplierMatcherError(
                f"Profile '{profile_name}' matching must be an object"
            )

        rules = matching.get("any_of", [])
        if not isinstance(rules, list):
            raise SupplierMatcherError(
                f"Profile '{profile_name}' matching.any_of must be a list"
            )

        profile_evidence = []
        for rule in rules:
            if not isinstance(rule, dict):
                raise SupplierMatcherError(
                    f"Profile '{profile_name}' matching rule must be an object"
                )
            code = rule.get("code")
            pattern = rule.get("pattern")
            if not isinstance(code, str) or not code.strip():
                raise SupplierMatcherError(
                    f"Profile '{profile_name}' matching rule code is invalid"
                )
            if not isinstance(pattern, str) or not pattern:
                raise SupplierMatcherError(
                    f"Profile '{profile_name}' matching rule pattern is invalid"
                )
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
            except re.error as exc:
                raise SupplierMatcherError(
                    f"Profile '{profile_name}' matching pattern is invalid: {exc}"
                ) from exc
            if compiled.search(normalized_text):
                profile_evidence.append(code.strip())

        if profile_evidence:
            matches.append((profile_name, tuple(profile_evidence)))

    if len(matches) != 1:
        return SupplierMatchResult(
            profile_name=None,
            evidence=tuple(
                code
                for _, profile_evidence in matches
                for code in profile_evidence
            ),
        )

    profile_name, evidence = matches[0]
    return SupplierMatchResult(
        profile_name=profile_name,
        evidence=evidence,
    )


def get_matched_profile_name(
    text: str,
) -> str | None:
    return match_supplier(
        text
    ).profile_name


def _find_a1_evidence(
    normalized_text: str,
):
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


def _find_electrohold_evidence(
    normalized_text: str,
):
    evidence = []

    strong_patterns = (
        (
            "electrohold_sales_company",
            re.compile(
                r"\bелектрохолд\s+"
                r"продажби\s+еад\b",
                re.IGNORECASE,
            ),
        ),
        (
            "electrohold_official_domain",
            re.compile(
                r"(?<![\w.-])"
                r"(?:https?://)?"
                r"(?:www\.)?"
                r"electrohold\.bg"
                r"(?:/[^\s]*)?"
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


def _find_toplofikacia_sofia_evidence(
    normalized_text: str,
):
    evidence = []
    strong_patterns = (
        (
            "toplofikacia_sofia_company",
            re.compile(
                r"\bтоплофикация\s+"
                r"софия(?:\s*[\"„“']*)?"
                r"\s+еад\b",
                re.IGNORECASE,
            ),
        ),
        (
            "toplofikacia_sofia_domain",
            re.compile(
                r"(?<![\w.-])"
                r"(?:https?://)?"
                r"(?:www\.)?"
                r"toplo\.bg"
                r"(?:/[^\s]*)?"
                r"(?![\w.-])",
                re.IGNORECASE,
            ),
        ),
    )
    for evidence_code, pattern in strong_patterns:
        if pattern.search(normalized_text):
            evidence.append(evidence_code)
    return evidence
