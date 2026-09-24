from security_dependencies import api_key_header


def test_api_key_header_contract():
    assert api_key_header.model.name == "X-API-Key"
    assert api_key_header.scheme_name == "ApiKeyAuth"
    assert api_key_header.auto_error is False
