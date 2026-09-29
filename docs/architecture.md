# System architecture

## Purpose and scope

This system processes business documents through a synchronous API pipeline. It validates uploads, extracts text, resolves document configuration and supplier profile, produces structured values and collections, validates the result, persists the processing lifecycle in PostgreSQL, and supports expert review and operational history.

The current user interface is primarily an administrative, testing, monitoring, and human-review workspace. It is not the primary production ingestion channel.

## Technology baseline

| Component | Technology | Version / source of truth | Purpose |
|---|---|---:|---|
| Runtime | Python | 3.14 | API, extraction, persistence, validation, and operational services |
| Web API | FastAPI | 0.141.1 | HTTP routing, validation, dependency injection, and OpenAPI |
| ASGI server | Uvicorn | 0.52.4 | Runs the FastAPI application |
| Data models | Pydantic | 2.13.5 | Request, response, configuration, and Universal Invoice validation |
| ORM | SQLAlchemy | 2.0.54 | PostgreSQL persistence and queries |
| Database driver | psycopg | 3.3.6 | PostgreSQL connectivity |
| Schema migrations | Alembic | 1.20.0 | Versioned database migrations and parity checks |
| Database | PostgreSQL | 17 in CI | Processing runs, review state, identity, and shadow metadata |
| OCR | EasyOCR | 1.7.2 | Bulgarian and English OCR |
| PDF rendering | Poppler / pdf2image | OS package / 1.17.0 | Converts PDF pages to images for OCR |
| PDF parsing | PyMuPDF | 1.28.2 | PDF document access |
| ML runtime | PyTorch CPU | 2.14.0 | EasyOCR model execution without CUDA |
| Image processing | OpenCV headless | 5.0.0.93 | OCR image preprocessing |
| Browser authentication | MSAL Browser | 5.19.0 | Microsoft Entra sign-in and token acquisition |
| Frontend bundling | esbuild | 0.25.10 | Builds the versioned browser authentication bundle |
| CI browser tests | Playwright | 1.63.0 | Chromium UI regression testing |
| Test framework | pytest | 9.1.1 | Unit, API, integration, security, and contract testing |
| CI JavaScript runtime | Node.js | 22 | Builds and verifies browser assets |
| Container base | python:3.14-slim | Dockerfile | Production Linux runtime |

Versions above are read from `Pipfile.lock`, `package-lock.json`, the Dockerfile, and the CI workflow. System packages such as Poppler follow the selected Linux image repositories unless an explicit package version is pinned in the container definition.

## Component model

### API and application shell

`api.py` constructs the FastAPI application, applies trusted-host, CORS, request logging, rate limiting, and startup validation, registers the routers, serves the static UI, and exposes liveness and readiness endpoints.

Dependencies: application settings, PostgreSQL engine, security middleware, routers, static UI assets, and migration state.

### Upload and OCR boundary

`upload_security.py`, `ocr_engine.py`, and `pdf_engine.py` validate file type and configured resource limits, create temporary processing artifacts, extract embedded text when possible, render PDF pages when required, and run OCR for image-based content.

Sequence:

1. Validate extension, signature, filename, size, page count, image dimensions, and pixel limits.
2. Store only temporary processing data.
3. Extract document input and determine the input format.
4. Extract text directly or render pages and run OCR.
5. Remove temporary data after completion or failure.

Dependencies: Poppler, pdf2image, PyMuPDF, Pillow, OpenCV, EasyOCR, and CPU-only PyTorch.

### Configuration and profile resolution

The configuration services load document-type definitions, common fields, supplier profiles, collection definitions, validation rules, and profile-specific overrides. Profile selection chooses the best supported supplier profile and retains a generic fallback.

Dependencies: configuration store, configuration identity hashing, schema validation, supplier matching, and document configuration resolution.

### Extraction and validation pipeline

`routes_extract.py` coordinates the request lifecycle. `extraction_orchestrator.py` combines LLM-derived values with deterministic rules such as constants, regular expressions, regex lists, nearby-anchor extraction, normalization, collections, and validation.

Sequence:

