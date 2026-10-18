> FICTIONAL EXAMPLE - not a real validation record. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are invented to show what an executed package looks like. Model ids are placeholders, not real model names. Signatures are applied by each person in the eQMS and are shown here only as "[signed in eQMS]".

# ACME-VAL-CLAUDE-02 Requirements: Claude Code

| Field | Value |
|---|---|
| Document ID | ACME-VAL-CLAUDE-02 |
| Title | Requirements (control objectives): Claude Code |
| Version | 1.0 (approved 2026-10-19) |
| Owner (role) | Engineering Lead |
| Approver (role) | Head of QA |
| Date | 2026-10-18 |
| Organisation | Acme MedSoft |

> Generated with the AI Coding Tool Validation Kit 0.1.0. Complete every `[fill in]` before review. Approval is given by the approver personally in the eQMS.

## 1. Purpose and scope

This document states the requirements for using Claude Code (Anthropic) in the intended use defined in ACME-VAL-CLAUDE-01. Each requirement states a condition that the code host, the tool configuration, the identities and the records must meet, whichever model produced the output, so that the tool's output cannot reach the product or the QMS without qualified human control.

Every requirement is testable, is traced to the tests in ACME-VAL-CLAUDE-05 and to the risks in ACME-VAL-CLAUDE-03, and applies to every in-scope surface (`local_cli_ide` `pr_review_bot` `ci_headless` ) and to every model in the approved envelope. A requirement marked "Not applicable" keeps its ID so that traceability stays complete; the reason is stated.

## 2. References

- ISO 13485:2016 §4.1.6 (software validation for the intended use), §4.2.4 and §4.2.5 (documents and records), §6.2 (competence), §7.4 (purchasing).
- 21 CFR Part 820 (QMSR), §820.10, incorporating ISO 13485:2016 by reference (§820.7). 21 CFR Part 11 applies to the records of this package that are kept or signed electronically.
- ISO/IEC 27001 (cross-reference for REQ-09, REQ-12, REQ-16): ISO/IEC 27001:2022 Annex A 5.19 to 5.23 (REQ-09, REQ-12), 5.16 to 5.18 (REQ-16); Statement of Applicability ACME-ISMS-SOA rev 4.
- Informative: FDA guidance "Computer Software Assurance for Production and Quality Management System Software" (February 2026); ISO/TR 80002-2:2017.
- Internal: ACME-VAL-CLAUDE-01 Inventory and intended use; ACME-VAL-GEN-01 AI-assisted development work instruction.

## 3. Contexts of use served

- `code_product`: Product code. Code for the regulated product (software in or as a medical device).
- `code_tooling`: Internal tooling. Internal tools, scripts and automation that are not part of the product.
- `pr_review`: Advisory AI PR review. AI review comments on pull requests; advisory only, never counted as the required human approval.
- `doc_drafting`: Document drafting. Drafting of controlled documents and records, previewed and approved by a human before they are written or released.

"all" in the tables below means every selected context.

## 4. Requirements and traceability

