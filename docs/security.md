# Security plan

## Phase 1: upload and resource protection

The extraction boundary enforces configured limits for upload size, filename length, PDF page count, image dimensions, and image pixel count. Supported file extensions are allowlisted and checked against file signatures. Temporary files are removed after processing or validation failure.

## Planned phases

- Authentication and object/function-level authorization
- Rate limiting, concurrency limits, and request timeouts
- Trusted hosts, explicit CORS, proxy trust, and production documentation exposure
- Retention, privacy, audit trail, backup protection, and deletion workflows
- Dependency scanning and security regression automation

## Network and API hardening

Production uses an explicit host allowlist, disables public OpenAPI and interactive documentation, and leaves CORS disabled by default. Cross-origin browser access is enabled only through explicit origins. Forwarded headers are trusted only from deployment-configured proxy addresses.
