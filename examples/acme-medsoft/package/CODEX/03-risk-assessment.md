> FICTIONAL EXAMPLE - not a real validation record. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are invented to show what an executed package looks like. Model ids are placeholders, not real model names. Signatures are applied by each person in the eQMS and are shown here only as "[signed in eQMS]".

# ACME-VAL-CODEX-03 Risk assessment: OpenAI Codex

| Field | Value |
|---|---|
| Document ID | ACME-VAL-CODEX-03 |
| Title | Risk assessment and criticality determination: OpenAI Codex |
| Version | 1.1 (approved 2026-10-23) |
| Owner (role) | Validation Engineer |
| Approver (role) | Head of QA |
| Date | 2026-10-18 |
| Organisation | Acme MedSoft |

> Generated with the AI Coding Tool Validation Kit 0.1.0. Complete every `[fill in]` and confirm every suggested determination before review. Approval is given by the approver personally in the eQMS.

## 1. Purpose and scope

This document assesses the **process risk** of using OpenAI Codex (OpenAI) for the contexts of use defined in ACME-VAL-CODEX-01, links each AI-specific failure mode to the controlling requirement (ACME-VAL-CODEX-02) and to the test that proves it (ACME-VAL-CODEX-05), determines the criticality and the resulting assurance level, test depth and review cadence, and justifies the model policy.

Process risk is not device risk. Where an AI-assisted change could affect a risk control of the device, the device risk management file is updated under the normal design-change process: ACME-QP-10 Risk management; device risk management file ACME-RMF-LUMEN (no risk control of the device is implemented with or by the tool).

## 2. References

- ISO 13485:2016 §4.1.6: validation approach and activities proportionate to the risk associated with the use of the software.
- 21 CFR Part 820 (QMSR), §820.10, incorporating ISO 13485:2016 by reference (§820.7). 21 CFR Part 11 applies to the records of this package that are kept or signed electronically.
- ISO/IEC 27001 (cross-reference): information security risk treatment for R-05, R-06 and R-10. ISMS risk register entries ISR-2026-031 (AI vendor data handling) and ISR-2026-032 (agent credentials).
- Informative: FDA guidance "Computer Software Assurance for Production and Quality Management System Software" (February 2026); ISO/TR 80002-2:2017 (risk-based, critical thinking); ISPE GAMP 5 Second Edition (2022).

## 3. Method

1. For each context of use, identify reasonably foreseeable failures of the tool to perform as intended. Assess the failure, not the feature name or how often it is used.
2. Determine the process risk with the model selected for Acme MedSoft (section 5).
3. Credit the other controls that limit the effect of a failure (server-side human approval gate, required CI checks, downstream verification, supplier evidence) only when those controls are themselves tested in this validation.
4. Select assurance activities, test depth and review cadence from the determination (section 6).
5. Record residual risks and their acceptance (section 9).

Rules applied regardless of the determination: negative tests of every gate (OQ-02 to OQ-07) are always scripted; MA-01 runs on every model in the envelope; acceptance criteria are fixed before execution; the tool never executes, concludes or approves its own validation.

## 4. AI-specific failure modes

