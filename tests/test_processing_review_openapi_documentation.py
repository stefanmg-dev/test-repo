from api import app


def test_processing_review_operations_are_documented():
    schema = app.openapi()
    path = schema["paths"]["/api/v1/processing-runs/{run_id}/review"]

    assert path["get"]["summary"] == "Get processing run review"
    assert "processing-runs:review" in path["get"]["description"]
    assert path["put"]["summary"] == (
        "Record a processing run review decision"
    )
    assert "processing-runs:review" in path["put"]["description"]
    assert path["put"]["responses"]["409"]["description"]


def test_processing_review_path_parameters_are_documented():
    path = app.openapi()["paths"][
        "/api/v1/processing-runs/{run_id}/review"
    ]
    for method in ("get", "put"):
        parameter = path[method]["parameters"][0]
        assert parameter["name"] == "run_id"
        assert parameter["description"]


def test_processing_review_models_are_documented():
    schemas = app.openapi()["components"]["schemas"]
    for name in (
        "ProcessingRunReviewRequestModel",
        "ProcessingRunReviewModel",
    ):
        for field_name, field in schemas[name]["properties"].items():
            assert field.get("description"), f"{name}.{field_name}"


def test_processing_review_examples_are_synthetic():
    schemas = app.openapi()["components"]["schemas"]
    request = schemas["ProcessingRunReviewRequestModel"]["properties"]
    assert request["corrected_values"]["examples"] == [
        {"invoice_number": "INV-SYNTH-002"}
    ]
