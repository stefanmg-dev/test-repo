# Processing acceptance contract

This document defines the current runtime decision contract for document processing. It documents existing behavior and does not introduce a new status or change extraction results.

## Decision precedence

Processing status is determined in this order:

1. `invalid` when scalar validation does not return `valid: true`.
2. `invalid` when collection or collection-summary validation is present and does not return `valid: true`.
3. `review` when all validation scopes pass but input quality or profile resolution sets `requires_review: true`.
4. `accepted` when all validation scopes pass and `requires_review` is not true.

Validation failure always has precedence over review warnings.

## Status contract

| Status | Required conditions | Meaning |
|---|---|---|
| `accepted` | Scalar validation passes; collection validation passes or is absent; `requires_review` is false or absent | Processing completed and no configured blocking validation or review condition remains. |
| `review` | Scalar and collection validation pass; `requires_review` is true | Processing completed, but a non-blocking quality or profile-resolution condition requires human verification. |
| `invalid` | Scalar validation fails, or collection/item/summary validation fails | Processing completed, but at least one configured blocking validation rule failed. |

## Quality decision

Input quality uses `accepted` or `review`; it does not directly produce `invalid`.

For images, the current accepted-dimension thresholds are:

- short edge at least `1400` pixels;
- long edge at least `2000` pixels.

If either edge is below its threshold, input quality adds the stable warning code `low_image_resolution`, sets quality status to `review`, and sets `requires_review: true`.

Supplier-profile resolution may also add stable warning codes and set `requires_review: true`. Those warnings are merged with input-quality warnings before the final processing decision.

## Stable reason sources

The current machine-readable reason sources are:

- `quality.warnings[*].code` for non-blocking input-quality and profile-resolution review reasons;
- `validation.errors` for blocking scalar validation reasons;
- `collection_validation.errors` for blocking collection-item and collection-summary reasons;
- `field_evidence[*].failure_reason` for scalar extraction diagnostics;
- `collection_evidence[collection][item][field].failure_reason` for collection extraction diagnostics;
- `invoice_shadow_validation_reason` for safe Universal Invoice shadow-validation failure classification.

Processing status itself remains a compact outcome. Consumers should use the structures above for detailed reasons rather than deriving a new reason from human-readable messages.

## Examples

| Scalar validation | Collection validation | Requires review | Result |
|---|---|---|---|
| Pass | Pass or absent | No | `accepted` |
| Pass | Pass or absent | Yes | `review` |
| Fail | Any | Any | `invalid` |
| Pass | Fail | Any | `invalid` |

## Acceptance rules for future changes

- Do not introduce a new processing status without updating the Pydantic model, OpenAPI export, API reference, persistence consumers, UI, and tests.
- Keep validation failures blocking and quality/profile warnings non-blocking unless an explicit versioned contract change is approved.
- Add a stable warning code or structured validation path before adding logic that depends on a human-readable message.
- Preserve the precedence of `invalid` over `review`.
- Keep provider-specific acceptance rules in document configuration or profile data rather than branching in the core status function.
