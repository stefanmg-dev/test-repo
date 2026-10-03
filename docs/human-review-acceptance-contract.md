# Human review acceptance contract

This document defines the current end-to-end contract for processing runs that require human review. It documents existing runtime behavior without changing review semantics.

## Entry conditions

A processing run enters the review workflow only when:

- processing completed with `requires_review: true`;
- `review_status` is initialized to `pending`;
- original `final_values`, collections, validation metadata, quality warnings, and extraction evidence are persisted.

Runs that do not require review cannot receive a review decision.

## Terminal decisions

The supported terminal decisions are:

| Decision | Corrected values | Effective values | Meaning |
|---|---|---|---|
| `approved` | Not allowed | Original `final_values` | The reviewer accepts the extracted result without correction. |
| `corrected` | Required | `corrected_values` | The reviewer replaces the effective scalar result while preserving the original extraction. |
| `rejected` | Not allowed | `null` | The reviewer rejects the extracted result for downstream use. |

Every decision is terminal. A completed review cannot be submitted again.

## Persistence and audit contract

A successful review persists:

- terminal `review_status`;
- optional `corrected_values` only for `corrected`;
- optional `review_comment`;
- `reviewed_at` timestamp;
- `reviewed_by_type`;
- `reviewed_by_subject`.

Original `final_values`, collections, evidence, quality, and validation metadata remain unchanged. The review decision is recorded atomically so concurrent submissions cannot both succeed.

## Effective-value contract

Effective scalar values are resolved as follows:

1. `rejected` returns no effective values.
2. `corrected` returns `corrected_values`.
3. `pending` and `approved` return original `final_values`.

Consumers must not overwrite original extraction values with reviewer corrections.

## API and UI workflow

The supported workflow is:

```text
extract
→ requires_review=true and review_status=pending
→ GET processing-run detail or review state
→ inspect values, collections, quality, validation, and evidence
→ POST one approved, corrected, or rejected decision
→ retrieve persisted audit metadata and effective values
→ include reviewed runs in feedback and quality analysis
```

The history UI exposes review actions only for pending runs. Corrected decisions require a corrected-values JSON object. Approved and rejected decisions must not send corrected values.

Corrected values are rejected for approved and rejected decisions. A corrected review requires corrected values, while a rejected review returns no effective values.

## Security and tenancy

- Review endpoints require the `processing-runs:review` scope when authentication is enabled.
- Tenant isolation applies to review reads and writes.
- Audit events record the decision and safe principal metadata without logging extracted or corrected customer values.
- Feedback export remains tenant-scoped and contains only reviewed invoice runs allowed by its API contract.

## Acceptance checklist

The review workflow is accepted only when:

- a review-required extraction is persisted as pending;
- pending review returns original effective values;
- approved review returns original effective values;
- corrected review requires and returns corrected values;
- rejected review returns no effective values;
- corrected values are rejected for approved and rejected decisions;
- non-review runs reject review submissions;
- repeated or concurrent terminal decisions are rejected;
- reviewer identity, comment, and timestamp persist;
- original extraction values and evidence remain unchanged;
- tenant isolation is covered by integration tests;
- feedback export and quality analysis consume terminal reviewed runs consistently.