| ID | Control objective | Serves | Applies | Verified by |
|---|---|---|---|---|
| REQ-01 | Human approval gate: every change to a protected branch needs at least one approval by a qualified human other than the author and the agent launcher, on the final commit | all | Yes | OQ-01, OQ-02, OQ-05, PQ-01, PQ-02 |
| REQ-02 | AI cannot approve or merge: approvals by AI, bots, apps or CI tokens are not counted; AI identities cannot merge | all | Yes | OQ-04, OQ-05, OQ-40, PQ-01 |
| REQ-03 | Required checks before merge: tests, SAST, secret scanning, dependency / SOUP gate; violations are blocked | all | Yes | OQ-07 |
| REQ-04 | No direct push and no silent bypass: direct pushes blocked; admin bypass prevented, or logged and reviewed | all | Yes | OQ-03, OQ-06, PQ-01 |
| REQ-05 | Attributability: every change traceable to a named human; agent activity distinguishable from human activity | all | Yes | IQ-02, IQ-04, OQ-01 |
| REQ-06 | Configuration under control: baseline of managed settings, permission mode, deny rules, sandbox, hooks, MCP allow-list, instruction files; users cannot override managed settings | all | Yes | IQ-01, IQ-03, OQ-09 |
| REQ-07 | Local guardrails behave as configured: denied commands, writes outside the workspace, network restrictions | all | Yes (local CLI / IDE in scope) | OQ-08, OQ-40 |
| REQ-08 | Model envelope: only approved models (enforced where the tool allows), model recorded per PR / session, new models admitted via MA-01 | all | Yes | OQ-10, MA-01, PQ-01 |
| REQ-09 | Data handling: no secrets, PHI or personal data in prompts / repositories beyond what is contractually covered; vendor retention and training terms as contracted (supplier requirement, ISO 13485 §7.4) | all | Yes | IQ-05, OQ-07 |
| REQ-10 | Provenance labelling: AI-assisted changes are declared (commit trailer and / or PR template) | all | Yes | OQ-11 |
| REQ-11 | Reversibility: AI-assisted changes can be reverted with full traceability | all | Yes | OQ-12 |
| REQ-12 | Vendor change monitoring: releases, deprecations, model changes and terms are monitored and trigger the defined tests | all | Yes | OQ-13 |
| REQ-13 | Source citation and human preview before any AI-assisted write to a controlled record | `doc_drafting` | Yes | OQ-20, MA-01 (citation probes, per model) |
| REQ-14 | Bounded write scope and oracle-based verification of agent outputs | `agents_qms` | Not applicable: context `agents_qms` not selected | - |
| REQ-15 | AI review is advisory only: never a required approval or the only verification | `pr_review` | Yes (advisory AI PR review selected) | OQ-04 |
| REQ-16 | Organisation-owned accounts / workspace with SSO; no personal accounts for QMS use | all | Yes | IQ-02 |
| REQ-17 | Competence: users trained on the work instruction (ACME-VAL-GEN-01) before use (ISO 13485 §6.2) | all | Yes | IQ-02 (seat list reconciled with training records); approvers in the OQ-01 and PQ-01 samples checked against training records; result recorded in ACME-VAL-CLAUDE-07 |

Risk traceability (risk to requirement to test) is in ACME-VAL-CLAUDE-03, section 4.

## 5. Requirement details

Each requirement lists the objective, the acceptance criteria used by the tests (fixed in ACME-VAL-CLAUDE-05 before execution), and implementation notes. Implementation notes describe known ways to meet the objective; they are not the acceptance criteria, and settings must be confirmed against the vendor's current documentation at IQ.

### REQ-01 Human approval gate

