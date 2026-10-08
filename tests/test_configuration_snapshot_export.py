import json
from pathlib import Path

import pytest

import scripts.export_configuration_snapshot as export_module
from configuration_snapshot import validate_configuration_snapshot


CONFIG = {
    "invoice": {
        "fields": [],
    }
}


def test_export_writes_valid_snapshot_and_creates_parent(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(export_module, "load_config", lambda: CONFIG)
    output = tmp_path / "nested" / "baseline.config-snapshot.json"

    snapshot = export_module.export_configuration_snapshot(output)

    assert output.is_file()
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written == snapshot
    assert validate_configuration_snapshot(written) == CONFIG
    assert output.read_text(encoding="utf-8").endswith("\n")


def test_export_refuses_to_overwrite_existing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(export_module, "load_config", lambda: CONFIG)
    output = tmp_path / "existing.config-snapshot.json"
    output.write_text("trusted original\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        export_module.export_configuration_snapshot(output)

    assert output.read_text(encoding="utf-8") == "trusted original\n"


def test_export_removes_invalid_written_snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr(export_module, "load_config", lambda: CONFIG)
    output = tmp_path / "invalid.config-snapshot.json"

    def reject_snapshot(snapshot):
        raise ValueError("simulated verification failure")

    monkeypatch.setattr(
        export_module,
        "validate_configuration_snapshot",
        reject_snapshot,
    )

    with pytest.raises(ValueError, match="simulated verification failure"):
        export_module.export_configuration_snapshot(output)

    assert not output.exists()


def test_export_cli_requires_explicit_output_path():
    content = Path(export_module.__file__).read_text(encoding="utf-8")

    assert "parser.add_argument" in content
    assert '"output"' in content
    assert "output_path.open" in content
    assert '"x"' in content
    assert "Existing files are never overwritten" in content


def test_snapshot_artifacts_are_ignored_by_git_and_container():
    root = Path(__file__).resolve().parents[1]

    for filename in (".gitignore", ".dockerignore"):
        content = (root / filename).read_text(encoding="utf-8")
        assert "configuration_snapshots/" in content
        assert "*.config-snapshot.json" in content

def test_export_does_not_delete_file_created_by_competing_writer(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(export_module, "load_config", lambda: CONFIG)
    output = tmp_path / "race.config-snapshot.json"
    original_open = Path.open

    def competing_open(path, mode="r", *args, **kwargs):
        if path == output and mode == "x":
            path.write_text("competing writer\n", encoding="utf-8")
            raise FileExistsError("simulated competing writer")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", competing_open)

    with pytest.raises(FileExistsError, match="competing writer"):
        export_module.export_configuration_snapshot(output)

    assert output.read_text(encoding="utf-8") == "competing writer\n"

