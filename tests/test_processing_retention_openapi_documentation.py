from api import app


def test_retention_operations_are_documented():
    schema = app.openapi()
    preview = schema["paths"][
        "/api/v1/processing-runs/retention-preview"
    ]["get"]
    execute = schema["paths"][
        "/api/v1/processing-runs/retention-execute"
    ]["post"]

    assert preview["summary"] == "Preview processing run retention"
    assert "internal admin scope" in preview["description"]
    assert "tenant-owned" in preview["description"]
    assert execute["summary"] == "Execute processing run retention"
    assert "internal admin scope" in execute["description"]
    assert "exact DELETE confirmation" in execute["description"]
    assert "Atomically" in execute["description"]


def test_retention_models_are_documented():
    schemas = app.openapi()["components"]["schemas"]
    for name in (
        "ProcessingRunRetentionPreviewModel",
        "ProcessingRunRetentionExecuteRequestModel",
        "ProcessingRunRetentionExecuteModel",
    ):
        for field_name, field in schemas[name]["properties"].items():
            assert field.get("description"), f"{name}.{field_name}"


def test_retention_request_contract_is_bounded_and_explicit():
    schema = app.openapi()["components"]["schemas"][
        "ProcessingRunRetentionExecuteRequestModel"
    ]["properties"]

    assert schema["confirmation"]["const"] == "DELETE"
    assert schema["confirmation"]["examples"] == ["DELETE"]
    assert schema["limit"]["minimum"] == 1
    assert schema["limit"]["maximum"] == 1000
    assert schema["limit"]["default"] == 100
