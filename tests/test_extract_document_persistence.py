from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

import routes_extract
from api import app
from processing_run_dependencies import (
    get_processing_run_service,
)


TEST_CONFIG = {
    "invoice": {
        "fields": [
            {
                "name": "invoice_number",
                "type": "constant",
                "value": "TEST-123",
                "validation": [],
            }
        ]
    }
}


class RecordingProcessingRunService:
    def __init__(self):
        self.run_id = uuid4()
        self.started = []
        self.completed = []
        self.failed = []

    def start_run(self, **kwargs):
        self.started.append(kwargs)
        return SimpleNamespace(id=self.run_id)

    def complete_run(self, run_id, **kwargs):
        self.completed.append((run_id, kwargs))

    def fail_run(self, run_id, **kwargs):
        self.failed.append((run_id, kwargs))


def install_service(service):
    app.dependency_overrides[
        get_processing_run_service
    ] = lambda: service


def configure_success(monkeypatch):
    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": "Test document text",
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
            "fields": {"invoice_number": "TEST-123"},
            "collections": {},
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


def test_successful_extraction_completes_processing_run(
    monkeypatch,
):
    service = RecordingProcessingRunService()
    install_service(service)
    configure_success(monkeypatch)

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "invoice.pdf",
                b"test-content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert service.started == [
        {
            "document_type": "invoice",
            "filename": "invoice.pdf",
            "input_format": "pdf",
        }
    ]
    assert len(service.completed) == 1
    assert service.completed[0][0] == service.run_id
    completed = service.completed[0][1]
    assert completed["processing_status"] == "accepted"
    assert completed["profile"] is None
    assert completed["requires_review"] is False
    assert completed["duration_ms"] >= 0
    assert set(completed["step_timings"]) == {
        "document_input_ms",
        "profile_resolution_ms",
        "llm_extraction_ms",
        "document_engine_ms",
        "validation_ms",
    }
    assert all(
        value >= 0
        for value in completed["step_timings"].values()
    )
    assert completed["final_values"] == {
        "invoice_number": "TEST-123"
    }
    assert completed["validation"] == {
        "fields": {"valid": True, "errors": {}},
        "collections": {"valid": True, "errors": {}},
    }
    assert service.failed == []


def test_invalid_document_fails_processing_run(monkeypatch):
    service = RecordingProcessingRunService()
    install_service(service)

    async def fail_input(file):
        raise routes_extract.InvalidDocumentInputError(
            "Invalid or corrupted PDF file"
        )

    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: TEST_CONFIG,
    )
    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fail_input,
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "broken.pdf",
                b"broken",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid or corrupted PDF file"
    }
    assert len(service.failed) == 1
    failed = service.failed[0][1]
    assert failed["error"] == {
        "type": "InvalidDocumentInputError",
        "detail": "Invalid or corrupted PDF file",
        "http_status": 422,
    }
    assert failed["duration_ms"] >= 0
    assert set(failed["step_timings"]) == {
        "document_input_ms"
    }
    assert failed["step_timings"]["document_input_ms"] >= 0
    assert service.completed == []


def test_unknown_document_type_does_not_start_run(monkeypatch):
    service = RecordingProcessingRunService()
    install_service(service)
    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: TEST_CONFIG,
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "unknown"},
        files={
            "file": (
                "invoice.pdf",
                b"test-content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 404
    assert service.started == []
    assert service.completed == []
    assert service.failed == []
