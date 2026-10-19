> FICTIONAL EXAMPLE - not a real validation record. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are invented to show what an executed package looks like. Model ids are placeholders, not real model names. Signatures are applied by each person in the eQMS and are shown here only as "[signed in eQMS]".

# ACME-VAL-CLAUDE-01 Inventory and intended use: Claude Code

| Field | Value |
|---|---|
| Document ID | ACME-VAL-CLAUDE-01 |
| Title | Inventory and intended use: Claude Code |
| Version | 1.1 (approved 2026-10-23) |
| Owner (role) | Engineering Lead |
| Approver (role) | Head of QA |
| Date | 2026-10-18 |
| Organisation | Acme MedSoft |
| Product context | Class II SaMD (FDA 510(k)); EU MDR Class IIa planned |

> Generated with the AI Coding Tool Validation Kit 0.2.0. Complete every `[fill in]` before review. Approval is given by the approver personally in the eQMS (or with an electronic signature); never type a name or signature into this document on someone else's behalf, and never let the AI tool do it.

## 1. Purpose and scope

This document registers Claude Code (Anthropic) in the software inventory of Acme MedSoft, decides whether its use is QMS-relevant, and defines the intended use for each context of use. It is the input to the requirements (ACME-VAL-CLAUDE-02), the risk assessment (ACME-VAL-CLAUDE-03) and the validation plan (ACME-VAL-CLAUDE-04).

The validation unit is **tool + vendor + surface + context of use**. The language model behind the tool is not qualified as such. What is validated is the intended use, the guardrails around the tool, and the verification of its output. Models are handled through an approved model envelope (section 4) and the model admission check MA-01.

## 2. References

- ISO 13485:2016 clause 4.1.6 (validation of computer software used in the QMS), clause 4.2.4 (control of documents: instruction and settings files are controlled configuration items), clause 6.2 (competence), clause 7.4 (purchasing: evaluation of the AI vendor).
- ISO 13485:2016 clause 4.1.5 (outsourced processes): interpretation, relevant when agents run on vendor infrastructure (cloud agents). Document either the quality agreement / terms review or why the clause does not apply.
- 21 CFR Part 820 (QMSR): 21 CFR 820.10, which incorporates ISO 13485:2016 by reference (21 CFR 820.7). Software validation duties come from ISO 13485 clauses 4.1.6, 7.5.6 and 7.6 as incorporated; the former 21 CFR 820.70(i) no longer exists and is not cited. 21 CFR Part 11 applies to the records of this package that are kept or signed electronically.
- ISO/IEC 27001 (cross-reference): supplier relationships, secure development, configuration and change management controls: ISO/IEC 27001:2022 Annex A 5.19 to 5.23 (supplier relationships, cloud services), 8.9 (configuration management), 8.25 and 8.28 (secure development and coding), 8.32 (change management); Statement of Applicability ACME-ISMS-SOA rev 4.
- Informative: FDA guidance "Computer Software Assurance for Production and Quality Management System Software" (February 2026); ISO/TR 80002-2:2017; ISPE GAMP 5 Second Edition (2022), Appendix D9 (Software Tools) and D11 (AI/ML).
- Internal: ACME-VAL-GEN-01 AI-assisted development work instruction; ACME-VAL-GEN-02 Tool discovery checklist; ACME-QP-04 Validation of QMS and development software; supplier evaluation record ACME-VEN-2026-011 (Anthropic).

## 3. Tool identification

