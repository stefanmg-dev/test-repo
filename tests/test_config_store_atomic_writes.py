import json
import os
from pathlib import Path

import pytest

import config_store
from config_validator import ConfigValidationError


VALID_CONFIG = {
    "invoice": {
        "fields": [],
    }
}


def configure_path(monkeypatch, tmp_path):
    config_path = tmp_path / "document_types.json"
    monkeypatch.setattr(config_store, "CONFIG_PATH", config_path)
    return config_path


def temporary_files(tmp_path):
    return list(tmp_path.glob(".document_types.json.*.tmp"))


def test_save_config_round_trips_valid_configuration(monkeypatch, tmp_path):
    config_path = configure_path(monkeypatch, tmp_path)

    config_store.save_config(VALID_CONFIG)

    assert json.loads(config_path.read_text(encoding="utf-8")) == VALID_CONFIG
    assert config_store.load_config() == VALID_CONFIG
    assert temporary_files(tmp_path) == []


def test_validation_happens_before_temporary_file_creation(
    monkeypatch,
    tmp_path,
):
    configure_path(monkeypatch, tmp_path)

    monkeypatch.setattr(
        config_store.tempfile,
        "mkstemp",
        lambda **kwargs: pytest.fail("temporary file must not be created"),
    )

    with pytest.raises(ConfigValidationError):
        config_store.save_config({})

    assert temporary_files(tmp_path) == []


def test_failed_json_write_preserves_original_and_cleans_temporary_file(
    monkeypatch,
    tmp_path,
):
    config_path = configure_path(monkeypatch, tmp_path)
    original = '{"original": true}\n'
    config_path.write_text(original, encoding="utf-8")

    def fail_dump(*args, **kwargs):
        raise OSError("simulated write failure")

    monkeypatch.setattr(config_store.json, "dump", fail_dump)

    with pytest.raises(OSError, match="simulated write failure"):
        config_store.save_config(VALID_CONFIG)

    assert config_path.read_text(encoding="utf-8") == original
    assert temporary_files(tmp_path) == []


def test_failed_replace_preserves_original_and_cleans_temporary_file(
    monkeypatch,
    tmp_path,
):
    config_path = configure_path(monkeypatch, tmp_path)
    original = '{"original": true}\n'
    config_path.write_text(original, encoding="utf-8")

    def fail_replace(source, destination):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(config_store.os, "replace", fail_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        config_store.save_config(VALID_CONFIG)

    assert config_path.read_text(encoding="utf-8") == original
    assert temporary_files(tmp_path) == []


def test_save_fsyncs_before_replace(monkeypatch, tmp_path):
    config_path = configure_path(monkeypatch, tmp_path)
    calls = []
    real_fsync = os.fsync
    real_replace = os.replace

    def capture_fsync(descriptor):
        calls.append("fsync")
        real_fsync(descriptor)

    def capture_replace(source, destination):
        calls.append("replace")
        real_replace(source, destination)

    monkeypatch.setattr(config_store.os, "fsync", capture_fsync)
    monkeypatch.setattr(config_store.os, "replace", capture_replace)

    config_store.save_config(VALID_CONFIG)

    assert calls == ["fsync", "replace"]
    assert config_path.is_file()


def test_sequential_writes_use_distinct_temporary_paths(monkeypatch, tmp_path):
    configure_path(monkeypatch, tmp_path)
    sources = []
    real_replace = os.replace

    def capture_replace(source, destination):
        sources.append(Path(source))
        real_replace(source, destination)

    monkeypatch.setattr(config_store.os, "replace", capture_replace)

    config_store.save_config(VALID_CONFIG)
    config_store.save_config(VALID_CONFIG)

    assert len(sources) == 2
    assert sources[0] != sources[1]
    assert all(source.parent == tmp_path for source in sources)
    assert temporary_files(tmp_path) == []
