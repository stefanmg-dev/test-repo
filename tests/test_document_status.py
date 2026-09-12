from document_status import (
    DOCUMENT_STATUS_DRAFT,
    DOCUMENT_STATUS_READY,
    build_document_type_metadata,
    get_document_type_status,
    is_document_type_ready,
)


def test_empty_document_type_is_draft():
    document_config = {
        "fields": []
    }

    assert get_document_type_status(
        document_config
    ) == DOCUMENT_STATUS_DRAFT

    assert is_document_type_ready(
        document_config
    ) is False


def test_document_type_with_fields_is_ready():
    document_config = {
        "fields": [
            {
                "name": "invoice_number",
                "type": "regex",
                "rule": "([0-9]+)",
            }
        ]
    }

    assert get_document_type_status(
        document_config
    ) == DOCUMENT_STATUS_READY

    assert is_document_type_ready(
        document_config
    ) is True


def test_missing_fields_is_draft():
    assert get_document_type_status(
        {}
    ) == DOCUMENT_STATUS_DRAFT


def test_invalid_document_config_is_draft():
    assert get_document_type_status(
        None
    ) == DOCUMENT_STATUS_DRAFT

    assert get_document_type_status(
        []
    ) == DOCUMENT_STATUS_DRAFT


def test_metadata_for_empty_document_type():
    metadata = build_document_type_metadata(
        {
            "fields": []
        }
    )

    assert metadata == {
        "status": "draft",
        "ready": False,
        "field_count": 0,
    }


def test_metadata_for_ready_document_type():
    metadata = build_document_type_metadata(
        {
            "fields": [
                {
                    "name": "invoice_number",
                    "type": "regex",
                    "rule": "([0-9]+)",
                },
                {
                    "name": "total_amount",
                    "type": "regex",
                    "rule": "([0-9]+\\.[0-9]+)",
                },
            ]
        }
    )

    assert metadata == {
        "status": "ready",
        "ready": True,
        "field_count": 2,
    }