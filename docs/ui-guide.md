# User interface guide

## Intended audience

The browser UI is designed for administrators, configuration specialists, testers, operations users, and human reviewers. It helps users configure extraction behavior, test documents, inspect processing history, review results, and monitor Universal Invoice shadow quality.

## Technology

- HTML, CSS, and browser JavaScript served by FastAPI as same-origin static assets.
- Microsoft Entra browser authentication through MSAL Browser 5.19.0.
- Authentication bundle built with esbuild 0.25.10.
- Chromium regression coverage through Playwright 1.63.0.

## Navigation and screens

### Main configuration interface

The main interface loads document types and their extraction configuration. It is used to inspect and maintain fields, supplier profiles, collection definitions, validation rules, and related configuration structures.

Typical sequence:

1. Open the application root, which redirects to `/ui/index.html`.
2. Sign in when browser OIDC is enabled.
3. Select a document type.
4. Review common fields and profile-specific configuration.
5. Add, update, or remove supported configuration elements when the principal has `config:write`.
6. Re-test extraction after configuration changes.

### Document test interface

The test interface is intended for controlled manual validation rather than bulk production ingestion.

Typical sequence:

1. Select a configured document type.
2. Select a local supported document.
3. Submit the document for extraction.
4. Review the returned status, profile, structured fields, collections, quality indicators, and validation details.
5. Use the processing-run identifier to continue investigation in history.

The interface must not be used to store credentials or permanent copies of uploaded documents.

### Processing History

Processing History lists tenant-visible runs and provides filters for status, profile, review requirement, Universal Invoice shadow status, and invoice schema version.

The detail view shows processing metadata, timings, configuration identity, review state, final/corrected values where authorized, collections, safe shadow metadata, and failure reason codes. Invoice runs can expose a read-only Universal Invoice preview through the dedicated endpoint.

### Human review

Runs requiring review can be approved, corrected, or rejected through the review workflow. Corrected values are stored separately from original final values, preserving the original extraction result for comparison and quality analysis.

### Universal Invoice monitoring

The history UI displays tenant-aware Universal Invoice shadow summary metrics, schema-version breakdown, status filters, and safe failure reasons. The preview is available only for invoice runs and handles unavailable mappings without exposing internal exception details.

### Authentication controls

When browser authentication is enabled, the UI initializes public authentication configuration from `/api/v1/auth/config`, obtains access tokens through MSAL, and uses authenticated requests for protected operations. No client secret is present in the browser.

## User-visible status model

- `accepted`: validation succeeded and human review is not required.
- `review`: processing completed but quality rules require human review.
- `invalid`: field or collection validation failed.
- Failure responses: the request could not complete because of upload, configuration, OCR, extraction, mapping, authorization, or infrastructure constraints.

## Operational guidance

- Use Processing History as the authoritative investigation view.
- Use the Universal Invoice preview only as a read-only normalized representation.
- Run retention preview before retention execution.
- Treat retention execution as irreversible.
- Keep API keys, bearer tokens, invoices, raw OCR, and personal data out of committed Postman environments and documentation.

## Interface structure

- `/ui/index.html`: configuration workspace for document types, fields, profiles, collections, and validation rules.
- `/ui/test.html`: controlled extraction test workspace for a selected local document.
- `/ui/history.html`: processing-run search, detail inspection, review, shadow monitoring, and Universal Invoice preview.
- Authentication controls: sign-in, sign-out, token acquisition, and authenticated API requests when browser OIDC is enabled.

## Typical end-to-end user journey

1. A configuration specialist defines or updates the document type and supplier profile.
2. A tester submits a representative document through the test interface.
3. The extraction response presents structured values, collections, quality, and validation information.
4. Processing History provides the persisted record, status, timings, configuration identity, and shadow metadata.
5. A reviewer approves, corrects, or rejects runs that require human review.
6. An operator monitors shadow summary and safe failure reasons before enabling downstream use of normalized Universal Invoice data.