| ID | Failure mode | Typical cause | Effect on product / QMS | Controls (REQ) | Verified by |
|---|---|---|---|---|---|
| R-01 | Incorrect or hallucinated code accepted | Plausible but wrong output; reviewer trusts the AI explanation instead of reading the diff | Defect in released software; nonconforming product | REQ-01, REQ-03, REQ-10, REQ-17 | OQ-01, OQ-07, PQ-02 |
| R-02 | Silent omission or false negative | The AI misses a defect in review, omits a required step or edge case, writes a test that does not exercise the requirement, or an agent misses an item it should report | False assurance; defects go undetected | REQ-01, REQ-03, REQ-15 | PQ-02, OQ-04 |
| R-03 | Wrong-target write | Wrong branch, file, repository or record selected | Corrupted controlled record or unintended component changed | REQ-01, REQ-11, REQ-13 | OQ-12, OQ-20 |
| R-04 | Behaviour drift without a version change | Vendor changes the model behind an unchanged id or alias, default modes or fallbacks without a tool version bump | Validated state no longer represents actual behaviour | REQ-06, REQ-08, REQ-12 | MA-01 and its scheduled re-run on the current envelope (ACME-VAL-CODEX-08 T19), OQ-10, OQ-13, PQ-01 |
| R-05 | Prompt injection | Instructions planted in repository files, issues, PR comments, web content or MCP tool output | Agent takes unintended actions: edits gates, leaks data, pushes changes | REQ-02, REQ-04, REQ-06, REQ-07 | OQ-40, OQ-08 |
| R-06 | Secret, health data or personal data leakage | Secrets in context or environment, data pasted into prompts, plaintext local transcripts, generated code embedding secrets | Data breach; contractual or regulatory breach | REQ-03, REQ-07, REQ-09 | IQ-05, OQ-07, OQ-08 |
| R-07 | Hallucinated or unapproved dependency ("slopsquatting") | The AI proposes a package name that does not exist or is attacker-controlled, or an unvetted component | Malicious or unqualified SOUP in the product | REQ-03, REQ-01 | OQ-07 |
| R-08 | Automation bias / rubber-stamp review | Large AI-generated diffs, time pressure, over-trust in AI review comments | The human gate exists on paper but not in substance | REQ-01, REQ-10, REQ-17, REQ-15 | PQ-01 (review time and comment metrics), PQ-02 |
| R-09 | Agent disables gates or edits CI | The agent edits workflow, gate, configuration or instruction files to make its change pass | Required checks or rules silently weakened | REQ-03, REQ-04, REQ-06, REQ-07 | OQ-03, OQ-06, OQ-09, MA-01 |
| R-10 | Personal-account dependency | Tool or agents run on a person's own account or identity | No organisational control of data, configuration or records; records lost when the person leaves | REQ-05, REQ-16 | IQ-02, IQ-04 |
| R-11 | Vendor terms change | Retention, training use, region, sub-processors or plan features change | Data handling no longer as contracted; supplier evaluation outdated | REQ-09, REQ-12 | IQ-05, monitoring records (ACME-VAL-CODEX-08) |
| R-12 | Guardrail fails open or is not delivered | Sandbox unavailable, policy hook crashes or times out, managed settings do not reach a surface (CI, cloud) | Controls assumed but absent on some surfaces | REQ-06, REQ-07 | IQ-03, IQ-04, OQ-08, OQ-09 |
| R-13 | Model outside the envelope used | User switch, automatic fallback, new vendor default model | Unadmitted behaviour in use | REQ-08 | OQ-10, MA-01, PQ-01 |
| R-14 | AI or bot approval counted, or launcher approves the agent's PR | Platform setting lets AI, app or CI-token approvals satisfy the rule; the person who launched an agent with its own identity approves the agent's PR, which the platform counts | Change merged without qualified, independent human approval | REQ-02, REQ-15 | OQ-04, OQ-05 |
| R-15 | Loss of provenance or attribution | No label on AI-assisted changes; agent acts under a human identity | AI-assisted changes cannot be identified for review, sampling or recall | REQ-05, REQ-10 | IQ-04, OQ-11 |
| R-16 | Unsourced or fabricated content in a controlled document | The AI states facts from memory or invents references | Incorrect controlled document or record | REQ-13, REQ-01 | OQ-20 |
| R-18 | Self-validation | The tool drafts the protocol, executes tests or writes the conclusion of its own validation | Validation not independent; conclusion not attributable | Roles and authorship rules in ACME-VAL-CODEX-04 | Review of ACME-VAL-CODEX-07 authorship statement |
| R-19 | Evidence not retained | Platform retention shorter than the record retention period (audit logs, CI logs, review history) | Validation and gate evidence lost | REQ-04; evidence rules in ACME-VAL-CODEX-04 | PQ-01 (exports archived) |

