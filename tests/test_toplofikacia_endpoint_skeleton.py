from fastapi.testclient import TestClient

import routes_extract
from api import app


TOPLOFIKACIA_OCR_TEXT = """
ДОСТАВЧИК: „ТОПЛОФИКАЦИЯ СОФИЯ“ ЕАД
ГР. СОФИЯ УЛ. „ЯСТРЕБЕЦ“ №23Б
ЕИК: 831609046
№ ПО ДДС: BG831609046

ПОЛУЧАТЕЛ: СТЕФАН МОМЧИЛОВ ГЕОРГИЕВ
ГР. СОФИЯ 1618 КРАСНО СЕЛО
БЛ. 201-А ВХ. 4 АПАРТАМЕНТ 68

БИЗНЕС ПАРТНЬОР №1000215239
ДОГОВОРНА СМЕТКА №002100047756
НОМЕР НА ИНСТАЛАЦИЯ №4000374298

ФАКТУРА № 1204458225 - ОРИГИНАЛ
Дата на издаване/Дата на данъчно събитие - 31.08.2026 г.
ВСИЧКО по фактура: 15,12
Срок за плащане на фактура № 1204458225 - 15.10.2026 г.
www.toplo.bg
""".strip()


PDF_QUALITY = {
    "status": "accepted",
    "requires_review": False,
    "input": {
        "format": "PDF",
        "source": "native_pdf",
        "page_count": 3,
    },
    "warnings": [],
}


def test_toplofikacia_endpoint_selects_profile_skeleton(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        await file.read()

        return {
            "text": TOPLOFIKACIA_OCR_TEXT,
            "quality": PDF_QUALITY,
        }

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

    client = TestClient(app)
    response = client.post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "toplofikacia-invoice.pdf",
                b"stable-toplofikacia-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["document_type"] == "invoice"
    assert body["profile"] == (
        "heating_toplofikacia_sofia"
    )

    final_values = body["final_values"]

    assert len(final_values) == 8
    assert set(final_values) == {
        "supplier_name",
        "supplier_id",
        "invoice_number",
        "issue_date",
        "customer_name",
        "customer_address",
        "due_date",
        "total_amount",
    }
    assert final_values["supplier_name"] == (
        "Топлофикация София ЕАД"
    )
    assert final_values["supplier_id"] == "831609046"
    assert final_values["invoice_number"] == "1204458225"
    assert final_values["issue_date"] == "31.08.2026"
    assert final_values["due_date"] == "15.10.2026"
    assert final_values["total_amount"] == "15.12"

    assert "contract_number" not in final_values
    assert "client_number" not in final_values
    assert "abonat_number" not in final_values

    warning_codes = {
        warning["code"]
        for warning in body["quality"]["warnings"]
    }
    assert "unknown_supplier_profile" not in warning_codes
