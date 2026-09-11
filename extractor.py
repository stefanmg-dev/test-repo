import re


def extract_supplier_name(text):

    if "А1 България" in text or "A1" in text:
        return "А1 България ЕАД"

    return None


def extract_supplier_id(text):

    match = re.search(
        r"ЕИК[:\s]*([0-9]{9,13})",
        text
    )

    return match.group(1) if match else None


def extract_invoice_number(text):

    match = re.search(
        r"Фактура[^0-9]{0,10}([0-9]{8,15})",
        text
    )

    return match.group(1) if match else None


def extract_issue_date(text):

    match = re.search(
        r"Дата на издаване[:\s]*([0-9]{2}\.[0-9]{2}\.[0-9]{4})",
        text
    )

    return match.group(1) if match else None


def extract_contract_number(text):

    match = re.search(
        r"Договор\s*(?:No|№)?[:\s]*([A-Z0-9]+)",
        text
    )

    return match.group(1) if match else None


def extract_due_date(text):

    match = re.search(
        r"Краен срок на плащане[:\s]*([0-9]{2}\.[0-9]{2}\.[0-9]{4})",
        text
    )

    return match.group(1) if match else None


def extract_total_amount(text):

    matches = re.findall(
        r"Обща стойност за плащане\s*([0-9]+\.[0-9]+)",
        text
    )

    return matches[-1] if matches else None


def extract_customer_name(text):

    match = re.search(
        r"Име:\s*Адрес:\s*(.*?)\s*жк",
        text,
        re.DOTALL
    )

    if match:
        return match.group(1).strip()

    return None


def extract_customer_address(text):

    match = re.search(
        r"жк.+?(?=Дата на дан\. събитие)",
        text,
        re.DOTALL
    )

    return match.group(0).strip() if match else None