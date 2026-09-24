from security_dependencies import api_key_header, bearer_scheme


def test_api_key_header_contract():
    assert api_key_header.model.name == "X-API-Key"
    assert api_key_header.scheme_name == "ApiKeyAuth"
    assert api_key_header.auto_error is False


def test_bearer_header_contract():
    assert bearer_scheme.scheme_name == "BearerAuth"
    assert bearer_scheme.model.scheme == "bearer"
    assert bearer_scheme.auto_error is False
