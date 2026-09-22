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
    )

    assert items == [item]
    assert total == 7
    session.scalars.assert_called_once()
    session.scalar.assert_called_once()
