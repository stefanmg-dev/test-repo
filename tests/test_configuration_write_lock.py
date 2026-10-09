from pathlib import Path

import pytest

import config_store
from config_validator import ConfigValidationError


VALID_CONFIG = {
    "invoice": {
        "fields": [],
    }
}


def test_lock_path_is_hidden_and_adjacent(tmp_path):
    config_path = tmp_path / "document_types.json"

    assert config_store.configuration_lock_path(config_path) == (
        tmp_path / ".document_types.json.lock"
    )


def test_write_lock_acquires_and_releases_exclusive_lock(
    monkeypatch,
    tmp_path,
):
    config_path = tmp_path / "document_types.json"
    events = []

    def capture_flock(descriptor, operation):
        events.append(operation)

    monkeypatch.setattr(config_store.fcntl, "flock", capture_flock)

    with config_store.configuration_write_lock(config_path):
        events.append("inside")

    assert events == [
        config_store.fcntl.LOCK_EX,
        "inside",
        config_store.fcntl.LOCK_UN,
    ]
    assert config_store.configuration_lock_path(config_path).is_file()


def test_write_lock_releases_after_exception(monkeypatch, tmp_path):
    config_path = tmp_path / "document_types.json"
    operations = []

    monkeypatch.setattr(
        config_store.fcntl,
        "flock",
        lambda descriptor, operation: operations.append(operation),
    )

    with pytest.raises(RuntimeError, match="simulated failure"):
        with config_store.configuration_write_lock(config_path):
            raise RuntimeError("simulated failure")

    assert operations == [
        config_store.fcntl.LOCK_EX,
        config_store.fcntl.LOCK_UN,
    ]


def test_save_validates_before_acquiring_lock(monkeypatch):
    monkeypatch.setattr(
        config_store,
        "configuration_write_lock",
        lambda: pytest.fail("invalid config must not acquire lock"),
    )

    with pytest.raises(ConfigValidationError):
        config_store.save_config({})


def test_save_holds_lock_around_atomic_write(monkeypatch):
    events = []

    class Lock:
        def __enter__(self):
            events.append("lock_enter")

        def __exit__(self, exc_type, exc, traceback):
            events.append("lock_exit")

    monkeypatch.setattr(
        config_store,
        "configuration_write_lock",
        lambda: Lock(),
    )
    monkeypatch.setattr(
        config_store,
        "_save_config_unlocked",
        lambda config: events.append(("write", config)),
    )

    config_store.save_config(VALID_CONFIG)

    assert events == [
        "lock_enter",
        ("write", VALID_CONFIG),
        "lock_exit",
    ]


def test_unlocked_writer_is_private_restore_primitive():
    content = Path(config_store.__file__).read_text(encoding="utf-8")

    assert "def _save_config_unlocked(" in content
    assert "with configuration_write_lock():" in content
