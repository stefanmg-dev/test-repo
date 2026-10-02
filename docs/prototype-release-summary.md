# Prototype release summary

## Release checkpoint

The prototype release candidate is based on commit `f4c89d8` (`Add nearby extraction normalization regression`). At this checkpoint, `main`, `origin/main`, and `HEAD` are synchronized and the working tree is clean.

Release verification completed with:

- 923 passed tests and 4 intentionally skipped environment-dependent tests;
- no pending Alembic upgrade operations;
- a reproducible and unchanged OpenAPI export;
- clean Git whitespace and working-tree checks;
- successful GitHub Actions CI, vulnerability audit, and SPDX SBOM generation for the preceding stable checkpoints.

## Implemented prototype capabilities

- Synchronous PDF, PNG, JPG, and JPEG document ingestion with upload validation and temporary-file cleanup.
- Native PDF text extraction and OCR processing for image-based input.
- Synthetic image-only multi-page PDF regression with real Poppler rendering.
- Profile-based and legacy document configuration APIs with fields, collections, validations, and resolved configuration.
- Deterministic extraction rules including constants, regular expressions, regex lists, nearby-anchor extraction, occurrence selection, and decimal normalization.
- Supplier-profile resolution with common-only fallback for unknown suppliers.
- Collection extraction, cardinality, item validation, arithmetic validation, and summary validation.
- PostgreSQL processing-run lifecycle, history, review, summaries, CSV export, retention controls, and tenant isolation.
- Versioned Universal Invoice shadow validation, preview, and bounded JSONL feedback export.
- API-key and OIDC bearer authentication, scope authorization, browser OIDC foundation, rate limiting, and security audit logging.
- Production container foundation, liveness/readiness checks, migration parity, backup/restore helpers, and deployment smoke automation.
- Administrative UI coverage for configuration, processing history, authentication controls, and human review.
- OpenAPI and API-reference audits for Configuration, extraction, and processing-run operations.

## Prototype acceptance evidence

The acceptance suites cover upload-to-processing lifecycle behavior, persistence, review, tenant isolation, authentication, retention contracts, backup/restore safeguards, deployment smoke behavior, security audit metadata, UI behavior, and real PDF page rendering. Environment-dependent real-provider fixtures remain optional and are not required for the deterministic CI baseline.

## Current boundaries

- Processing remains synchronous.
- The UI is an administrative and expert workspace rather than the primary production ingestion channel.
- The container model uses one Uvicorn process per container.
- Automatic retention scheduling is disabled.
- HEIF and HEIC are outside the current scope.
- Production-specific monitoring thresholds, infrastructure sizing, shared rate-limit storage, concurrency limits, timeout policy, incident ownership, backup schedules, recovery objectives, and recurring restore exercises remain deployment decisions.

## Deferred architecture

Asynchronous processing with `202 Accepted`, job identifiers, polling, queues, retries, delivery guarantees, idempotency, and webhooks is intentionally deferred until concrete external integration requirements exist.

## Operational references

- [System architecture](architecture.md)
- [Production deployment](deployment.md)
- [Security plan](security.md)
- [PostgreSQL backup and restore runbook](backup-restore.md)
- [Production deployment smoke test](deployment-smoke-test.md)
- [Development quick reference](development-quick-reference.md)
- [API reference](api-reference.md)