Add tool- or organisation-specific failure modes below the table with IDs from R-20.

## 5. Criticality determination per context of use

Risk model: **FDA CSA (binary)**. A context is **high process risk** when failure of the tool to perform as intended in that context may result in a quality problem that foreseeably compromises safety (an increased medical device risk). Otherwise it is **not high process risk**. Acme MedSoft may document finer internal tiers, but the binary determination drives the assurance level.

| Context | Foreseeable failure and effect | Controls credited | Suggested determination | Determination | Rationale |
|---|---|---|---|---|---|
| `code_product` | Wrong or insecure code reaches device software (R-01, R-07) | REQ-01, REQ-03 | High process risk | High process risk (confirmed) | Product software (IEC 62304 class B); a wrong change that passed review could compromise a device function |
| `code_tooling` | Defect in internal tooling | REQ-01, REQ-03 | Not high, unless the tooling produces QMS records or verification results (then high) | Not high (confirmed) | qa-tooling holds developer convenience scripts; the SOUP gate and release scripts live in the product repositories and are covered by `code_product` |
| `pr_review` | Missed or wrong review comment (R-02, R-08) | REQ-01, REQ-15 (human review remains the control) | Not high, provided REQ-15 holds | Not high (confirmed) | AI review is advisory; the human approval gate is unchanged (OQ-04 passed) |
| `doc_drafting` | Unsourced or wrong content in a controlled document (R-16, R-03) | REQ-13, document approval | Not high if every draft is reviewed against its cited sources and approved by the document owner; high if drafts can reach records without that review | Not high (confirmed) | Every draft is a PR in qms-docs, reviewed against its sources and released in the eQMS by the document approver |

**Overall determination for OpenAI Codex:** the highest determination of any context: **high process risk** (`code_product`).

## 6. Resulting assurance level, test depth and cadence

| Determination | Assurance activities | Test depth | Samples | Review cadence |
|---|---|---|---|---|
| High process risk | Scripted testing of all gates and guardrails with positive and negative cases; MA-01 on every model in the envelope; PQ-01 and PQ-02; supplier evidence as supplement only | Robust scripted for OQ-01 to OQ-12 and for the context tests (OQ-20, OQ-30) in scope; error-guessing and exploratory sessions in addition | Minimums in ACME-VAL-CODEX-04, increased by two repositories in OQ-01 and two in every negative gate test | Recommended 6 months (configured: 6), plus every trigger in ACME-VAL-CODEX-08 |
| Not high process risk | Scripted negative tests of the gates and MA-01 on every model in the envelope (always); unscripted (ad hoc, error-guessing, exploratory) and historical evidence for the rest; supplier evidence may be credited | Limited scripted or unscripted with the same acceptance criteria | Minimums in ACME-VAL-CODEX-04 | Typically 12 months (configured: 6), plus every trigger in ACME-VAL-CODEX-08 |

Configured periodic review interval: every 6 months. If the overall determination is the highest level and the configured interval is longer than 6 months, justify it here: not needed (6 months configured).

## 7. Model policy determination

The model policy follows from whether the AI output itself is relied on as a control or as evidence.

| # | Question | Answer |
|---|---|---|
| M1 | Is an AI reviewer counted as verification in any context? (Not allowed by REQ-15; answer must be no.) | no |
| M2 | Is AI output used as a judge, or to compute a result that is recorded as evidence without independent recomputation? | no |
| M3 | Are records written from AI drafts without independent human verification against sources? | no |
| M4 | Do autonomous or scheduled agents act on QMS systems? | no (`agents_qms` not selected) |

Any "yes" for M2 to M4 requires the **pinned** policy for the affected use. Otherwise the **envelope** policy is appropriate, because the output is independently verified downstream.

Selected policy: **envelope**. Approved envelope: `openai-model-a` `openai-model-b` 

