import copy

import pytest
from fastapi.testclient import TestClient

import routes_extract
from api import app
from config_store import load_config


BASE_TEXT = """
ТОПЛОФИКАЦИЯ СОФИЯ ЕАД
ЕИК: 831609046
www.toplo.bg

ПОЛУЧАТЕЛ: ТЕСТОВ КЛИЕНТ ПРИМЕРЕН
ГР. СОФИЯ 1000 ТЕСТОВ КВАРТАЛ БЛ. 1 ВХ. А АПАРТАМЕНТ 1

БИЗНЕС ПАРТНЬОР №1000000001
ДОГОВОРНА СМЕТКА №002100000001
НОМЕР НА ИНСТАЛАЦИЯ №4000000001

ФАКТУРА № 1200000001 - ОРИГИНАЛ
Дата на издаване/Дата на данъчно събитие - 31.08.2026

ВСИЧКО по фактура: 15,12
Оставаща сума за плащане по фактура 1200000001 15,12 Евро
Срок за плащане на фактура № 1200000001 - 15.10.2026
""".strip()


SERVICE_ONE = (
    "Топлинна енергия за отопление на имот "
    "МВтч 1,000000 13,07 13,07"
)

SERVICE_TWO = (
    "Дялово разпределение на топлинна енергия "
    "(1/12 част) бр 1 2,05 2,05"
)


PDF_QUALITY = {
    "status": "accepted",
    "requires_review": False,
    "input": {
        "format": "PDF",
        "source": "native_pdf",
        "page_count": 1,
    },
    "warnings": [],
}


def exactly_one_config():
    config = copy.deepcopy(load_config())

    services_schema = config[
        "invoice"
    ]["profiles"][
        "heating_toplofikacia_sofia"
    ]["collections"]["services"]

    services_schema["cardinality"] = "exactly_one"

    return config


def post_invoice(
    monkeypatch,
    raw_text,
):
    config = exactly_one_config()

    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": raw_text,
            "quality": PDF_QUALITY,
        }

    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: config,
    )
    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fake_extract_document_input,
    )
    monkeypatch.setattr(
        routes_extract,
        "extract_values",
        lambda text: {},
    )

    return TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "toplofikacia-exactly-one.pdf",
                b"toplofikacia-exactly-one-fixture",
                "application/pdf",
            )
        },
    )


@pytest.mark.parametrize(
    (
        "service_rows",
        "expected_count",
        "expected_status",
        "expected_collection_valid",
    ),
    [
        (
            [],
            0,
            "invalid",
            False,
        ),
        (
            [SERVICE_ONE],
            1,
            "accepted",
            True,
        ),
        (
            [
                SERVICE_ONE,
                SERVICE_TWO,
            ],
            2,
            "invalid",
            False,
        ),
    ],
)
def test_endpoint_enforces_exactly_one_collection(
    monkeypatch,
    service_rows,
    expected_count,
    expected_status,
    expected_collection_valid,
):
    raw_text = "\n".join(
        [
            BASE_TEXT,
            *service_rows,
        ]
    )

    response = post_invoice(
        monkeypatch=monkeypatch,
        raw_text=raw_text,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == (
        "heating_toplofikacia_sofia"
    )
    assert body["quality"] == PDF_QUALITY

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }

    assert len(
        body["collections"]["services"]
    ) == expected_count

    assert (
        body["collection_validation"]["valid"]
        is expected_collection_valid
    )
    assert body["processing_status"] == expected_status

    collection_errors = body[
        "collection_validation"
    ]["errors"]

    if expected_collection_valid:
        assert collection_errors == {}
    else:
        assert set(collection_errors) == {
            "_services",
        }
        assert collection_errors["_services"]


def test_exactly_one_violation_does_not_change_input_quality(
    monkeypatch,
):
    response = post_invoice(
        monkeypatch=monkeypatch,
        raw_text=BASE_TEXT,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["processing_status"] == "invalid"
    assert body["quality"]["status"] == "accepted"
    assert body["quality"]["requires_review"] is False
    assert body["validation"]["valid"] is True
    assert body["collection_validation"]["valid"] is False
