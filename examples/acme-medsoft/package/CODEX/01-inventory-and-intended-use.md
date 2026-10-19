> FICTIONAL EXAMPLE - not a real validation record. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are invented to show what an executed package looks like. Model ids are placeholders, not real model names. Signatures are applied by each person in the eQMS and are shown here only as "[signed in eQMS]".

# ACME-VAL-CODEX-01 Inventory and intended use: OpenAI Codex

| Field | Value |
|---|---|
| Document ID | ACME-VAL-CODEX-01 |
| Title | Inventory and intended use: OpenAI Codex |
| Version | 1.1 (approved 2026-10-23) |
| Owner (role) | Engineering Lead |
| Approver (role) | Head of QA |
| Date | 2026-10-18 |
| Organisation | Acme MedSoft |
| Product context | Class II SaMD (FDA 510(k)); EU MDR Class IIa planned |

> Generated with the AI Coding Tool Validation Kit 0.2.0. Complete every `[fill in]` before review. Approval is given by the approver personally in the eQMS (or with an electronic signature); never type a name or signature into this document on someone else's behalf, and never let the AI tool do it.

## 1. Purpose and scope

This document registers OpenAI Codex (OpenAI) in the software inventory of Acme MedSoft, decides whether its use is QMS-relevant, and defines the intended use for each context of use. It is the input to the requirements (ACME-VAL-CODEX-02), the risk assessment (ACME-VAL-CODEX-03) and the validation plan (ACME-VAL-CODEX-04).

The validation unit is **tool + vendor + surface + context of use**. The language model behind the tool is not qualified as such. What is validated is the intended use, the guardrails around the tool, and the verification of its output. Models are handled through an approved model envelope (section 4) and the model admission check MA-01.

## 2. References

- ISO 13485:2016 clause 4.1.6 (validation of computer software used in the QMS), clause 4.2.4 (control of documents: instruction and settings files are controlled configuration items), clause 6.2 (competence), clause 7.4 (purchasing: evaluation of the AI vendor).
- ISO 13485:2016 clause 4.1.5 (outsourced processes): interpretation, relevant when agents run on vendor infrastructure (cloud agents). Document either the quality agreement / terms review or why the clause does not apply.
- 21 CFR Part 820 (QMSR): 21 CFR 820.10, which incorporates ISO 13485:2016 by reference (21 CFR 820.7). Software validation duties come from ISO 13485 clauses 4.1.6, 7.5.6 and 7.6 as incorporated; the former 21 CFR 820.70(i) no longer exists and is not cited. 21 CFR Part 11 applies to the records of this package that are kept or signed electronically.
- ISO/IEC 27001 (cross-reference): supplier relationships, secure development, configuration and change management controls: ISO/IEC 27001:2022 Annex A 5.19 to 5.23 (supplier relationships, cloud services), 8.9 (configuration management), 8.25 and 8.28 (secure development and coding), 8.32 (change management); Statement of Applicability ACME-ISMS-SOA rev 4.
- Informative: FDA guidance "Computer Software Assurance for Production and Quality Management System Software" (February 2026); ISO/TR 80002-2:2017; ISPE GAMP 5 Second Edition (2022), Appendix D9 (Software Tools) and D11 (AI/ML).
- Internal: ACME-VAL-GEN-01 AI-assisted development work instruction; ACME-VAL-GEN-02 Tool discovery checklist; ACME-QP-04 Validation of QMS and development software; supplier evaluation record ACME-VEN-2026-015 (OpenAI).

## 3. Tool identification

| Field | Value |
|---|---|
| Tool | OpenAI Codex |
| Tool type | `codex` |
| Tool ID (used in document IDs and evidence folders) | CODEX |
| Vendor | OpenAI |
| Product / plan | Enterprise workspace, contract ACME-PUR-2026-019 |
| Organisation account / workspace | Workspace "Acme MedSoft"; identifier recorded in ACME-VAL-CODEX-06 section 5 |
| Account ownership | Organisation-owned, single sign-on via the corporate identity provider (SAML). Personal accounts are prohibited for QMS use (REQ-16). |
| Console administrators | Jordan Demo (Engineering Lead) and Casey Admin (IT administrator) |
| Surfaces in use (detail in section 5) | `local_cli_ide` `cloud_agent`  |
| Validated version / release channel | codex-cli 0.163.0 (stable releases only); cloud agent vendor-hosted |
| Update control | Endpoint-managed package pinned to 0.163.0; `check_for_update_on_startup = false` enforced in `requirements.toml`; upgrades only by change record (ACME-VAL-CODEX-08, T7) |
| Model policy | envelope |
| Approved model envelope | `openai-model-a` `openai-model-b`  |
| Code hosting | GitHub |
| Status | Validated on 2026-10-23 (retrospective validation; interim use under ACME-VAL-CODEX-04 section 12 ended with the release decision); cloud agent restricted, see ACME-VAL-CODEX-07 |
| Date of first known use | 2026-06-15 (workspace activation and first Codex-assisted PR in qa-tooling, confirmed in interviews during ACME-VAL-GEN-02) |
| GAMP 5 category | See section 7 |
| Criticality | High process risk, driven by `code_product` (ACME-VAL-CODEX-03 section 5) |
| Periodic review | Every 6 months, and on the triggers in ACME-VAL-CODEX-08 |
| Last validation | 2026-10-23, ACME-VAL-CODEX-07: approved with restrictions (cloud agent) |