1. Authenticate and authorize the caller when authentication is enabled.
2. Create a `ProcessingRun` and bind its identifier to request context.
3. Validate and read the uploaded document.
4. Load configuration and resolve the supplier profile.
5. Resolve fields, collections, and summary validations.
6. Extract OCR text and candidate LLM values.
7. Apply deterministic rules and normalization.
8. Extract and validate collections.
9. Validate the final result and calculate quality/review status.
10. Run non-blocking Universal Invoice shadow validation for invoice documents.
11. Persist final values, collections, timings, configuration identity, status, and safe shadow metadata.
12. Return the existing extraction response contract.

### Persistence and processing lifecycle

`database_models.py`, `processing_run_repository.py`, and `processing_run_service.py` implement PostgreSQL persistence. Alembic owns schema evolution.

A processing run tracks the request from start through completion or failure, including processing status, review state, configuration identity, step timings, final values, corrected values, collections, Universal Invoice shadow metadata, and tenant ownership.

Tenant-aware routes apply the principal tenant to reads, review actions, retention, Universal Invoice preview, summaries, and feedback export.

### Universal Invoice capability

The Universal Invoice model is versioned independently from the extraction response. The mapper converts persisted final values and collections into the typed invoice schema without mutating source data.

Flow:

1. Invoice extraction completes using the existing runtime contract.
2. Shadow validation maps the result without blocking successful extraction.
3. Safe status, schema version, and failure reason are persisted.
4. History provides summary, filters, and safe metadata.
5. Authorized users can request a read-only Universal Invoice preview.
6. Reviewed, shadow-valid invoice runs can be exported as deterministic JSONL feedback.
7. Export supports bounded tuple-cursor continuation and secret-safe audit/observability metadata.

### Authentication, authorization, and audit

The API supports API keys and OIDC bearer tokens. Microsoft Entra delegated scopes map through an explicit allowlist. The internal `admin` scope is not granted from browser delegated scopes.

Security dependencies authenticate the principal and enforce operation-specific scopes. Structured security audit events record only allowlisted operational metadata. Raw OCR, document values, filenames, cursor values, tokens, and secrets are excluded from feedback-export audit metadata.

### Container and deployment

The production image runs one non-root Uvicorn process as UID/GID 10001. EasyOCR models are preloaded during image build and runtime downloads are disabled. PostgreSQL is external. Migrations run as a separate release step before API replicas start.

Readiness requires database connectivity and Alembic revision parity. Liveness does not query PostgreSQL.

## Current boundaries and limitations

- Document processing is synchronous.
- The UI is an administrative and expert interface rather than a high-volume ingestion channel.
- The current container model is one Uvicorn process per container.
- Automatic retention scheduling is not enabled.
- HEIF/HEIC is outside the current scope.
- A real scanned-PDF validation fixture remains a lower-priority task.

## Future architecture direction

A future asynchronous model may introduce `202 Accepted`, a job identifier, polling, and optional webhooks for external consumers. This is a planned direction, not part of the current runtime contract. Queue technology, delivery guarantees, retry policy, idempotency, and webhook security are intentionally not specified until concrete integration requirements exist.

## Dependency sequence

The principal runtime dependency chain is:

1. FastAPI receives and validates the HTTP request using Pydantic models.
2. Security dependencies resolve an API-key or OIDC principal and enforce the required scope.
3. Upload security validates the document before OCR or extraction starts.
4. PDF and image services prepare content for EasyOCR and CPU-only PyTorch.
5. Configuration and supplier-profile services resolve the effective extraction contract.
6. The extraction orchestrator combines candidate LLM values with deterministic rules and collection processing.
7. Pydantic and domain validators determine validity, quality, and review requirements.
8. SQLAlchemy and psycopg persist the processing lifecycle in PostgreSQL.
9. Universal Invoice shadow mapping runs independently of the public extraction response.
10. Structured logging, security audit, and request context emit safe operational metadata.

A failure stops dependent downstream steps. Persistence records a safe failed lifecycle where the request has progressed far enough to create a processing run. Universal Invoice shadow failure does not turn an otherwise successful extraction into a failed extraction.

