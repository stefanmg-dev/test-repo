import copy

from fastapi.testclient import TestClient

import routes_extract
from api import app
from config_store import load_config


TOPLOFIKACIA_TEXT_WITHOUT_SERVICES = """
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


def test_endpoint_is_invalid_for_empty_one_or_more_collection(
    monkeypatch,
):
    config = copy.deepcopy(load_config())

    services_schema = config[
        "invoice"
    ]["profiles"][
        "heating_toplofikacia_sofia"
    ]["collections"]["services"]

    services_schema["cardinality"] = "one_or_more"

    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": TOPLOFIKACIA_TEXT_WITHOUT_SERVICES,
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
        lambda raw_text: {},
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "toplofikacia-no-services.pdf",
                b"toplofikacia-no-services-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == "heating_toplofikacia_sofia"

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }

    assert body["collections"]["services"] == []

    assert body["collection_validation"] == {
        "valid": False,
        "errors": {
            "_services": [
                "Collection must contain at least one item",
            ]
        },
    }

    assert body["processing_status"] == "invalid"

    assert body["quality"] == PDF_QUALITY


def test_endpoint_accepts_empty_zero_or_more_collection(
    monkeypatch,
):
    config = copy.deepcopy(load_config())

    services_schema = config[
        "invoice"
    ]["profiles"][
        "heating_toplofikacia_sofia"
    ]["collections"]["services"]

    assert services_schema["cardinality"] == "zero_or_more"

    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": TOPLOFIKACIA_TEXT_WITHOUT_SERVICES,
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
        lambda raw_text: {},
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "toplofikacia-optional-services.pdf",
                b"toplofikacia-optional-services-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == "heating_toplofikacia_sofia"

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }

    assert body["collections"]["services"] == []

    assert body["collection_validation"] == {
        "valid": True,
        "errors": {},
    }

    assert body["processing_status"] == "accepted"
    assert body["quality"] == PDF_QUALITY
