from api import app


def test_api_keys_and_auth_operations_are_documented():
    schema = app.openapi()
    paths = {
        ("post", "/api/v1/api-keys"),
        ("get", "/api/v1/api-keys"),
        ("post", "/api/v1/api-keys/{api_key_id}/rotate"),
        ("delete", "/api/v1/api-keys/{api_key_id}"),
        ("get", "/api/v1/auth/config"),
    }

    for method, path in paths:
        operation = schema["paths"][path][method]
        assert operation["description"], f"{method} {path}"
        for response in operation["responses"].values():
            assert response["description"]

    for path in (
        "/api/v1/api-keys/{api_key_id}/rotate",
        "/api/v1/api-keys/{api_key_id}",
    ):
        parameters = schema["paths"][path][
            "post" if path.endswith("rotate") else "delete"
        ]["parameters"]
        api_key_id = next(item for item in parameters if item["name"] == "api_key_id")
        assert api_key_id["description"]


def test_api_key_and_auth_fields_have_descriptions_and_examples():
    schemas = app.openapi()["components"]["schemas"]
    names = (
        "ApiKeyCreateRequest",
        "ApiKeyRotateRequest",
        "ApiKeyModel",
        "ApiKeyCreatedModel",
        "ApiKeyListResponseModel",
        "BrowserAuthConfigModel",
    )
    for name in names:
        for field_name, field in schemas[name].get("properties", {}).items():
            assert field.get("description"), f"{name}.{field_name}"
            if name != "ApiKeyListResponseModel":
                assert field.get("examples"), f"{name}.{field_name}"
