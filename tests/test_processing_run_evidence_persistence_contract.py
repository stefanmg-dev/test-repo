from pathlib import Path

from database_models import ProcessingRun
from processing_run_models import ProcessingRunDetailModel


ROOT = Path(__file__).resolve().parent.parent


def test_processing_run_models_expose_extraction_evidence():
    assert hasattr(ProcessingRun, "field_evidence")
    assert hasattr(ProcessingRun, "collection_evidence")
    assert "field_evidence" in ProcessingRunDetailModel.model_fields
    assert "collection_evidence" in ProcessingRunDetailModel.model_fields


def test_extraction_route_persists_engine_evidence():
    content = (ROOT / "routes_extract.py").read_text(encoding="utf-8")
    assert 'field_evidence=engine_result.get(' in content
    assert 'collection_evidence=engine_result.get(' in content


def test_processing_run_service_assigns_extraction_evidence():
    content = (ROOT / "processing_run_service.py").read_text(
        encoding="utf-8"
    )
    assert "processing_run.field_evidence = field_evidence" in content
    assert (
        "processing_run.collection_evidence = collection_evidence"
        in content
    )


def test_evidence_migration_is_reversible():
    content = (
        ROOT
        / "alembic"
        / "versions"
        / "a6c3d4e5f7b8_add_processing_run_extraction_evidence.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "f5b2c3d4e6a7"' in content
    assert '"field_evidence"' in content
    assert '"collection_evidence"' in content
    assert 'op.drop_column("processing_runs", "collection_evidence")' in content
    assert 'op.drop_column("processing_runs", "field_evidence")' in content
