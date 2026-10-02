from pathlib import Path

from api import app


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)
RUNTIME_PREFIXES = (
    "/api/v1/processing-runs",
    "/extract-document",
)
METHODS = {"get", "post", "put", "patch", "delete"}


def runtime_operations():
    schema = app.openapi()
    for path, path_item in schema["paths"].items():
        if not path.startswith(RUNTIME_PREFIXES):
            continue
        for method, operation in path_item.items():
            if method in METHODS:
                yield path, method, operation


def test_all_runtime_operations_and_parameters_are_documented():
    operations = list(runtime_operations())
    assert operations

    for path, method, operation in operations:
        name = f"{method.upper()} {path}"
        assert operation.get("summary"), name
        assert operation.get("description"), name

        success_responses = [
            response
            for status_code, response in operation["responses"].items()
            if status_code.startswith("2")
        ]
        assert success_responses, name
        assert all(
            response.get("description")
            for response in success_responses
        ), name

        for parameter in operation.get("parameters", []):
            assert parameter.get("description"), (
                f"{name}: {parameter['name']}"
            )


def test_extraction_contract_documents_input_and_errors():
    operation = app.openapi()["paths"]["/extract-document"]["post"]

    assert operation.get("requestBody")
    assert {"200", "404", "409", "413", "415", "422"}.issubset(
        operation["responses"]
    )
    assert "documents:extract" in operation["description"]


def test_runtime_operations_exist_in_api_reference():
    content = API_REFERENCE.read_text(encoding="utf-8")

    for path, method, _operation in runtime_operations():
        heading = f"### {method.upper()} `{path}`"
        assert heading in content, heading
