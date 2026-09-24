from fastapi.testclient import TestClient

import routes_extract
from api import app


client = TestClient(app)


def test_extract_document_returns_413_for_oversized_upload(
    monkeypatch,
):
    async def reject_upload(file):
        raise routes_extract.PayloadTooLargeError(
            "Uploaded file exceeds the configured size limit"
        )

    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        reject_upload,
    )

    response = client.post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "invoice.pdf",
                b"%PDF-test",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "Uploaded file exceeds the configured size limit"
    }
