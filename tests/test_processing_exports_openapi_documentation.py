from api import app


def test_csv_export_operation_is_documented():
    operation = app.openapi()["paths"][
        "/api/v1/processing-runs/export"
    ]["get"]

    assert operation["summary"] == "Export processing runs as CSV"
    assert "tenant-scoped" in operation["description"]
    assert "processing-runs:read" in operation["description"]
    assert "excludes raw OCR text" in operation["description"]
    assert "text/csv" in operation["responses"]["200"]["content"]


def test_feedback_export_operation_and_cursor_are_documented():
    operation = app.openapi()["paths"][
        "/api/v1/processing-runs/universal-invoice-feedback-export"
    ]["get"]

    assert operation["summary"] == (
        "Export reviewed Universal Invoice feedback as JSONL"
    )
    assert "deterministic" in operation["description"]
    assert "processing-runs:read" in operation["description"]
    assert "excludes filenames and raw OCR text" in operation["description"]
    assert "409" in operation["responses"]

    parameters = {item["name"]: item for item in operation["parameters"]}
    assert parameters["limit"]["description"]
    assert parameters["limit"]["schema"]["minimum"] == 1
    assert parameters["limit"]["schema"]["maximum"] == 1000
    assert parameters["after_reviewed_at"]["description"]
    assert parameters["after_processing_run_id"]["description"]


def test_feedback_export_next_cursor_headers_are_documented():
    headers = app.openapi()["paths"][
        "/api/v1/processing-runs/universal-invoice-feedback-export"
    ]["get"]["responses"]["200"]["headers"]

    assert headers["X-Next-Reviewed-At"]["description"]
    assert headers["X-Next-Processing-Run-Id"]["description"]
