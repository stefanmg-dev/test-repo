from extractor import (
    extract_supplier_name,
    extract_supplier_id,
    extract_invoice_number,
    extract_issue_date,
    extract_contract_number,
    extract_customer_name,
    extract_customer_address,
    extract_due_date,
    extract_total_amount
)


def extract_invoice(text):

    return {
        "supplier_name": extract_supplier_name(text),
        "supplier_id": extract_supplier_id(text),
        "invoice_number": extract_invoice_number(text),
        "issue_date": extract_issue_date(text),
        "contract_number": extract_contract_number(text),
        "customer_name": extract_customer_name(text),
        "customer_address": extract_customer_address(text),
        "due_date": extract_due_date(text),
        "total_amount": extract_total_amount(text),
    }