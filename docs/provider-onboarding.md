# Provider onboarding

## Purpose

This checklist defines the acceptance contract for adding a supplier profile without provider-specific runtime Python code. Supplier identity, extraction rules, collections, and validations belong in configuration. Runtime code changes are allowed only for provider-independent defects or capabilities.

## Entry criteria

Before creating a profile:

- Confirm that the document belongs to an existing document type.
- Store real customer fixtures outside Git.
- Choose a stable lowercase `snake_case` profile name.
- Identify stable OCR evidence that distinguishes the supplier.
- Classify every required value as common, profile-specific, or collection data.
- Record expected processing outcome: `accepted`, `review`, or `invalid`.

## Matching contract

Every production profile must define `matching.any_of`. Every rule contains:

- `code`: a stable lowercase evidence identifier;
- `pattern`: a valid regular expression evaluated against normalized OCR text.

Example:

```json
{
  "matching": {
    "any_of": [
      {
        "code": "synthetic_provider_company",
        "pattern": "\\bsynthetic provider ead\\b"
      },
      {
        "code": "synthetic_provider_domain",
        "pattern": "(?<![\\w.-])synthetic\\.example(?![\\w.-])"
      }
    ]
  }
}
```

Use evidence that is stable and supplier-specific, such as an official legal name or official domain. Do not use weak markers such as a short token, page coordinate, generic invoice label, or customer-specific value.

Matching acceptance requires:

- a positive company-name case;
- every supported OCR or language variant;
- an official-domain case when a domain rule exists;
- negative lookalike cases;
- an unknown supplier case returning `profile=None`;
- an ambiguous multi-supplier case returning `profile=None` and requiring review;
- stable evidence codes in the extraction result.

When any profile has configured matching, configuration-driven matching is authoritative. Do not rely on the legacy matcher as a hidden fallback.

## Field and collection design

Use common fields for stable business concepts shared by all profiles. Use profile fields only for supplier-specific labels, anchors, layouts, or values. Avoid copying the complete common-field set into each profile.

For every scalar field:

- choose the least complex reliable extraction method;
- define normalization expectations;
- add required, format, date, decimal, or range validation where applicable;
- test absent, malformed, and repeated values.

For every collection:

- define cardinality;
- define a stable item boundary when required;
- assert exact item order and values for approved fixtures;
- add item validations for within-row consistency;
- add summary validations for aggregate consistency.

## Deterministic acceptance tests

A new provider requires versioned deterministic tests that cover:

- matching and evidence codes;
- profile selection;
- common and profile field resolution;
- scalar extraction and normalization;
- collection extraction when applicable;
- scalar, collection, and summary validation;
- unknown and ambiguous supplier safety;
- endpoint response profile and processing status;
- regression safety for existing providers.

Synthetic fixtures must not contain real customer data.

## Real-document acceptance

Keep real fixtures outside Git under `uploaded_documents/manual-regression/` or an explicitly configured local path. Add an environment-variable-based E2E test with explicit expectations for:

- selected profile;
- required normalized scalar values;
- collection rows and order;
- validation outcome;
- input quality and `requires_review`;
- final processing outcome.

Add the provider to `docs/real-document-fixture-matrix.md`. Add the case to `scripts/manual_invoice_regression.py` only after the fixture filename and E2E test are stable. Failure output must identify the provider without printing sensitive document content.

## Verification gate

Before declaring an onboarding checkpoint complete, run:

1. Targeted matching, pipeline, extraction, validation, and endpoint tests.
2. Full `pytest`.
3. The real-document baseline.
4. Configuration load and validation.
5. Alembic current and schema parity checks.
6. Static OpenAPI export and contract checks when schemas changed.
7. CI and supply-chain security workflows.
8. Final `git status` confirming a clean working tree.

## Change classification

Classify every defect before changing code:

- OCR;
- profile matching;
- configuration;
- scalar rule extraction;
- normalization;
- collection splitting;
- validation;
- provider-independent runtime defect.

Keep provider-specific behavior in `document_types.json`. Change core Python only when the defect is provider-independent and add a synthetic regression proving that general behavior.

## Completion checklist

A provider is onboarded only when:

- configuration validation passes;
- matching is distinctive and ambiguity-safe;
- unknown supplier behavior remains common-only review;
- deterministic tests are green;
- the real fixture passes its explicit acceptance contract;
- existing provider baselines remain green;
- no customer document or sensitive extracted value is committed;
- documentation and fixture matrix are updated;
- CI and security workflows are green;
- the repository is clean at the recorded checkpoint.