| Field | Value |
|---|---|
| Tool | Claude Code |
| Tool type | `claude_code` |
| Tool ID (used in document IDs and evidence folders) | CLAUDE |
| Vendor | Anthropic |
| Product / plan | Enterprise plan, contract ACME-PUR-2026-014 |
| Organisation account / workspace | Organisation "Acme MedSoft"; identifier recorded in ACME-VAL-CLAUDE-06 section 5 |
| Account ownership | Organisation-owned, single sign-on via the corporate identity provider (SAML). Personal accounts are prohibited for QMS use (REQ-16). |
| Console administrators | Jordan Demo (Engineering Lead) and Casey Admin (IT administrator) |
| Surfaces in use (detail in section 5) | `local_cli_ide` `pr_review_bot` `ci_headless`  |
| Validated version / release channel | 2.1.302 (managed minimum = maximum), channel "stable" |
| Update control | Managed `requiredMinimumVersion` / `requiredMaximumVersion` and `autoUpdatesChannel`; CI runner image digest and action commit SHA pinned; range raised only by change record (ACME-VAL-CLAUDE-08, T7) |
| Model policy | envelope |
| Approved model envelope | `anthropic-model-a` `anthropic-model-b`  |
| Code hosting | GitHub |
| Status | Validated on 2026-10-23 (retrospective validation; interim use under ACME-VAL-CLAUDE-04 section 12 ended with the release decision) |
| Date of first known use | 2026-01-12 (first invoice, first AI-attributed commit in lumen-core, confirmed in interviews during ACME-VAL-GEN-02) |
| GAMP 5 category | See section 7 |
| Criticality | High process risk, driven by `code_product` (ACME-VAL-CLAUDE-03 section 5) |
| Periodic review | Every 6 months, and on the triggers in ACME-VAL-CLAUDE-08 |
| Last validation | 2026-10-23, ACME-VAL-CLAUDE-07: approved for intended use |

Version evidence for Claude Code: `claude --version` and `claude doctor` (which reports the auto-update state). Update control options: the `autoUpdatesChannel` setting (`"stable"` or `"latest"`), the `DISABLE_UPDATES=1` environment variable, and the managed-only `requiredMinimumVersion` / `requiredMaximumVersion` keys. Invalid values of the two version keys are dropped instead of enforced, so confirm the effect with `claude --version` on a test machine before rollout. Releases are very frequent; the validated range must be explicit.

## 4. Approved model envelope and model policy

Approved models (ids or family patterns, as entered in the kit configuration):

- `anthropic-model-a`
- `anthropic-model-b`

Policy: **envelope**. AI output is independently verified downstream (human review plus required CI checks), so any model inside the envelope may be used. A model enters the envelope only after MA-01 passes, and the model used is recorded per PR or session (REQ-08). A family pattern pre-authorises the admission route, not the model itself.

The rationale for the policy is in ACME-VAL-CLAUDE-03. The approved envelope at release is restated in ACME-VAL-CLAUDE-07.

## 5. Surfaces and identities

Input to IQ-04 (surface to identity mapping). Surfaces not listed here are not permitted.

| Surface | Who starts it | Identity that writes (commits, PRs, comments, records) | Where it writes | Configuration delivery path | Evidence ref |
|---|---|---|---|---|---|
| Local CLI / IDE | Trained developer | Developer's own git and GitHub identity; managed attribution trailer marks AI assistance | Feature branches and PRs in the four repositories of section 8 | Managed settings file deployed by endpoint management (macOS, Linux) | IQ-03, IQ-04 |
| PR review bot | Automatically on every PR (workflow `claude-review.yml`) | `acme-claude-reviewer[bot]` (custom GitHub App) | Review comments only | Action `settings` input plus managed settings file in the runner image | IQ-01, IQ-04, OQ-04 |
| CI / headless | Nightly workflow `test-gap-report` in qa-tooling | Workflow token (`contents: read`) | Job artifact only, no repository writes | Managed settings file in runner image `acme-ci-ubuntu-2026.10.2`; explicit `--permission-mode` | IQ-01, IQ-04, OQ-08 |

Claude Code notes: device-deployed managed settings (file or MDM) never reach Anthropic-hosted cloud sessions; server-managed settings are not delivered to sessions that authenticate with a Console API key (typical in CI) and are skipped when a third-party provider or a custom `ANTHROPIC_BASE_URL` is used. Each surface therefore needs its own delivery path and its own IQ evidence.

## 6. QMS-relevance determination

Answer each question for the contexts in section 8. One "yes" makes the use QMS-relevant.

