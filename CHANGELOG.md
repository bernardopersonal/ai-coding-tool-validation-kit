# Changelog

All notable changes to this kit are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

For organisations that have validated a tool with the kit: a new kit version is not automatically a change to your validation. A change to `admission/tasks/` or to the acceptance criteria is a change to the admission suite, so assess it under your change control before you use it for model admissions.

## Unreleased

Changes from the regulatory, practitioner and de-identification review of 0.1.0. Organisations that validated with 0.1.0: the admission suite changed (task `guardrail-denied-command` version 2, runner flags), so treat the new suite version as a plan change.

### Added

- Shared record `00-shared/code-host-gate-qualification.md` (`doc_id_gates`): the code-host gates (OQ-01 to OQ-07, OQ-12) are qualified once per code host for all tools, with per-step records, an evidence index under `evidence/GEN/` and the results credited to each tool.
- `checks/soup_gate.py` (required CI check against unapproved or non-existent dependencies, OQ-07 b) with `examples/github-workflow-soup-gate.yml` and `examples/github/approved-components.example.json`.
- `checks/mirror_protection.py`: copies branch protection, rulesets and the Actions approval setting to a sandbox repository and compares them.
- `checks/client_regression.py` with probe examples in `tools/claude-code/` and `tools/codex/`: automated client regression (CS-3a) as the gate for batched version raises and a security-fix fast path (T7a).
- OQ-13 (vendor change monitoring), RV-01 (retrospective review of use before validation, separate from PQ), a PQ-02 severity table, PQ-01 outlier rule, and an "approved with conditions" path until the PQ addendum.
- `examples/github/pull_request_template.md`, `examples/github/CODEOWNERS.example`, `examples/github-workflow-label-check.yml`.

### Changed

- Every evidence script records who ran it (`--operator` or `$KIT_OPERATOR`, operating-system user, host, SHA-256 of the machine id, and the GitHub login where relevant).
- Validation plan: objective pre-authorised scope for Tier 2 changes with an enforced allow-list of admitted exact model ids, time-boxed admission after detection for tools without an enforced allow-list, re-test validity rules, MA-01 run-count rationale, isolation and denied-command control per tool, interim use with a mandatory nonconformity and CAPA reference, Day 0 preparation before the execution week.
- Validated versions are the versions actually tested; the Claude Code example pins `requiredMinimumVersion` and `requiredMaximumVersion` to the tested version.
- `check_github_gates.py`: required checks verified on merged PRs (check runs and statuses), retention setting recorded and expired results reported as inconclusive, launcher of agent-authored PRs excluded from qualifying approvals with a compensating control.
- `run_canary.sh`: server-side merge attempt through the REST API with HTTP status, admin and merge-queue detection, preconditions for OQ-07 variants, result `pass` / `fail` / `inconclusive`.
- `capture_baseline.py`: Claude Code managed sources evaluated in the client's own order and merge behaviour, findings name their source, graded `--compare` with `--approved-version`.
- `run_admission.py`: isolation from the executor's user configuration, denied-command control (`--deny-control`, N/A with a reason where no control exists), check of the model actually used (`--aux-model`, `--model-log`), baseline variants.
- Claude Code example: secrets denied, gate files asked instead of denied, mods restricted with `allowManagedModsOnly` and `disableSideloadFlags` (`allowManagedHooksOnly` recommended for runners), realistic domain list, exact model matching, static attribution. Codex examples: `inherit = "all"` with explicit filters, `cli_auth_credentials_store = "auto"`, MCP allowlist shipped commented out.
- 21 CFR Part 11 and ISO 13485 §6.2 c) mapped where they apply; audit-finding lists reworded as design rules of the kit.
- Defaults use obviously fictional placeholders (organisation "Acme MedSoft", model envelope `anthropic-model-*` / `openai-model-*`); the de-identification deny-list moved out of the repository.

## 0.1.0 - 2026-10-18

First public release.

### Added

- `kit.py` CLI (`init`, `render`, `example-config`, `vars`) with an interactive wizard, a strict mustache-like template engine (standard library only) and optional `.docx` output through pandoc.
- Document templates: a shared work instruction and tool-discovery checklist, and per tool the inventory and intended use, requirements REQ-01 to REQ-17, risk assessment, validation plan with the three-tier model change protocol, test protocol (IQ-01 to IQ-05, OQ-01 to OQ-12, OQ-20, OQ-30, OQ-40, MA-01, PQ-01, PQ-02), configuration baseline, validation report and change and revalidation.
- Options for risk model (CSA or three-level), contexts of use, surfaces, code host, model policy (envelope or pinned), GxP, and retrospective validation when the tool is already in use.
- Evidence scripts in `checks/`: GitHub gate check, configuration baseline capture, AI footprint scan, canary PR.
- Model admission suite in `admission/`: runner, vendor-neutral JSON tasks and fixtures.
- Tool notes and verified configuration examples for Claude Code (`tools/claude-code/`) and OpenAI Codex (`tools/codex/`).
- Documentation: `GUIDE.md`, `docs/regulatory-mapping.md`, `docs/model-change-protocol.md`, `docs/adapting-other-tools.md`.
- Fictional filled example (`examples/acme-medsoft/`) and a workflow example for exporting review evidence.
- Unit tests and GitHub Actions CI.

Vendor facts verified on 2026-10-18 (Claude Code v2.1.302, Codex CLI 0.163.0).
