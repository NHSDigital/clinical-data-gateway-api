# CI/CD Workflows and Composite Actions Overview

This document summarizes the GitHub Actions workflows and reusable stages provided by the [repository template](https://github.com/NHSDigital/repository-template).

## Responsibility Split

Layer | Responsibility
----- | -------------
PR Workflow | Orchestrates commit, test, build, acceptance for validation
Publish Workflow | Release management on merge to main
Deploy Workflow | Manual promotion of a selected tag
Stage Workflows | Reusable quality gates (can be invoked by other orchestrators)
Composite Actions | Encapsulate repeatable checks & reports

---

## 1. Pull Request Validation Workflow

File: [workflows/cicd-1-pull-request.yaml](workflows/cicd-1-pull-request.yaml)
Trigger: `pull_request` (opened, reopened).
Purpose: Full PR quality gate (~≤20 min target).
Job sequence:

1. metadata – gathers timestamps, tool versions, semantic version.
2. commit-stage – calls reusable workflow [stage-1-commit.yaml](workflows/stage-1-commit.yaml).
3. test-stage – calls [stage-2-test.yaml](workflows/stage-2-test.yaml).
4. build-stage – calls [stage-3-build.yaml](workflows/stage-3-build.yaml).
5. acceptance-stage – calls [stage-4-acceptance.yaml](workflows/stage-4-acceptance.yaml).

Outcome: Fast feedback on security, formatting, unit tests, build readiness, and higher‑level tests before merge.

---

## 2. Publish Workflow (Release on Merge)

File: [workflows/cicd-2-publish.yaml](workflows/cicd-2-publish.yaml)
Trigger: `pull_request` closed on default branch where `merged == true`.
Purpose: Convert merged main commit into a release artefact and send optional notification.
Jobs:

- metadata – reconstructs build/version context.
- publish – placeholder for artefact retrieval (future), creates release/tag.
- success – optional Microsoft Teams notification (webhook secret gated).

---

## 3. Deploy Workflow (Manual Promotion)

File: [workflows/cicd-3-deploy.yaml](workflows/cicd-3-deploy.yaml)
Trigger: `workflow_dispatch` (input: tag; default latest).
Purpose: Manually deploy a chosen tag to an environment.
Jobs:

- metadata – captures tag + version details.
- deploy – placeholder deployment steps (extend with real infra logic).

---

## Workflow Stages

### 1. Reusable Commit Stage

File: [workflows/stage-1-commit.yaml](workflows/stage-1-commit.yaml) (invoked via `workflow_call`)
Parallel short-running jobs:

<!-- vale off -->
- scan-secrets – [actions/scan-secrets](actions/scan-secrets/action.yaml)
- check-file-format – [actions/check-file-format](actions/check-file-format/action.yaml)
- check-markdown-format – [actions/check-markdown-format](actions/check-markdown-format/action.yaml)
- check-english-usage – [actions/check-english-usage](actions/check-english-usage/action.yaml)
- lint-terraform – [actions/lint-terraform](actions/lint-terraform/action.yaml)
- count-lines-of-code – [actions/create-lines-of-code-report](actions/create-lines-of-code-report/action.yaml)
- scan-dependencies – [actions/scan-dependencies](actions/scan-dependencies/action.yaml)
Purpose: Early fail-fast quality, security, formatting, and reporting gates.
<!-- vale on -->

---

### 2. Reusable Test Stage

File: [workflows/stage-2-test.yaml](workflows/stage-2-test.yaml)
Jobs:

- test-unit – `make test-unit`
- test-lint – `make test-lint`
- test-coverage – depends on unit; `make test-coverage`

Purpose: Validate correctness, style, and coverage.

---

### 3. Reusable Build Stage

File: [workflows/stage-3-build.yaml](workflows/stage-3-build.yaml)
Jobs:

- artefact-1 – placeholder for build + artefact upload.
- artefact-2 – second placeholder pattern.

Purpose: Scaffold for producing distributable artefacts.

---

### 4. Reusable Acceptance Stage

File: [workflows/stage-4-acceptance.yaml](workflows/stage-4-acceptance.yaml)
Flow:

1. environment-set-up – provision infra / DB / deploy app (placeholders).
2. Parallel test jobs (all depend on setup):
   - test-security (`make test-security`)
   - test-ui (`make test-ui`)
   - test-ui-performance (`make test-ui-performance`)
   - test-integration (`make test-integration`)
   - test-load (`make test-load`)
3. environment-tear-down – runs with `if: always()` after tests.

Purpose: Broad functional and non-functional validation in an ephemeral environment.

---

## Composite Actions Summary

<!-- vale off -->
Action | Path | Purpose | Key Script(s)
------ | ---- | ------- | -------------
Scan secrets | [actions/scan-secrets](actions/scan-secrets/action.yaml) | Detect committed secrets | Internal script (history scan)
Check file format | [actions/check-file-format](actions/check-file-format/action.yaml) | Enforce formatting conventions | `scripts/githooks/check-file-format.sh`
Check Markdown format | [actions/check-markdown-format](actions/check-markdown-format/action.yaml) | Markdown style/structure | `scripts/githooks/check-markdown-format.sh`
Check English usage | [actions/check-english-usage](actions/check-english-usage/action.yaml) | Natural language lint (e.g. Vale) | `scripts/githooks/check-english-usage.sh` (implied)
Lint Terraform | [actions/lint-terraform](actions/lint-terraform/action.yaml) | `Terraform fmt` + validate + custom checks | `scripts/githooks/check-terraform-format.sh`
Create LOC report | [actions/create-lines-of-code-report](actions/create-lines-of-code-report/action.yaml) | Generate & archive lines-of-code metrics | `scripts/reports/create-lines-of-code-report.sh`
Scan dependencies | [actions/scan-dependencies](actions/scan-dependencies/action.yaml) | SBOM + vulnerability report | `scripts/reports/create-sbom-report.sh` (+ vulnerability script)
<!-- vale on -->

---

## Make Targets (Referenced by Workflows)

Primary targets invoked:

- Test stage & acceptance tests: see `scripts/tests/test.mk` for `test-*` targets.
- Local workflow emulation: `runner-act` in `scripts/init.mk` (uses `act`).

---