Justification: AI output in every context is verified by qualified human review and required CI checks before it takes effect (REQ-01, REQ-03, REQ-13). Residual model risk is controlled by MA-01 on every model entering the envelope, by recording the model per PR or session (REQ-08) and by PQ-01. No AI output is counted as a control or as evidence in OpenAI Codex.

## 8. Known guardrail limitations of OpenAI Codex

These limitations are inputs to the residual risk. Confirm each against the vendor's current documentation at IQ. Each has an ID (KL-nn) so that the test protocol can list, before execution, the limitations that are accepted and reproduced rather than failed.

- KL-01: In PreToolUse hooks only an explicit deny blocks; errors, timeouts and unsupported outputs let the tool call continue (R-12).
- KL-02: Environment variables named like KEY, SECRET or TOKEN reach spawned commands by default (R-06).
- KL-03: `managed_config.toml` supplies defaults that users can change during a run; only `requirements.toml` enforces (R-12).
- KL-04: Model defaults in requirements are not enforcement (R-13).
- KL-05: The identity used by cloud tasks for commits and PRs is not documented (R-15).
- KL-06: Vendor compliance logs and telemetry do not establish a complete record of every local action (R-19).
- KL-07: Command rules govern only commands run outside the sandbox: a command that runs inside the workspace-write sandbox is not stopped by a rule, so the MA-01 denied-command check counts only with a verified deny control such as a managed PreToolUse hook (R-05, R-12).

## 9. Residual risk and acceptance

| Risk ID | Residual risk after controls | Acceptable? | Additional measure or restriction |
|---|---|---|---|
| R-13 | Model envelope monitored, not enforced (no verified client-side enforcement) | yes: output verified downstream; model recorded per session (telemetry) | Weekly model-use check; a model first seen without an admission record is a T4 deviation with MA-01 within 5 working days (ACME-VAL-CODEX-04 section 5.2); PQ-01; re-check vendor documentation at each release review |
| R-12 | Policy hooks may fail open on error or timeout (KL-01) | yes: hooks are not relied on alone; requirements, sandbox and server-side gates enforce | OQ-08 re-test on releases touching hooks (T7) |
| R-05, R-12 | No verified deny control for commands inside the sandbox; command rules cover only commands outside it, so the MA-01 denied-command check is N/A (KL-07) | yes: commands inside `workspace-write` have no network and cannot change protected paths; the server-side gate binds | Re-assess at each release review; declare a verified control to MA-01 once one exists |
| R-15 | Cloud PR / commit identity not documented by the vendor | yes, with restriction | Empirical IQ-04 result recorded; cloud agent limited to non-product repositories until ACME-VEN-2026-015-B is closed |
| R-11 | Outsourced cloud execution (ISO 13485 §4.1.5) not yet covered by a terms review; certificate scope does not name the coding product | yes, with restriction | ACME-VEN-2026-015-A and ACME-VEN-2026-015-B, due 2026-11-30 |
| R-08 | Rubber-stamp review of large AI-generated diffs | yes, with monitoring | PQ-01 review-time metrics; PQ-02 at each periodic review |

Overall conclusion: residual risk acceptable with restrictions (cloud agent limited to non-product repositories until the §4.1.5 terms review ACME-VEN-2026-015-B is approved). Written by Alex Example (Validation Engineer) on 2026-10-23 after the test results; accepted by Sam Sample on 2026-10-23 [signed in eQMS]; Robin Specimen informed on 2026-10-23. The conclusion is written by a named human author, not by the AI tool. Accepted in the eQMS by the Head of QA, with Regulatory Affairs Manager informed.

## Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-18 | Alex Example | Initial draft generated with the kit (0.1.0) |
| 1.0 | 2026-10-19 | Alex Example | Determinations confirmed; approved before execution |
| 1.1 | 2026-10-23 | Alex Example | Residual risks (section 9) completed with the test results |
