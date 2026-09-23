# Postman package

## Import

Import `Document_Processing_API_Stable.postman_collection.json` and `Document_Processing_Local.postman_environment.json`, then select `Document Processing Local`.

Populate local file paths only in Postman. Never commit absolute paths, invoices, raw extraction responses, credentials, or personal data.

## Confirmed manually

Health; A1, Electrohold, and Toplofikacia extraction; processing history list/detail and filters; unsupported file 415; unknown document type 404; missing file 422; processing run not found 404; read-only configuration.

## Pending manual fixtures

Generic fallback and corrupted PDF 422 remain defined with empty path variables.