- **Objective:** every change to a protected branch of an in-scope repository requires at least 1 approval by a qualified human who is neither the author nor the person who launched the agent, given on the final commit.
- **Acceptance:** the platform rule requires the approvals; approvals become stale on a new push; 100% of sampled merged AI-assisted PRs had a qualified human approval submitted before merge on the head commit; merge without approval is refused (negative test); PRs authored by a bot or agent identity need 2 approvals or code-owner approval by a human team (compensating control, because the platform counts the launcher's approval of such a PR).
- **Qualified reviewer:** trained on ACME-VAL-GEN-01 and authorised by ACME-QP-12 Code review and merge, Annex A (qualified-reviewer list).
- **GitHub:** classic branch protection `required_approving_review_count` of 1 or more, `dismiss_stale_reviews`, `require_last_push_approval` (the most recent push must be approved by someone other than the pusher; enable stale-review dismissal as well), `require_code_owner_reviews` for protected paths; or a ruleset `pull_request` rule with `required_approving_review_count`, `dismiss_stale_reviews_on_push`, `require_last_push_approval` and `require_code_owner_review`. Only approvals from reviewers with write permission count.

### REQ-02 AI cannot approve or merge

- **Objective:** approvals submitted by the AI tool, bots, apps or CI tokens are not counted toward the required approval, and no AI identity can merge.
- **Acceptance:** negative tests show that an approval from each AI / bot / CI identity in scope does not satisfy the merge requirement and that a merge attempt by an AI identity is refused; settings that let AI approvals count are off and recorded in ACME-VAL-CLAUDE-06.
- **GitHub:** Actions workflow permission `can_approve_pull_request_reviews` false at organisation and repository level ("Allow GitHub Actions to create and approve pull requests" off). GitHub documentation does not say whether approvals by a GitHub App count; prove it with OQ-04. If Copilot code review is enabled anywhere in the organisation, keep "Allow Copilot approvals to count toward merge requirements" off and the enterprise policy "Allow Copilot to approve pull requests" at "Disabled everywhere".
- **Claude Code:** the Claude Code GitHub Action documents that it cannot approve pull requests, submit formal reviews or merge. This is behaviour of the action, not a platform boundary (its GitHub App holds pull-request write permission), so the platform settings above remain the control. The managed Code Review service never approves or blocks a PR; its check run concludes neutral.

### REQ-03 Required checks before merge

- **Objective:** the required checks `ci / unit-tests`, `ci / sast`, `soup-gate` and `pr-template-check` (plus secret scanning push protection) run on every PR to a protected branch and block merge on failure.
- **Acceptance:** canary PRs containing a failing test, an unapproved dependency and a test secret are each blocked (OQ-07); required checks are bound to the expected source so that a status set by another identity does not satisfy them.
- **Dependency / SOUP gate:** new or changed dependencies are checked against the SOUP register maintained under ACME-QP-13 SOUP and dependency management, by the required check `soup-gate` (built from `checks/soup_gate.py`; the approved list is exported from the register); this also catches hallucinated package names.
- **GitHub:** any person or integration with write access can set a commit status, so bind required checks to the expected app (classic `checks[].app_id`; rulesets `required_status_checks[].integration_id`). A required check passes when it is successful, skipped or neutral, so an AI review check that concludes neutral is not a gate. Enable secret scanning push protection (`security_and_analysis.secret_scanning_push_protection`).

### REQ-04 No direct push and no silent bypass

- **Objective:** nobody, including administrators and AI identities, can push directly to a protected branch; any bypass of the rules is either impossible or logged and reviewed.
- **Acceptance:** direct push refused (OQ-03); admin bypass refused, or the bypass appears in the audit records and is reviewed (OQ-06); no bypass in the PQ-01 period without a review record.
- **GitHub:** classic `enforce_admins` true ("Do not allow bypassing the above settings"), or rulesets with reviewed `bypass_actors`. Do not use `bypass_mode` "exempt" on QMS branches: exempt actors are not evaluated and no bypass audit entry is created. The organisation audit log shows 180 days and Git events only 7 days; export or stream it, and export ruleset and rule-suite (bypass) records periodically.

### REQ-05 Attributability

- **Objective:** every change and every write is traceable to a named human (requester or author, and approver); activity of the AI agent is distinguishable from human activity.
- **Acceptance:** the surface to identity mapping (IQ-04) shows no shared or anonymous identities; account ownership and SSO are confirmed (IQ-02); in the OQ-01 sample every PR shows a named human requester and approver, and AI involvement is identifiable.
- **Note:** give agents a dedicated identity, or a mandatory label (REQ-10) that the reviewer checks.
- **Claude Code:** in telemetry `user.id` is an anonymous identifier, not a person; user identity attributes (such as `user.email`) are present only with a claude.ai or Team / Enterprise login. For API-key fleets add an identity attribute through `OTEL_RESOURCE_ATTRIBUTES`.

### REQ-06 Configuration under control

- **Objective:** the tool configuration that governs behaviour (managed or admin settings, permission mode, allow / deny rules, sandbox, hooks, MCP or extension allow-list, instruction files) is baselined with hashes, changed only through change control, and cannot be overridden by users.
- **Acceptance:** baseline captured and hashed (`python3 checks/capture_baseline.py`, IQ-03) and recorded in ACME-VAL-CLAUDE-06; version recorded per surface (IQ-01); a user-level attempt to override a managed setting has no effect (OQ-09); instruction and configuration files in repositories require code-owner review.
- **Claude Code:** managed settings (system `managed-settings.json`, MDM, or server-managed from the admin console) take precedence over `--settings`, `.claude/settings.local.json`, `.claude/settings.json` and `~/.claude/settings.json`. Candidate locks: `permissions.disableBypassPermissionsMode` = `"disable"`; `disableAutoMode` = `"disable"` or an explicit managed `permissions.defaultMode`; `allowManagedPermissionRulesOnly`; `allowManagedHooksOnly` (CI and agent runners) or, on developer machines, `pluginConfigs` `cc-plugin-sec-default@builtin` option `allowManagedModsOnly` with `disableSideloadFlags`; `allowManagedMcpServersOnly`; `availableModels` with `availableModelsMatch` = `"exact"` and `enforceAvailableModels`. `CLAUDE.md` is guidance, not enforcement. Verify the effective sources with `/status` ("Setting sources") and `claude doctor`. Server-managed settings are a client-side control, not a security boundary; endpoint-managed settings give stronger guarantees.

### REQ-07 Local guardrails behave as configured

Applies: the local CLI / IDE surface is in scope.

- **Objective:** denied commands are not executed, writes outside the workspace are refused, network access is limited to approved destinations, and guardrails fail closed (an unavailable sandbox or a failing policy hook blocks rather than allows).
- **Acceptance:** OQ-08 negative cases (denied command, write outside workspace, non-approved network destination) are all refused; the failure-mode case blocks; OQ-40 shows that instructions planted in untrusted content do not lead to a denied action.
- **Claude Code:** Bash deny rules match the command text and are not a security boundary (for example `Bash(curl *)` does not stop `/usr/bin/curl`); use the OS sandbox with `sandbox.enabled`, `sandbox.failIfUnavailable` and `sandbox.allowUnsandboxedCommands` = false (the sandbox is not available on native Windows; built-in file tools, hooks and MCP servers run outside it). Hooks fail open on errors and timeouts unless the hook sets `"onFailure": "block"`. In CI always pass `--permission-mode` explicitly.

### REQ-08 Model envelope

- **Objective:** only models in the approved envelope are used; the model is restricted where the tool can enforce it, otherwise recorded and monitored; the model used is recorded per PR or session; a new model or model version is used only after MA-01 passes.
- **Approved envelope:** `anthropic-model-a` `anthropic-model-b` 
- **Policy:** envelope. Any model in the envelope may be used once admitted by MA-01.
- **Acceptance:** OQ-10: selecting a model outside the envelope is refused where the tool can enforce it, and detected in the records where it cannot; the enforced allow-list equals the admitted ids in ACME-VAL-CLAUDE-06 section 12; the model used is recorded for 100% of sampled PRs / sessions; an MA-01 pass record exists for every model in use; PQ-01: every model observed during the period is inside the envelope.
- **Note:** envelope entries and the pre-authorised patterns of ACME-VAL-CLAUDE-04 section 5.2 are glob patterns used by the kit's records and checks. The vendor's own allow-list syntax may differ (for example prefix matching); the enforced allow-list holds admitted exact ids only, and the translation is recorded in ACME-VAL-CLAUDE-06.
- **Claude Code:** managed `availableModels` restricts selection (`/model`, `--model`, the `model` key); with the default prefix matching an entry also permits later versions, so list admitted exact ids with the managed-only `availableModelsMatch` = `"exact"` and `deniedModels` for known unadmitted ids; set `enforceAvailableModels` true so the Default option resolves inside the list. A managed `model` is only a starting default. Automatic fallbacks (overload, content-based) can change the model during a session; their targets are checked against `availableModels`.

### REQ-09 Data handling

- **Objective:** prompts, context and repositories reachable by the tool contain no secrets, health data or personal data beyond what the contract and the data protection assessment cover; vendor retention, training use and region are as contracted.
- **Acceptance:** vendor terms recorded and matched to the contract (IQ-05); the secret canary in OQ-07 is blocked; local transcript retention is set as decided in ACME-VAL-CLAUDE-06.
- **Supplier requirement:** the vendor is evaluated and monitored under ISO 13485 §7.4: ACME-VEN-2026-011 (Anthropic).
- **Claude Code:** local transcripts are plaintext JSONL under `~/.claude/projects/`, deleted after `cleanupPeriodDays` (default 30); pin the value in managed settings according to the retention decision.

### REQ-10 Provenance labelling

- **Objective:** every AI-assisted change is declared using the labels defined in ACME-VAL-GEN-01 (commit trailer and / or PR template field; the model used is recorded once per PR or from telemetry).
- **Acceptance:** OQ-11: 100% of sampled AI-assisted PRs carry the label; the required check `pr-template-check` rejects PRs whose AI-assistance question is left unanswered.
- **Claude Code:** the default commit trailer is `Co-Authored-By: <model name> <noreply@anthropic.com>`; the `attribution` setting customises commit and PR text. Attribution is an instruction to the model, not a git hook, so it is not proof that every AI-assisted commit is labelled.

### REQ-11 Reversibility

- **Objective:** any AI-assisted change can be reverted through the normal reviewed process, and the history keeps the original change, its approval and the revert.
- **Acceptance:** OQ-12: a merged AI-assisted change in a test repository is reverted through a reviewed PR; original commit, approval and revert are linked; force-push and history rewrite on protected branches are refused.

### REQ-12 Vendor change monitoring

- **Objective:** releases, deprecations, model changes, policy defaults and terms of Anthropic are monitored at least weekly (one entry in every calendar week, at most 7 days between entries); each relevant change gets an impact assessment and triggers the tests defined in ACME-VAL-CLAUDE-04 and ACME-VAL-CLAUDE-08 before rollout.
- **Acceptance:** OQ-13: the monitoring log has no gap longer than the defined frequency over the period fixed in ACME-VAL-CLAUDE-04; every guardrail-relevant release has an impact assessment dated before rollout; every model in use has an MA-01 record dated before its first QMS-relevant use (retrospective validation: exceptions listed and covered by the interim-use nonconformity). Sources to watch are listed in ACME-VAL-CLAUDE-08.

### REQ-13 Source citation and preview before write

- **Objective:** in AI-assisted drafting, every factual claim cites a source the reviewer can check; before any write to a controlled document or record, the human previews the exact content to be written and decides; the write is attributed to that human; the AI does not release documents.
- **Acceptance:** OQ-20: source-citation probes during normal drafting work; a statement without a supporting source fails; for sampled writes, a preview record precedes the write and the write is attributed to the human who approved the preview.

### REQ-14 Bounded write scope and oracle-based verification

Not applicable: the `agents_qms` context is not selected. Selecting it later is a new context of use (re-baseline trigger).

### REQ-15 AI review is advisory only

- **Objective:** AI review comments and checks are advisory: never a required approval, never counted as verification evidence on their own, and never the only review of a change.
- **Acceptance:** OQ-04 shows that the AI review does not satisfy the approval requirement; the required-check list in ACME-VAL-CLAUDE-06 contains no AI review check, or only one that fails closed and is additional to human review.
- **Claude Code:** the Code Review check run concludes neutral or skipped, never failure, so it cannot act as a gate unless your own CI parses its result.

### REQ-16 Organisation-owned accounts and SSO

- **Objective:** the tool is used only through organisation-owned accounts or workspaces with single sign-on; personal accounts, and accounts belonging to other organisations, are not used for QMS-relevant work.
- **Acceptance:** IQ-02: seat or member list reconciled with the identity provider; a login with a personal or foreign account is refused where the tool can enforce it, and otherwise detected by the reconciliation.
- **Claude Code:** managed `forceLoginMethod` and `forceLoginOrgUUID`. `claude setup-token` and `/install-github-app` enforce only `forceLoginMethod`, so tokens for CI are reviewed separately.

### REQ-17 Competence

- **Objective:** every user of the tool and every reviewer who approves AI-assisted changes is trained on ACME-VAL-GEN-01 before access or first approval, with records.
- **Acceptance:** 100% of the users with access and of the approvers in the OQ-01 and PQ-01 samples have a training record dated before their access or first approval; result recorded in ACME-VAL-CLAUDE-07.

## 6. Approval

Reviewed and approved in the eQMS by the Head of QA (Sam Sample, 2026-10-19, [signed in eQMS]). Author: Jordan Demo (Engineering Lead); reviewed by Alex Example (Validation Engineer). AI assistance in drafting: no.

## Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-18 | Jordan Demo | Initial draft generated with the kit (0.1.0) |
| 1.0 | 2026-10-19 | Jordan Demo | Completed and approved for the validation |
