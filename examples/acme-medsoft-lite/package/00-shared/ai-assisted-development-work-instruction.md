> FICTIONAL EXAMPLE, invented for illustration only. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are made up to show what an executed lite package looks like. Model ids are placeholders. Each person signs in the eQMS, shown here only as "[signed in eQMS]".

# ACME-VAL-GEN-L01 AI-assisted development work instruction

| Field | Value |
|---|---|
| Document ID | ACME-VAL-GEN-L01 (lite profile) |
| Version | 1.1 (approved 2026-10-23) |
| Owner / approver (roles) | Engineering Lead / Head of QA |
| Date | 2026-10-19 |
| Organisation | Acme MedSoft |

> Generated with the AI Coding Tool Validation Kit 0.2.0, lite profile. Complete every `[fill in]` before review. The approver approves personally in the eQMS.

## 1. Scope

Applies to everyone at Acme MedSoft who uses an AI coding tool, or reviews work produced with one, on any surface and in any context below. Using these tools is encouraged; these rules make sure every change still reaches the product and the QMS only through qualified human control.

References: ISO 13485:2016 clauses 4.1.6 and 6.2; 21 CFR Part 820 (QMSR, incorporating ISO 13485); EU AI Act Article 4 (AI literacy) where applicable; ACME-VAL-GEN-L02 Tool discovery checklist; ACME-QP-12 Code review and merge; ACME-QP-15 SOUP and dependency management; ACME-QP-09 Deviations and nonconformities.

## 2. Approved tools and contexts

| Tool | Surfaces | Model policy and approved models | Validation | Status |
|---|---|---|---|---|
| Claude Code (Anthropic) | `local_cli_ide` `pr_review_bot`  | envelope: `anthropic-model-a` `anthropic-model-b`  | ACME-VAL-CLAUDE-L01 to ACME-VAL-CLAUDE-L03 | Released with conditions 2026-10-23 (ACME-VAL-CLAUDE-L03); PQ-01 and PQ-02 addendum due 2026-11-27 |
| OpenAI Codex (OpenAI) | `local_cli_ide`  | envelope: `openai-model-a`  | ACME-VAL-CODEX-L01 to ACME-VAL-CODEX-L03 | Released with conditions 2026-10-23 (ACME-VAL-CODEX-L03), local CLI only; PQ-01 and PQ-02 addendum due 2026-11-27 |

Approved contexts: Product code (`code_product`); Internal tooling (`code_tooling`); Advisory AI PR review (`pr_review`); nothing else. Any other purpose needs validation first: ask the Engineering Lead.

## 3. Rules

