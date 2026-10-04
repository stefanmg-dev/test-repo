from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ORCHESTRATOR = ROOT / "extraction_orchestrator.py"
MODELS = ROOT / "extraction_models.py"
ROUTES = ROOT / "routes_extract.py"


def test_engine_returns_separate_summary_validation():
    content = ORCHESTRATOR.read_text(encoding="utf-8")

    assert '"summary_validation": summary_validation' in content
    assert '"collection_validation": (' in content


def test_api_response_model_exposes_summary_validation():
    content = MODELS.read_text(encoding="utf-8")

    assert "summary_validation: ExtractionValidationModel" in content
    assert "Collection validation remains combined" in content


def test_route_returns_and_persists_summary_validation():
    content = ROUTES.read_text(encoding="utf-8")

    assert 'summary_validation = engine_result.get(' in content
    assert '"summary_validation": summary_validation' in content
    assert '"summary": summary_validation' in content


def test_processing_status_keeps_combined_collection_validation():
    content = ROUTES.read_text(encoding="utf-8")

    status_start = content.index(
        "processing_status = determine_processing_status("
    )
    status_end = content.index(
        "finally:",
        status_start,
    )
    status_call = content[status_start:status_end]

    assert "collection_validation=collection_validation" in status_call
    assert "summary_validation=" not in status_call
