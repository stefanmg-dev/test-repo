# Configuration guide

## Purpose

This guide explains how administrators and configuration specialists define document types, supplier profiles, extraction fields, collections, and validation rules. Configuration changes affect future processing and should be tested with representative documents before production use.

For the complete creation and acceptance workflow, see [Provider onboarding](provider-onboarding.md).

## Document type and supplier profile

A document type represents a business document category, such as `invoice`, `receipt`, or `contract`. A supplier profile represents one layout or supplier variation inside that category.

For example, `telecom_a1` and `electricity_electrohold` are profiles of the `invoice` document type. A new supplier invoice normally requires a new profile under `invoice`, not a new document type. Create a new document type only when the document has a meaning and structure that is fundamentally different from an invoice.

## Default profile and profile for editing

`default_profile` is the runtime fallback used when supplier matching does not select another profile. The UI field **Profile for editing** only chooses which profile configuration is displayed and edited. Changing the UI selection does not change `default_profile` and does not control the profile selected during document processing.

At runtime, supplier matching evaluates the OCR text and selects the most appropriate configured profile. If no reliable match is available, the configured default profile provides the fallback behavior.

## Common fields and profile fields

### Common fields

Common fields are available to every profile of the document type. Use them for concepts that every invoice should expose, such as invoice number, issue date, due date, total amount, currency, and customer name.

### Profile fields

Profile fields belong to one supplier profile. Use them when the supplier has a unique value, anchor, label, layout, or extraction rule. A profile field with the same system name can provide supplier-specific behavior while preserving the common business field name.

Recommended approach:

1. Define the stable business contract in common fields.
2. Add only genuinely supplier-specific rules to the profile.
3. Keep a generic fallback where practical.
4. Avoid copying every common field into every profile.

## Creating a new profile

1. Confirm that the document is a variation of an existing document type.
2. Choose a stable profile name such as `electricity_supplier_name` using lowercase letters, digits, and underscores.
3. Add supplier-matching evidence that is stable and distinctive in OCR text.
4. Add only the required profile-specific fields and collections.
5. Validate required values, formats, numerical ranges, and collection consistency.
6. Test the profile with representative documents.
7. Confirm in Processing History that the expected profile was selected.
8. Confirm Universal Invoice shadow status for invoice documents.

Do not change `default_profile` merely to inspect or edit another profile. The profile selector in the UI is specifically for that editing task.

## Defining an extraction field

Every field requires a stable system name and an extraction type. Labels are for users; the system name is part of the configuration and API contract.

Example system names:

- `invoice_number`
- `issue_date`
- `total_amount`
- `supplier_id`
- `contract_number`

Use lowercase `snake_case`. Avoid supplier names in common field names.

## Extraction methods

### `constant`

Returns a configured value without searching the document. Use it only when the value is guaranteed by the selected profile.

```json
{
  "name": "supplier_name",
  "type": "constant",
  "value": "Example Supplier AD"
}
```

Typical use: canonical supplier name or a fixed document category.

### `regex`

Applies one regular expression to OCR text. Use a capture group for the value that must be returned.

```json
{
  "name": "invoice_number",
  "type": "regex",
  "rule": "Invoice\\s*(?:No\\.|#)\\s*([A-Z0-9-]+)",
  "occurrence": "first"
}
```

Use `first` when the first valid match is authoritative and `last` when later occurrences are expected to be final totals or summaries.

### `regex_list`

Tries several regular expressions in order and uses the first rule that returns a value.

```json
{
  "name": "invoice_number",
  "type": "regex_list",
  "occurrence": "first",
  "rules": [
    "Invoice\\s*No\\.\\s*([A-Z0-9-]+)",
    "Document\\s*number\\s*([A-Z0-9-]+)"
  ]
}
```

Use it for controlled layout or OCR variations. Put the most specific rule first and keep generic rules last.

### `nearby`

Searches with a regular expression inside a bounded text window around an anchor.

```json
{
  "name": "due_date",
  "type": "nearby",
  "anchor": "Due date",
  "pattern": "([0-9]{2}\\.[0-9]{2}\\.[0-9]{4})",
  "direction": "after",
  "window_size": 200,
  "occurrence": "first"
}
```

Use it when the same value shape occurs many times but a nearby label identifies the correct occurrence. Prefer the smallest reliable window.

### `llm`

Uses the candidate value produced by the configured LLM extraction stage.

```json
{
  "name": "customer_name",
  "type": "llm"
}
```

Use it when layout and wording vary enough that deterministic rules are not reliable. Add validation because contextual extraction can still return missing or malformed values.

## Choosing an extraction method

Use this order of preference:

1. `constant` for a value guaranteed by the profile.
2. `regex` for one stable and unambiguous format.
3. `regex_list` for a small known set of format variations.
4. `nearby` when an anchor is needed to disambiguate repeated values.
5. `llm` when the value needs semantic context or has unstable placement and wording.

Prefer deterministic methods when they are stable. Do not replace a reliable rule with an LLM rule merely because the LLM rule is shorter to configure.

## Validation

Extraction finds a candidate value. Validation decides whether that value is acceptable.

Typical validations include:

- required value;
- regex format;
- date format;
- decimal format;
- minimum and maximum values;
- collection item validation;
- collection summary consistency.

A successful extraction with failed validation can require human review or become invalid according to the processing rules.

## Collections

Collections represent repeating structures such as services, meters, metering points, or consumption items. Define collection fields with the same discipline as scalar fields. Keep collection item validation separate from summary validation so users can identify whether one item is malformed or the aggregate is inconsistent.

## Testing and safe rollout

1. Save the configuration through the UI or versioned API.
2. Submit a representative document in the test interface.
3. Review selected profile, extracted values, collections, validation, and review requirement.
4. Open the persisted run in Processing History.
5. Compare original and corrected values if human review is required.
6. For invoices, inspect Universal Invoice shadow status and preview.
7. Introduce broader rules only after checking that existing profiles still behave correctly.

## Common mistakes

- Creating a new document type for every supplier instead of adding a profile.
- Editing `default_profile` when the intention is only to inspect another profile.
- Duplicating common fields across all profiles.
- Using a regex without a capture group for the returned value.
- Putting a generic regex before a more specific rule in `regex_list`.
- Using an excessively large `nearby` window.
- Using `llm` without validation.
- Testing only the new supplier and not checking regression behavior for existing profiles.
