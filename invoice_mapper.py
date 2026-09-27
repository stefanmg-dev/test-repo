from copy import deepcopy
from typing import Any

from invoice_models import UniversalInvoiceModel


INVOICE_VALUE_FIELDS = frozenset(
    {
        "supplier_name",
        "supplier_id",
        "invoice_number",
        "issue_date",
        "customer_name",
        "customer_address",
        "due_date",
        "total_amount",
        "contract_number",
        "client_number",
        "abonat_number",
        "total_consumption",
        "business_partner_number",
        "contract_account_number",
        "installation_number",
    }
)

INVOICE_COLLECTION_FIELDS = (
    "services",
    "metering_points",
    "meters",
    "consumption_items",
)


def map_extraction_to_universal_invoice(
    *,
    document_type: str,
    final_values: dict[str, Any],
    collections: dict[str, list[dict[str, Any]]],
) -> UniversalInvoiceModel | None:
    if document_type != "invoice":
        return None

    payload = {
        key: deepcopy(value)
        for key, value in final_values.items()
        if key in INVOICE_VALUE_FIELDS
    }
    for collection_name in INVOICE_COLLECTION_FIELDS:
        payload[collection_name] = deepcopy(
            collections.get(collection_name, [])
        )

    return UniversalInvoiceModel.model_validate(payload)
