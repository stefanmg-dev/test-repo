from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import configuration_revision as revision


CONFIG_A = {
    "invoice": {
        "fields": [],
    }
}

CONFIG_B = {
    "invoice": {
        "fields": [
            {
                "name": "invoice_number",
                "type": "constant",
                "value": "synthetic",
            }
        ],
    }
}


def request(method):
    return SimpleNamespace(method=method)


def test_revision_is_deterministic_sha256():
    first = revision.configuration_revision(
        CONFIG_A
    )
    second = revision.configuration_revision(
        CONFIG_A
    )

    assert first == second
    assert len(first) == 64
    assert all(
        character in "0123456789abcdef"
        for character in first
    )


def test_revision_changes_with_configuration():
    assert revision.configuration_revision(
        CONFIG_A
    ) != revision.configuration_revision(
        CONFIG_B
    )


def test_etag_is_strong_and_quoted():
    digest = revision.configuration_revision(
        CONFIG_A
    )

    assert revision.configuration_etag(
        digest
    ) == f'"{digest}"'


def test_if_match_supports_current_tag_lists_and_wildcard():
    digest = revision.configuration_revision(
        CONFIG_A
    )
    etag = revision.configuration_etag(
        digest
    )

    assert revision.revision_matches_if_match(
        etag,
        digest,
    )
    assert revision.revision_matches_if_match(
        f'"other", {etag}',
        digest,
    )
    assert revision.revision_matches_if_match(
        "*",
        digest,
    )


def test_weak_or_stale_if_match_does_not_match():
    digest = revision.configuration_revision(
        CONFIG_A
    )

    assert not revision.revision_matches_if_match(
        f'W/"{digest}"',
        digest,
    )
    assert not revision.revision_matches_if_match(
        '"stale"',
        digest,
    )


@pytest.mark.parametrize(
    "method",
    ["GET", "HEAD", "OPTIONS"],
)
def test_safe_methods_do_not_load_configuration(
    monkeypatch,
    method,
):
    monkeypatch.setattr(
        revision,
        "load_config",
        lambda: pytest.fail(
            "safe method must not load configuration"
        ),
    )

    revision.enforce_configuration_revision(
        request(method),
        '"unused"',
    )


@pytest.mark.parametrize(
    "method",
    ["POST", "PUT", "DELETE"],
)
def test_missing_if_match_remains_temporarily_compatible(
    monkeypatch,
    method,
):
    monkeypatch.setattr(
        revision,
        "load_config",
        lambda: pytest.fail(
            "missing optional header must not load"
        ),
    )

    revision.enforce_configuration_revision(
        request(method),
        None,
    )


def test_current_if_match_allows_mutation(
    monkeypatch,
):
    monkeypatch.setattr(
        revision,
        "load_config",
        lambda: CONFIG_A,
    )

    digest = revision.configuration_revision(
        CONFIG_A
    )

    revision.enforce_configuration_revision(
        request("PUT"),
        revision.configuration_etag(digest),
    )


def test_stale_if_match_returns_412_and_current_etag(
    monkeypatch,
):
    monkeypatch.setattr(
        revision,
        "load_config",
        lambda: CONFIG_A,
    )

    digest = revision.configuration_revision(
        CONFIG_A
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        revision.enforce_configuration_revision(
            request("DELETE"),
            '"stale"',
        )

    error = exc_info.value
    assert error.status_code == 412
    assert error.detail == (
        "Configuration revision is stale. "
        "Reload the configuration and retry."
    )
    assert error.headers == {
        "ETag": revision.configuration_etag(
            digest
        )
    }