Version evidence for Codex: `codex --version` (prints `codex-cli <version>`) and `codex doctor`. In CI, pin the GitHub Action to a tag or commit SHA and set its `codex-version` input explicitly: leaving it blank installs the latest published CLI.

## 4. Approved model envelope and model policy

Approved models (ids or family patterns, as entered in the kit configuration):

- `openai-model-a`
- `openai-model-b`

Policy: **envelope**. AI output is independently verified downstream (human review plus required CI checks), so any model inside the envelope may be used. A model enters the envelope only after MA-01 passes, and the model used is recorded per PR or session (REQ-08). A family pattern pre-authorises the admission route, not the model itself.

The rationale for the policy is in ACME-VAL-CODEX-03. The approved envelope at release is restated in ACME-VAL-CODEX-07.

## 5. Surfaces and identities

Input to IQ-04 (surface to identity mapping). Surfaces not listed here are not permitted.

| Surface | Who starts it | Identity that writes (commits, PRs, comments, records) | Where it writes | Configuration delivery path | Evidence ref |
|---|---|---|---|---|---|
| Local CLI / IDE | Trained developer | Developer's own git and GitHub identity; PR declaration marks AI assistance | Feature branches and PRs in the four repositories of section 8 | `requirements.toml` (Linux) and MDM payload (macOS) by endpoint management | IQ-03, IQ-04 |
| Cloud agent | Members of group `acme-codex-cloud` | Vendor GitHub connector identity (observed in IQ-04) | Branches and PRs in `acme-medsoft/qa-tooling` and `acme-medsoft/val-sandbox` only (restriction, ACME-VAL-CODEX-07) | Cloud-managed requirements and environment settings in the workspace admin console | IQ-01, IQ-04, IQ-05 |

Codex notes: cloud environments do not inherit local device policy or MDM; cloud-managed requirements are configured in the workspace admin console. Vendor documentation does not state which GitHub identity authors commits and PRs created from cloud tasks: establish it empirically in IQ-04.

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
| Who | Triggered automatically or by developers (`@codex review` comment by the PR author or reviewer) |
| Where | `acme-medsoft/qa-tooling` only (cloud review restricted to non-product repositories, ACME-VAL-CODEX-07) |
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
- Local transcripts and logs on developer machines are transient data minimised for privacy (`history.persistence = "none"`); the QMS records are the PRs, reviews and evidence exports; decide and record it in ACME-VAL-CODEX-06.
- Full rules: ACME-VAL-GEN-01.

## 11. Supplier and contractual terms (input to IQ-05)

| Item | Value |
|---|---|
| Contract / terms reference | ACME-PUR-2026-019 and DPA of 2026-06-01 |
| Data retention by the vendor | Workspace retention setting configured by the workspace owner (value in ACME-VAL-CODEX-06 section 13); Compliance API records 30 days |
| Use of data for model training | Not used for training (enterprise workspace default; not changed) |
| Processing region / residency | No residency commitment (`enforce_residency` not set); accepted in DPIA-2026-03 |
| Certifications (scope and expiry as stated on the certificate) | Scope text and expiry recorded in IQ-05 evidence; coverage of the coding product to be confirmed (ACME-VEN-2026-015-A) |
| Change and deprecation notification commitments | Contract notice for material changes of terms; product changes followed through the monitoring routine (ACME-VAL-CODEX-08) |
| Supplier evaluation record | ACME-VEN-2026-015, approved supplier since 2026-06-10; ISO 13485 clause 4.1.5 terms review of cloud execution open (ACME-VEN-2026-015-B) (ISO 13485 clause 7.4) |

OpenAI publishes certifications on its Trust Portal (trust.openai.com). Whether the scope covers Codex was not verified: record the scope text and expiry. With ChatGPT sign-in, data follows the workspace retention and residency settings; with an API key, it follows the API organisation's settings.

## 12. Related documents

| ID | Title |
|---|---|
| ACME-VAL-CODEX-02 | Requirements |
| ACME-VAL-CODEX-03 | Risk assessment |
| ACME-VAL-CODEX-04 | Validation plan |
| ACME-VAL-CODEX-05 | Test protocol |
| ACME-VAL-CODEX-06 | Configuration baseline |
| ACME-VAL-CODEX-07 | Validation report |
| ACME-VAL-CODEX-08 | Change and revalidation |
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