| # | Question | Answer | Rationale |
|---|---|---|---|
| Q1 | Is the tool used to create or change software that is part of the device, or that is used to produce, test or release it? | yes | Product code in lumen-core and lumen-app |
| Q2 | Does its output become part of a controlled document or a QMS record? | yes | Drafts of controlled documents in qms-docs |
| Q3 | Is it used in verification (tests, reviews) whose results are relied on? | no | AI review comments are advisory (REQ-15); verification results come from CI and human review |
| Q4 | Does it read or write QMS systems (eQMS, issue tracker used for CAPA or change control, document repository)? | yes | Writes drafts to the controlled document repository qms-docs (never to the eQMS) |
| Q5 | Could a failure affect product conformity or QMS compliance without another control detecting it? | no, if the gates hold | Human approval gate and required checks detect failures; these controls are what this validation tests (REQ-01 to REQ-04) |
| Q6 | Does it process confidential design data, personal data or health data? | yes (design data only) | Source code and design documents; personal and health data excluded by the data rules (section 10) |

Decision: **QMS-relevant** (Q1, Q2, Q4, Q6). If QMS-relevant, it is validated under ISO 13485:2016 clause 4.1.6 before (further) use. If not QMS-relevant, record why and keep the tool on the inventory for periodic re-check.

## 7. GAMP 5 category

Recommended: **Category 4 (configured product)**. Agentic coding tools are configured through settings, permission modes, allow/deny rules, sandbox options, hooks, MCP or extension allow-lists and instruction files, and that configuration changes behaviour. The model itself is not categorised; it is managed through the envelope.

Selected category: **Category 4**. Category 3 was not selected, so no justification is needed. A configurable tool classified as non-configured, with its configuration never baselined, is a common audit finding.

## 8. Contexts of use

Boundary for every context: **the AI never approves, merges, signs or closes records.** Approval is always given by the responsible human role named below, under that person's own identity.

### Context: Product code (`code_product`)

| Item | Intended use |
|---|---|
| Who | Software developers of the product team trained on ACME-VAL-GEN-01 |
| Where | `acme-medsoft/lumen-core` and `acme-medsoft/lumen-app`, protected branch `main` |
| Inputs | Work items, requirements, existing source code, test results |
| Outputs | Proposed code changes in branches and pull requests |
| Who approves | A qualified human reviewer other than the author and the agent launcher (ACME-QP-12 Code review and merge) |
| Boundary | The AI never approves, merges, signs or closes records. Changes reach protected branches only through the server-side gate (REQ-01 to REQ-04). |
| Prohibited | Direct pushes to protected branches; editing CI, gate or tool configuration files without code-owner review; changes to safety-classified items without the second review by a senior developer required by the software development plan for safety-related items |
| Data rules | Section 10 |

### Context: Internal tooling (`code_tooling`)

| Item | Intended use |
|---|---|
| Who | Developers and QA engineers trained on ACME-VAL-GEN-01 |
| Where | `acme-medsoft/qa-tooling`, protected branch `main` |
| Inputs | Work items, existing scripts and automation |
| Outputs | Changes to internal tools, scripts and automation in pull requests |
| Who approves | A qualified human reviewer other than the author and the agent launcher |
| Boundary | The AI never approves, merges, signs or closes records. A tool that itself produces QMS records or verification results is validated separately under the software validation procedure. |
| Prohibited | Direct pushes; using AI-written tooling to generate QMS evidence before that tooling is validated |
| Data rules | Section 10 |

### Context: Advisory AI PR review (`pr_review`)

| Item | Intended use |
|---|---|
| Who | Triggered automatically or by developers (workflow `claude-review.yml` on every PR) |
| Where | `acme-medsoft/lumen-core`, `acme-medsoft/lumen-app`, `acme-medsoft/qa-tooling` |
| Inputs | Pull request diff and repository context |
| Outputs | Review comments only |
| Who approves | The human reviewer; AI comments are advisory |
| Boundary | The AI never approves, merges, signs or closes records. AI review is never a required approval and never the only verification (REQ-15). |
| Prohibited | Enabling settings that let AI approvals count toward merge requirements; treating an AI check that concludes neutral as a gate |
| Data rules | Section 10 |

### Context: Document drafting (`doc_drafting`)

