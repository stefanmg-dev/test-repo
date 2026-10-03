from pathlib import Path

from fastapi.testclient import TestClient

import routes_config_collections_v1
from api import app


ROOT = Path(__file__).resolve().parent.parent
ROUTES = ROOT / "routes_config_collections_v1.py"
MODELS = ROOT / "config_models.py"
SERVICE = ROOT / "config_collection_service.py"


def test_summary_validation_api_contract_is_registered():
    paths = app.openapi()["paths"]
    base = (
        "/api/v1/config/document-types/{document_type}/profiles/"
        "{profile_name}/summary-validations"
    )
    assert "post" in paths[base]
    assert "put" in paths[f"{base}/{{validation_index}}"]
    assert "delete" in paths[f"{base}/{{validation_index}}"]


def test_summary_validation_request_models_use_typed_validation():
    content = MODELS.read_text(encoding="utf-8")
    assert "class AddSummaryValidationRequest" in content
    assert "class UpdateSummaryValidationRequest" in content
    assert "validation: CollectionSummaryValidationModel" in content


def test_summary_validation_service_uses_copy_and_validated_save():
    content = SERVICE.read_text(encoding="utf-8")
    for name in (
        "add_profile_summary_validation",
        "update_profile_summary_validation",
        "delete_profile_summary_validation",
    ):
        assert f"def {name}(" in content
    assert "updated_config = deepcopy(config)" in content
    assert "save_validated_config(updated_config)" in content


def test_summary_validation_routes_require_existing_config_scope():
    content = ROUTES.read_text(encoding="utf-8")
    assert 'prefix="/api/v1/config"' in content
    assert "dependencies=[Depends(enforce_config_scope)]" in content
    assert "summary-validations/{validation_index}" in content
