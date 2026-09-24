from unittest.mock import Mock
from uuid import uuid4

import pytest

from database_models import ProcessingRun
from processing_run_service import (
    ProcessingRunNotFoundError,
    ProcessingRunService,
)


def test_get_run_returns_existing_run():
    session = Mock()
    processing_run = ProcessingRun(
        id=uuid4(),
        document_type="invoice",
        filename="invoice.pdf",
        input_format="pdf",
        processing_status="accepted",
        requires_review=False,
        tenant_id="tenant-1",
    )
    session.get.return_value = processing_run

    result = ProcessingRunService(session).get_run(
        processing_run.id
    )

    assert result is processing_run


def test_get_run_requires_existing_run():
    session = Mock()
    session.get.return_value = None
    run_id = uuid4()

    with pytest.raises(
        ProcessingRunNotFoundError,
        match=str(run_id),
    ):
        ProcessingRunService(session).get_run(run_id)


def test_list_runs_returns_items_and_total():
    session = Mock()
    item = ProcessingRun(
        id=uuid4(),
        document_type="invoice",
        filename="invoice.pdf",
        input_format="pdf",
        processing_status="accepted",
        requires_review=False,
    )
    session.scalars.return_value.all.return_value = [item]
    session.scalar.return_value = 7

    items, total = ProcessingRunService(session).list_runs(
        offset=20,
        limit=10,
        document_type="invoice",
        processing_status="accepted",
        profile="telecom_a1",
        requires_review=False,
        tenant_id="tenant-1",
    )

    assert items == [item]
    assert total == 7
    session.scalars.assert_called_once()
    session.scalar.assert_called_once()
    list_sql = str(session.scalars.call_args.args[0])
    count_sql = str(session.scalar.call_args.args[0])
    for sql in (list_sql, count_sql):
        assert "processing_runs.document_type" in sql
        assert "processing_runs.processing_status" in sql
        assert "processing_runs.profile" in sql
        assert "processing_runs.requires_review" in sql
        assert "processing_runs.tenant_id" in sql


def test_get_run_can_be_tenant_scoped():
    session = Mock()
    item = ProcessingRun(
        id=uuid4(),
        tenant_id="tenant-1",
        created_by_type="service",
        created_by_subject="service-1",
        document_type="invoice",
        filename="invoice.pdf",
        input_format="pdf",
        processing_status="accepted",
        requires_review=False,
    )
    session.scalar.return_value = item

    result = ProcessingRunService(session).get_run(
        item.id,
        tenant_id="tenant-1",
    )

    assert result is item
    sql = str(session.scalar.call_args.args[0])
    assert "processing_runs.id" in sql
    assert "processing_runs.tenant_id" in sql