1. **No shadow AI:** use only the declared, organisation-approved tools of section 2, with organisation accounts; never use an AI tool on a personal account for Acme MedSoft development or QMS work. Label every AI-assisted change (section 4). Report any AI tool, extension, bot or agent you find outside section 2 (section 6): it needs registration and validation first. AI use the organisation does not know about cannot be validated, controlled or defended in an audit.
2. **Accounts:** only the organisation account or workspace, through single sign-on. No foreign or shared accounts or tokens. Agent and CI tokens are issued and recorded by the tool owner.
3. **Data:** never put secrets, patient or health data or personal data into prompts, context or instruction files, or repositories the tool can read, unless the contract and the data protection impact assessment DPIA-2026-03 cover it. Use synthetic data for tests.
4. **Untrusted content:** issues, PR comments, web pages and MCP results can carry instructions aimed at the agent (prompt injection). Do not combine such content with write access to protected systems.
5. **You own every line you merge.** As author: keep changes reviewable; read and understand every changed line; never let the AI delete tests, weaken assertions or change expected values to make CI pass; check that every new dependency exists and is approved (AI tools invent package names).
6. **As reviewer:** review the diff itself (the AI's summary is a hint); approve only what you understood; check tests, dependencies, secrets and changes to CI, gate, tool configuration or instruction files (these need code-owner review). AI review comments are hints, and their absence proves nothing.
7. **Separation of duties:** never approve your own PR or a PR whose agent you launched. Where the agent opens PRs under its own identity, the code host counts your approval, so this rule is yours to keep; such PRs need 2 approvals or code-owner approval.
8. **Models:** only models from the approved list, and a newly released model only after its admission record (MA-01) exists. Report unexpected model switches to the tool owner.
9. **Configuration:** managed or admin configuration changes only by the Engineering Lead, through change control. Instruction files guide the AI; they do not enforce anything.
10. **Prohibited:** letting the AI approve, merge, sign, close or release anything; recording an approval for someone else; merging without approvals, pushing directly to a protected branch or bypassing gates outside the emergency change route of ACME-QP-12 section 9; permission-bypass or unsandboxed modes; MCP servers, plugins or extensions not on the allow-list; agent write access to QMS systems outside the code-host gate (for example through MCP) unless validated for it; asking the AI to execute, conclude or approve the validation of an AI tool.
    - Claude Code: never use `--dangerously-skip-permissions` or the `bypassPermissions` mode; do not change files in the managed settings location.
    - OpenAI Codex: never use `--dangerously-bypass-approvals-and-sandbox` or the `danger-full-access` sandbox mode; do not change the admin `requirements.toml`.

## 4. Provenance label

Declare every AI-assisted change with commit trailers (some tools add a trailer for you) and record the model id once per PR in the PR template (`examples/github/pull_request_template.md` in the kit):

```
AI-Assisted: yes
AI-Tool: <tool name>
```

- Claude Code: the default trailer `Co-Authored-By: <model name> <noreply@anthropic.com>` names the model; keep it or set the managed `attribution` setting. It works as an instruction to the model, so still check the label. Acme MedSoft sets the managed `attribution` to the two trailers above and records the model id in the PR template.
- OpenAI Codex: no built-in commit attribution setting is documented; add the trailers yourself or through the PR template.

## 5. Context rules

- **Product code:** changes reach protected branches only through an approved PR with green required checks; give extra scrutiny to the items classified safety-related or security-sensitive in the software development plan (for example alarm-threshold logic and input validation), which also need the second senior review.
- **Internal tooling:** same review rules; tooling that produces QMS records or verification results is validated before its output is used as evidence.
- **AI PR review:** advisory only; never the required approval and never the only review.

## 6. Report without delay

To the deviation form in the eQMS (ACME-QP-09), or directly to the Head of QA: a defective AI-assisted change that passed review; a guardrail that did not behave as expected; a model outside the approved list or an unexpected switch; an AI tool, bot or agent not listed in section 2; suspected leakage of secrets, health data or personal data; an attempted prompt injection.

## 7. Training

Users and reviewers are trained on this work instruction before access or their first approval of an AI-assisted change (ISO 13485:2016 clause 6.2): these rules, typical AI failure modes (plausible but wrong code, invented dependencies, missed defects, prompt injection, automation bias) and reporting. Retrain on material changes. Records: eQMS training module, course AI-DEV-01 (records TR-2026-301 to TR-2026-320, all 2026-10-19). Effectiveness check: PQ-01 review-time outliers (reviewed by the Engineering Lead), the PQ-02 re-review sample and periodic review findings, reported to the Head of QA.

## 8. Approval

Approved in the eQMS by the Head of QA. Author: Jordan Demo (Engineering Lead); reviewed by Alex Example (Validation Engineer). AI assistance in drafting: no. Version 1.0 approved in the eQMS by Sam Sample on 2026-10-19 and version 1.1 on 2026-10-23: [signed in eQMS].

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-19 | Jordan Demo | Initial draft generated with the kit (0.2.0, lite profile) |
| 1.0 | 2026-10-19 | Jordan Demo | Issued; all users briefed the same day |
| 1.1 | 2026-10-23 | Jordan Demo | Status after the release decisions |
