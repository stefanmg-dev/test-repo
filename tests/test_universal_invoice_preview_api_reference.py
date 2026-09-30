from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def preview_section() -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(
        "### GET `/api/v1/processing-runs/{run_id}/universal-invoice`"
    )
    end = content.index("### POST `/extract-document`", start)
    return content[start:end]


def test_universal_invoice_preview_reference_documents_boundary():
    content = preview_section()

    assert "read-only" in content
    assert "versioned Universal Invoice preview" in content
    assert "processing-runs:read" in content
    assert "Tenant isolation" in content
    assert "`run_id` (UUID, required)" in content


def test_universal_invoice_preview_reference_explains_semantics():
    content = preview_section()

    for field_name in (
        "schema_version",
        "supplier_name",
        "supplier_id",
        "invoice_number",
        "issue_date",
        "due_date",
        "customer_name",
        "customer_address",
        "total_amount",
        "contract_number",
        "client_number",
        "abonat_number",
        "business_partner_number",
        "contract_account_number",
        "installation_number",
        "total_consumption",
        "services",
        "metering_points",
        "meters",
        "consumption_items",
    ):
        assert f"`{field_name}`" in content

    assert "Nullable scalar fields" in content
    assert "empty arrays" in content
    assert "strings, integers, or floating-point numbers" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content
