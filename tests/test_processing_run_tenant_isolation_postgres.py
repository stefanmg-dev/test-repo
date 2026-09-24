import os

import pytest


if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )

from database import SessionLocal
from database_models import ProcessingRun
from processing_run_service import (
    ProcessingRunNotFoundError,
    ProcessingRunService,
)


def test_processing_runs_are_filtered_by_tenant():
    session = SessionLocal()
    created_ids = []
    try:
        service = ProcessingRunService(session)
        first = service.start_run(
            document_type="invoice",
            filename="tenant-a.pdf",
            input_format="pdf",
            tenant_id="tenant-a",
            created_by_type="service",
            created_by_subject="service-a",
        )
        second = service.start_run(
            document_type="invoice",
            filename="tenant-b.pdf",
            input_format="pdf",
            tenant_id="tenant-b",
            created_by_type="service",
            created_by_subject="service-b",
        )
        created_ids.extend([first.id, second.id])

        items, total = service.list_runs(
            offset=0,
            limit=100,
            tenant_id="tenant-a",
        )
        ids = {item.id for item in items}
        assert first.id in ids
        assert second.id not in ids
        assert total >= 1

        assert service.get_run(
            first.id,
            tenant_id="tenant-a",
        ).id == first.id
        with pytest.raises(ProcessingRunNotFoundError):
            service.get_run(
                second.id,
                tenant_id="tenant-a",
            )
    finally:
        session.rollback()
        if created_ids:
            session.query(ProcessingRun).filter(
                ProcessingRun.id.in_(created_ids)
            ).delete(synchronize_session=False)
            session.commit()
        session.close()
