from types import SimpleNamespace
from uuid import uuid4

import pytest

from api import app
from processing_run_dependencies import (
    get_processing_run_service,
)
from security_dependencies import (
    get_optional_api_key_principal,
    get_optional_principal,
)


class NoOpProcessingRunService:
    def start_run(self, **kwargs):
        return SimpleNamespace(id=uuid4())

    def complete_run(self, run_id, **kwargs):
        return None

    def fail_run(self, run_id, **kwargs):
        return None


@pytest.fixture(autouse=True)
def override_processing_run_service():
    service = NoOpProcessingRunService()
    app.dependency_overrides[
        get_processing_run_service
    ] = lambda: service
    yield
    app.dependency_overrides.pop(
        get_processing_run_service,
        None,
    )
    app.dependency_overrides.pop(
        get_optional_api_key_principal,
        None,
    )
    app.dependency_overrides.pop(
        get_optional_principal,
        None,
    )