| Item | Intended use |
|---|---|
| Who | QA and RA document authors (for example Morgan Writer) trained on ACME-VAL-GEN-01 |
| Where | Procedures, work instructions and technical documentation sections authored in `acme-medsoft/qms-docs` (Markdown) and released through the eQMS |
| Inputs | Approved source documents and records named in the request |
| Outputs | Draft text, with each factual claim citing its source |
| Who approves | The document owner and approver defined by the document control procedure |
| Boundary | The AI never approves, merges, signs or closes records. The human previews the exact content before any write to a controlled record (REQ-13). |
| Prohibited | Writing to a controlled record without preview; releasing a document; drafting the conclusion of the tool's own validation without independent human authorship |
| Data rules | Section 10 |

## 9. Uses outside the intended use

The following are not part of the intended use and are prohibited unless this document is revised and the change is validated:

- any use not covered by a context in section 8;
- use through a surface not listed in section 5, or with a model outside the envelope;
- AI approving, merging, signing or closing anything, or acting as the reviewer of record;
- the tool executing, concluding or approving its own validation;
- use with personal accounts for any QMS-relevant work.

## 10. Data rules

- No secrets (keys, tokens, passwords), no patient or health data and no personal data in prompts, context files or repositories reachable by the tool, unless covered by contract and by the data protection impact assessment DPIA-2026-03.
- Confidential design data only under the organisation account and the contracted terms (section 11).
- Local transcripts and logs on developer machines are transient data minimised for privacy (`cleanupPeriodDays` 30); the QMS records are the PRs, reviews and evidence exports; decide and record it in ACME-VAL-CLAUDE-06.
- Full rules: ACME-VAL-GEN-01.

## 11. Supplier and contractual terms (input to IQ-05)

| Item | Value |
|---|---|
| Contract / terms reference | ACME-PUR-2026-014 and DPA of 2026-01-05 |
| Data retention by the vendor | 30 days standard server retention (commercial terms); no zero-retention option purchased |
| Use of data for model training | Not used for training (commercial terms; no opt-in) |
| Processing region / residency | As stated in the contract; no residency commitment purchased; accepted in DPIA-2026-03 |
| Certifications (scope and expiry as stated on the certificate) | Scope text and expiry recorded in IQ-05 evidence; coverage of the coding tool to be confirmed (ACME-VEN-2026-011-A) |
| Change and deprecation notification commitments | Contract notice for material changes of terms; product changes followed through the monitoring routine (ACME-VAL-CLAUDE-08) |
| Supplier evaluation record | ACME-VEN-2026-011, approved supplier since 2026-01-09 (ISO 13485 clause 7.4) |

Anthropic points to its Trust Center (trust.anthropic.com) for the SOC 2 Type 2 report and ISO/IEC 27001 certificate, and holds an ISO/IEC 42001 certificate. Record the certificate scope text; public statements do not explicitly name Claude Code within those scopes.

## 12. Related documents

| ID | Title |
|---|---|
| ACME-VAL-CLAUDE-02 | Requirements |
| ACME-VAL-CLAUDE-03 | Risk assessment |
| ACME-VAL-CLAUDE-04 | Validation plan |
| ACME-VAL-CLAUDE-05 | Test protocol |
| ACME-VAL-CLAUDE-06 | Configuration baseline |
| ACME-VAL-CLAUDE-07 | Validation report |
| ACME-VAL-CLAUDE-08 | Change and revalidation |
| ACME-VAL-GEN-01 | AI-assisted development work instruction |
| ACME-VAL-GEN-02 | Tool discovery checklist |

## 13. Approval

Reviewed and approved in the eQMS by the Head of QA. Author: Jordan Demo (Engineering Lead); reviewed by Alex Example (Validation Engineer). The AI tool did not assist in drafting this document. Version 1.0 approved in the eQMS by Sam Sample on 2026-10-19 and version 1.1 on 2026-10-23: [signed in eQMS].

## Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-18 | Jordan Demo | Initial draft generated with the kit (0.2.0) |
| 1.0 | 2026-10-19 | Jordan Demo | Completed and approved for the validation |
| 1.1 | 2026-10-23 | Jordan Demo | Status, criticality and last validation updated after the release decision |
