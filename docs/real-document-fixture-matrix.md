# Real-document fixture matrix and acceptance checklist

This document defines the local, privacy-preserving acceptance matrix for real invoice fixtures. Real customer documents remain outside Git under `uploaded_documents/manual-regression/` or another explicitly configured local path.

## Baseline command

Run the versioned PDF acceptance suite with:

```bash
python scripts/manual_invoice_regression.py
```

A successful baseline reports:

```text
PASS A1: passed
PASS Electrohold: passed
PASS Toplofikacia: passed
SUMMARY passed=3 failed=0
```

The command exits non-zero when a required PDF fixture is missing or a mapped E2E test fails.

## Fixture matrix

| Case | Local fixture or variable | Acquisition path | Expected profile | Scalar acceptance | Collection acceptance | Validation acceptance | Expected outcome |
|---|---|---|---|---|---|---|---|
| A1 PDF | `uploaded_documents/manual-regression/a1.pdf` or `A1_REAL_PDF_PATH` | Native PDF and/or OCR through the document endpoint | `telecom_a1` | Non-empty normalized values | Document configuration dependent | Scalar validation returns a boolean result | `accepted` or `review` |
| Electrohold PDF | `uploaded_documents/manual-regression/electrohold.pdf` or `ELECTROHOLD_REAL_PDF_PATH` | Document endpoint | `electricity_electrohold` | Configured invoice fields | Metering point, meter, and consumption rows match the approved fixture | Scalar, collection, and summary validation pass | `accepted` |
| Toplofikacia PDF | `uploaded_documents/manual-regression/toplofikacia.pdf` or `TOPLOFIKACIA_REAL_PDF_PATH` | Document endpoint | `heating_toplofikacia_sofia` | All configured scalar fields are non-empty | Service rows match the approved fixture | Scalar and collection validation pass | `accepted` |
| A1 JPEG variants | `A1_REAL_JPEG_DIR` | Real OCR for five JPEG quality/orientation variants | Scalar rule configuration | Supplier ID, invoice number, dates, amount, and contract number match | Not applicable in the current JPEG test | Input quality matches the expected variant status | One low-resolution variant is `review`; the other variants are `accepted` |
| Synthetic image-only PDF | Versioned synthetic test fixture | Poppler rendering and OCR stub | Test configuration | Expected scalar values | Test-dependent | Cleanup and pipeline assertions pass | Deterministic regression only |

## Acceptance checklist for every real fixture

A real fixture is accepted into the matrix only when all applicable checks are explicit:

- The fixture remains outside Git and contains no committed customer data.
- The test selects the expected supplier profile.
- Required scalar fields have exact expected normalized values or an explicitly justified non-empty assertion.
- Required collections have exact item order and field values.
- Scalar validation, collection validation, and summary validation have explicit expectations.
- Input quality and `requires_review` have explicit expectations where OCR quality is relevant.
- Processing outcome is explicitly asserted as `accepted`, `review`, or `invalid`.
- Failure output identifies the provider and fixture case without printing sensitive document content.
- A discovered defect is classified as OCR, profile matching, configuration, rule extraction, normalization, collection splitting, or validation before code is changed.
- Core extraction code is changed only for a provider-independent defect; provider-specific behavior stays in configuration or profile data.

## Current local baseline

The three required PDF cases are executed by `scripts/manual_invoice_regression.py`. The A1 JPEG matrix is optional until `A1_REAL_JPEG_DIR` points to the local JPEG fixture directory.

Do not copy real documents into versioned test directories. Do not include extracted customer values in documentation, logs, or commit messages.

## Adding another provider

1. Store the real fixture outside Git.
2. Add one environment-variable-based E2E test with explicit profile, field, collection, validation, quality, and outcome assertions.
3. Add the case to this matrix.
4. Add it to `scripts/manual_invoice_regression.py` only when the local fixture filename and acceptance test are stable.
5. Run the real baseline, the deterministic test suite, Alembic check, CI, and supply-chain checks before declaring a new checkpoint.
