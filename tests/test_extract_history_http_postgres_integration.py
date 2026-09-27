import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select


if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )

import routes_extract
from api import app
from configuration_identity import configuration_sha256
from database import SessionLocal
from database_models import ProcessingRun
from processing_run_dependencies import (
    get_processing_run_service,
)
from processing_run_service import ProcessingRunService


TEST_CONFIG = {
    "invoice": {
        "fields": [
            {
                "name": "invoice_number",
                "type": "constant",
                "value": "HTTP-PG-TEST-123",
                "validation": [],
            }
        ]
    }
}


async def fake_extract_document_input(file):
    await file.read()
    return {
        "text": "Deterministic integration document",
        "quality": {
            "status": "accepted",
            "requires_review": False,
            "input": {
                "format": "PDF",
                "source": "native_pdf",
                "page_count": 1,
            },
            "warnings": [],
        },
    }


def test_extract_document_persists_and_history_returns_run(
    monkeypatch,
):
    session = SessionLocal()
    created_run_id = None
    filename = f"http_postgres_{uuid4()}.pdf"
    request_id = str(uuid4())
    previous_override = app.dependency_overrides.get(
        get_processing_run_service
    )

    def override_processing_run_service():
        return ProcessingRunService(session)

    app.dependency_overrides[
        get_processing_run_service
    ] = override_processing_run_service

    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: TEST_CONFIG,
    )
    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fake_extract_document_input,
    )
    monkeypatch.setattr(
        routes_extract,
        "extract_values",
        lambda text: {},
    )
    monkeypatch.setattr(
        routes_extract,
        "extract_document_data",
        lambda **kwargs: {
            "fields": {
                "invoice_number": "HTTP-PG-TEST-123",
            },
            "collections": {},
            "collection_validation": {
                "valid": True,
                "errors": {},
            },
        },
    )
    monkeypatch.setattr(
        routes_extract,
        "validate_result",
        lambda **kwargs: {
            "valid": True,
            "errors": {},
        },
    )

    try:
        client = TestClient(app)
        extract_response = client.post(
            "/extract-document",
            data={"document_type": "invoice"},
            files={
                "file": (
                    filename,
                    b"deterministic-pdf-content",
                    "application/pdf",
                )
            },
            headers={"X-Request-ID": request_id},
        )

        assert extract_response.status_code == 200
        assert extract_response.headers["X-Request-ID"] == (
            request_id
        )
        extract_body = extract_response.json()
        assert extract_body["processing_status"] == "accepted"
        assert extract_body["final_values"] == {
            "invoice_number": "HTTP-PG-TEST-123",
        }

        session.expire_all()
        persisted = session.scalar(
            select(ProcessingRun).where(
                ProcessingRun.filename == filename
            )
        )
        assert persisted is not None
        created_run_id = persisted.id
        assert persisted.processing_status == "accepted"
        assert persisted.requires_review is False
        assert persisted.final_values == {
            "invoice_number": "HTTP-PG-TEST-123",
        }
        assert persisted.collections == {}
        assert persisted.quality["status"] == "accepted"
        assert persisted.error is None
        assert len(persisted.configuration_hash) == 64
        assert persisted.configuration_schema_version == "1"
        assert persisted.invoice_schema_version == "1"
        assert persisted.invoice_shadow_validation_status == (
            "succeeded"
        )
        assert persisted.configuration_snapshot == {
            "schema_version": "1",
            "document_type": "invoice",
            "selected_profile": None,
            "resolved_fields": TEST_CONFIG["invoice"]["fields"],
            "resolved_collections": {},
            "resolved_summary_validations": [],
        }
        assert persisted.configuration_hash == (
            configuration_sha256(
                persisted.configuration_snapshot
            )
        )
        assert set(persisted.step_timings) == {
            "document_input_ms",
            "profile_resolution_ms",
            "llm_extraction_ms",
            "document_engine_ms",
            "validation_ms",
        }

        history_response = client.get(
            f"/api/v1/processing-runs/{created_run_id}",
            headers={"X-Request-ID": request_id},
        )

        assert history_response.status_code == 200
        assert history_response.headers["X-Request-ID"] == (
            request_id
        )
        history_body = history_response.json()
        assert history_body["id"] == str(created_run_id)
        assert history_body["filename"] == filename
        assert history_body["document_type"] == "invoice"
        assert history_body["input_format"] == "pdf"
        assert history_body["processing_status"] == "accepted"
        assert history_body["requires_review"] is False
        assert history_body["final_values"] == {
            "invoice_number": "HTTP-PG-TEST-123",
        }
        assert history_body["collections"] == {}
        assert history_body["validation"] == {
            "fields": {
                "valid": True,
                "errors": {},
            },
            "collections": {
                "valid": True,
                "errors": {},
            },
        }
        assert history_body["quality"]["status"] == (
            "accepted"
        )
        assert set(history_body["step_timings"]) == {
            "document_input_ms",
            "profile_resolution_ms",
            "llm_extraction_ms",
            "document_engine_ms",
            "validation_ms",
        }
        assert history_body["duration_ms"] >= 0
        assert history_body["completed_at"] is not None
        assert history_body["error"] is None
        assert history_body["configuration_hash"] == (
            persisted.configuration_hash
        )
        assert history_body[
            "configuration_schema_version"
        ] == "1"
        assert history_body["invoice_schema_version"] == "1"
        assert history_body[
            "invoice_shadow_validation_status"
        ] == "succeeded"
        assert history_body["configuration_snapshot"] == (
            persisted.configuration_snapshot
        )
    finally:
        session.rollback()
        if created_run_id is not None:
            persisted = session.get(
                ProcessingRun,
                created_run_id,
            )
            if persisted is not None:
                session.delete(persisted)
                session.commit()
        session.close()

        if previous_override is None:
            app.dependency_overrides.pop(
                get_processing_run_service,
                None,
            )
        else:
            app.dependency_overrides[
                get_processing_run_service
            ] = previous_override
