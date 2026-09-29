# Supply chain security

## Purpose

The supply-chain workflow inventories repository dependencies and checks locked Python and npm dependencies for published vulnerabilities. It runs independently from the main test workflow so ordinary application tests and security findings remain distinguishable.

## Workflow triggers

The workflow runs:

- after a push to `main`;
- for pull requests targeting `main`;
- every Monday at 03:17 UTC;
- when started manually from GitHub Actions.

The scheduled run checks the unchanged lockfiles against newly published advisories. A passing historical run does not guarantee that the same dependency set remains free of later advisories.

## Python audit

The workflow exports exact runtime and development versions from `Pipfile.lock` through `pipenv requirements --dev`. `pip-audit` 2.10.1 checks that generated requirements set for known vulnerabilities.

The Python audit fails on reported vulnerabilities. Findings are not ignored automatically. A temporary exception requires a documented vulnerability identifier, affected component, exposure analysis, compensating controls, owner, and expiration date before an explicit ignore can be considered.

## npm audit

`npm audit --package-lock-only --audit-level=high` evaluates the committed `package-lock.json`. The job fails for high or critical findings. Moderate and low findings remain visible in the audit output and should be reviewed during dependency maintenance.

The workflow does not run `npm audit fix` and does not modify the lockfile.

## Pull request dependency review

Pull requests run GitHub dependency review with a high-severity failure threshold. The review evaluates dependency changes introduced by the pull request and reports patched versions when available.

Dependency review complements the full lockfile audits. It does not replace the scheduled Python and npm scans.

## SPDX SBOM

Non-pull-request runs generate an SPDX JSON SBOM from the checked-out repository by using Anchore's SBOM action and Syft. The workflow uploads `document-processing-sbom.spdx.json` as a workflow artifact.

The SBOM is an inventory artifact, not proof that every listed component is safe or correctly licensed. Keep the SBOM associated with the commit and CI run that produced it.

## Action version policy

Third-party security actions use explicit release versions rather than floating major aliases:

- `actions/dependency-review-action@v5.0.0`;
- `anchore/sbom-action@v0.24.2`;
- `pip-audit==2.10.1`.

Review version updates as dependency changes. Do not silently replace audit failures with `continue-on-error`.

## Finding response

1. Confirm the affected package and dependency path.
2. Determine whether the package is present in the production runtime, development tooling, or both.
3. Prefer an upgrade that preserves the locked and tested dependency graph.
4. Run the complete application test suite and container checks after changing dependencies.
5. Record an exception only when no safe upgrade is available and the actual exposure is understood.
6. Remove expired exceptions and re-evaluate them during every dependency update.

Deprecation warnings without a vulnerability advisory are tracked as compatibility work. They are not vulnerability-audit exceptions and must not be hidden merely to make logs quiet.
