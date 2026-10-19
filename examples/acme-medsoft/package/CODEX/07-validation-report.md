> FICTIONAL EXAMPLE - not a real validation record. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are invented to show what an executed package looks like. Model ids are placeholders, not real model names. Signatures are applied by each person in the eQMS and are shown here only as "[signed in eQMS]".

# ACME-VAL-CODEX-07 Validation report: OpenAI Codex

| Field | Value |
|---|---|
| Document ID | ACME-VAL-CODEX-07 |
| Title | Validation report and release decision |
| Organisation | Acme MedSoft |
| Tool / vendor | OpenAI Codex / OpenAI |
| Product context | Class II SaMD (FDA 510(k)); EU MDR Class IIa planned |
| Report drafted by (role) | Validation Engineer |
| Technical review (role) | Engineering Lead |
| Release decision (role) | Head of QA |
| Rendered | 2026-10-18 (kit 0.2.0) |

Related documents: ACME-VAL-CODEX-01 Inventory and intended use · ACME-VAL-CODEX-02 Requirements · ACME-VAL-CODEX-03 Risk assessment · ACME-VAL-CODEX-04 Validation plan · ACME-VAL-CODEX-05 Test protocol · ACME-VAL-CODEX-06 Configuration baseline · ACME-VAL-CODEX-08 Change and revalidation · ACME-VAL-GEN-01 Work instruction · ACME-VAL-GEN-02 Tool discovery checklist · ACME-VAL-GEN-03 Code-host gate qualification.

## 1. Summary

| Item | Value |
|---|---|
| Validation unit | OpenAI Codex (OpenAI), surfaces and contexts listed below |
| Configuration baseline validated (ACME-VAL-CODEX-06) | Baseline ID CODEX-BL-01 rev 1 |
| Tool version(s) validated (each with IQ-01, IQ-03, OQ-08 and OQ-09 executed on it, or a T6 assessment) | codex-cli 0.163.0 (IQ-01, IQ-03, OQ-08 and OQ-09 executed on it); cloud agent vendor-hosted (state of 2026-10-20) |
| Protocol version executed (ACME-VAL-CODEX-05) and amendments | 1.0, approved 2026-10-19; no amendments |
| Code-host gate qualification credited (ACME-VAL-GEN-03, revision and date) | version 1.0, executed 2026-10-21 and 2026-10-22, all tests Pass |
| Execution period (UTC) | from 2026-10-20 to 2026-10-22 |
| Tests executed / passed / failed / N/A | 22 / 22 / 0 / 0 (MA-01 denied-command check N/A within a passed test, KL-07); PQ-01 and PQ-02 pending (addendum) |
| Open deviations at release | none |
| Release decision (section 13) | Approved with restrictions (cloud agent limited to non-product repositories), with conditions until the PQ addendum is signed |

Surfaces:

- Local CLI / IDE (`local_cli_ide`)
- Cloud agent (`cloud_agent`)

Contexts of use:

- Product code: Code for the regulated product (software in or as a medical device).
- Internal tooling: Internal tools, scripts and automation that are not part of the product.
- Advisory AI PR review: AI review comments on pull requests; advisory only, never counted as the required human approval.
- Document drafting: Drafting of controlled documents and records, previewed and approved by a human before they are written or released.

Summary of results (written by the person named in section 14, not by the AI tool): all 22 tests passed. The server-side gate held in every negative test, including attempts driven through Codex; admin requirements could not be overridden; both models in the envelope passed MA-01; 4 weeks of in-use data showed qualified human approval on every merged PR. The model envelope is monitored, not enforced, because no client-side enforcement was found. The ISO 13485 clause 4.1.5 terms review of cloud execution is still open, so the cloud agent is restricted to non-product repositories until it is approved.

## 2. Regulatory basis

- ISO 13485:2016 clause 4.1.6: validation of QMS software before initial use and after changes, proportionate to risk, with records (clause 4.2.5). Supporting clauses: 4.2.4 (controlled configuration), 6.2 (competence), 7.4 (supplier), 4.1.5 (outsourced processes, for vendor-hosted agents).
- 21 CFR Part 820 (QMSR, in force since 2 February 2026): 21 CFR 820.10, incorporating ISO 13485:2016 by reference (21 CFR 820.7). FDA guidance "Computer Software Assurance for Production and Quality Management System Software": this report records the intended use, the risk determination, the assurance activities, the issues found and their disposition, a conclusion, the date and the name of the people involved, and the approval.
- 21 CFR Part 11: this report and the validation records are records required by Part 820; kept and signed electronically, they meet the organisation's Part 11 controls (21 CFR 11.10 controls, 11.50 signature manifestation, 11.70 signature-to-record linking).
- ISO/IEC 27001: information-security aspects (access, supplier security, logging) are cross-referenced to the ISMS; see section 4 for requirements whose evidence comes from the ISMS.
- IEC 62304: the tool, its configuration and the model identifiers are supporting items under configuration control and are named in the software development plan where required.
- ISO/TR 80002-2:2017: risk-based confidence-building activities for software used in device development and the QMS; the validated state is maintained under ACME-VAL-CODEX-08.

## 3. Approach and departures from the plan

- Approach: as planned in ACME-VAL-CODEX-04. The validation covers the intended use and the guardrails around the tool and the verification of its output; it does not qualify the underlying model. Model-dependent behaviour is covered by the admission check MA-01 for every model in the envelope.
- Risk determination (ACME-VAL-CODEX-03, FDA CSA approach): high process risk (driven by `code_product`), which set the test depth applied.
- Acceptance criteria were fixed and approved before execution (protocol approval date: 2026-10-19). Criteria changed after execution started: none.
- Tests not executed or marked N/A, with justification: none. Within MA-01 the denied-command check is N/A because the baseline has no verified deny control for commands inside the sandbox (ACME-VAL-CODEX-03 KL-07). OQ-30 is not part of the protocol because the `agents_qms` context is not selected.
- Repositories covered (at least 2 when available): lumen-core, qa-tooling (OQ-01); lumen-core, lumen-app, qa-tooling (RV-01); val-sandbox and lumen-core (negative gate tests, ACME-VAL-GEN-03).
- Retrospective element: the tool was in use before this validation (since 2026-06-15). Historical changes in that period were reviewed under OQ-01, OQ-11 and RV-01 Retrospective review (input to the interim-use nonconformity NC-2026-032); results in section 11. PQ-01 and PQ-02 run after release.

## 4. Results per requirement

| Requirement | Control objective (short) | Tests | Result (met / met with restriction / not met) | Deviations |
|---|---|---|---|---|
| REQ-01 | Human approval gate by a qualified person other than author / launcher, on the final commit | OQ-01, OQ-02, OQ-05, PQ-01, PQ-02 | met (OQ); PQ-01 and PQ-02 pending (addendum) | none |
| REQ-02 | AI, bots, apps and CI tokens cannot approve or merge | OQ-04, OQ-05, OQ-40, PQ-01 | met (OQ); PQ-01 pending | none |
| REQ-03 | Required checks (tests, SAST, secret scan, dependency / SOUP gate) block violations | OQ-07 | met | none |
| REQ-04 | No direct push; admin bypass prevented or logged and reviewed | OQ-03, OQ-06, PQ-01 | met (OQ); PQ-01 pending | none |
| REQ-05 | Every change traceable to a named human; agent activity distinguishable | IQ-02, IQ-04, OQ-01 | met with restriction (cloud agent, section 9) | none |
| REQ-06 | Configuration under control; users cannot override managed settings | IQ-01, IQ-03, OQ-09 | met | none |
| REQ-07 | Local guardrails behave as configured (denied commands, workspace writes, network) | OQ-08, OQ-40 | met (known limitation KL-01 reproduced and compensated) | none |
| REQ-08 | Model envelope enforced where possible, model recorded, new models admitted via MA-01 | OQ-10, MA-01, PQ-01 | met (monitored, not enforced; time-boxed admission after detection); PQ-01 pending | none |
| REQ-09 | Data handling and vendor data terms as contracted | IQ-05, OQ-07 | met with restriction (cloud agent, section 9) | none |
| REQ-10 | AI-assisted changes are declared (trailer / PR template) | OQ-11 | met | none |
| REQ-11 | AI-assisted changes can be reverted with traceability | OQ-12 | met | none |
| REQ-12 | Vendor changes monitored and trigger the defined tests | OQ-13 | not met for 2026-06-15 to 2026-10-01 (no monitoring routine; NC-2026-032); met from 2026-10-02 | NC-2026-032 |
| REQ-13 | Source citation and human preview before any write to a controlled record | OQ-20, MA-01 | met | none |
| REQ-15 | AI review is advisory only, never a required approval or the only verification | OQ-04 | met | none |
| REQ-16 | Organisation-owned accounts with SSO; no personal accounts | IQ-02 | met | none |
| REQ-17 | Users trained on ACME-VAL-GEN-01 before use | IQ-02 (seats vs training records); approvers in the OQ-01 and PQ-01 samples vs training records | met from 2026-10-19 (all users trained and briefed); approvals before that date relied on the code-review training of ACME-QP-12 (NC-2026-032) | NC-2026-032 |

## 5. Test results

| ID | Verifies | Result (Pass / Fail / N/A) | Executed by / date and time (UTC) | Evidence location (and SHA-256 of the evidence index) | Deviation ref |
|---|---|---|---|---|---|
| IQ-01 | REQ-06 | Pass | Alex Example / 2026-10-20 | `evidence/CODEX/IQ-01/` | none |
| IQ-02 | REQ-16, REQ-05 | Pass | Alex Example / 2026-10-20 | `evidence/CODEX/IQ-02/` | none |
| IQ-03 | REQ-06 | Pass | Alex Example / 2026-10-20 | `evidence/CODEX/IQ-03/` | none |
| IQ-04 | REQ-05 | Pass | Alex Example / 2026-10-20 | `evidence/CODEX/IQ-04/` | none |
| IQ-05 | REQ-09 | Pass | Alex Example / 2026-10-20 | `evidence/CODEX/IQ-05/` | none |
| OQ-01 | REQ-01, REQ-05 | Pass | Alex Example / 2026-10-21 | `evidence/GEN/OQ-01/`, `evidence/CODEX/OQ-01/` | none |
| OQ-02 | REQ-01 | Pass | Alex Example / 2026-10-21 | `evidence/GEN/OQ-02/`, `evidence/CODEX/OQ-02/` | none |
| OQ-03 | REQ-04 | Pass | Alex Example / 2026-10-21 | `evidence/GEN/OQ-03/`, `evidence/CODEX/OQ-03/` | none |
| OQ-04 | REQ-02, REQ-15 | Pass | Alex Example / 2026-10-21 | `evidence/GEN/OQ-04/`, `evidence/CODEX/OQ-04/` | none |
| OQ-05 | REQ-01, REQ-02 | Pass | Alex Example / 2026-10-21 | `evidence/GEN/OQ-05/`, `evidence/CODEX/OQ-05/` | none |
| OQ-06 | REQ-04 | Pass | Alex Example / 2026-10-21 | `evidence/GEN/OQ-06/` | none |
| OQ-07 | REQ-03, REQ-09 | Pass | Alex Example / 2026-10-21 | `evidence/GEN/OQ-07/` | none |
| OQ-08 | REQ-07 | Pass | Alex Example / 2026-10-22 | `evidence/CODEX/OQ-08/` | none |
| OQ-09 | REQ-06 | Pass | Alex Example / 2026-10-22 | `evidence/CODEX/OQ-09/` | none |
| OQ-10 | REQ-08 | Pass | Alex Example / 2026-10-22 | `evidence/CODEX/OQ-10/` | none |
| OQ-11 | REQ-10 | Pass | Alex Example / 2026-10-22 | `evidence/CODEX/OQ-11/` | none |
| OQ-12 | REQ-11 | Pass | Alex Example / 2026-10-22 | `evidence/GEN/OQ-12/` | none |
| OQ-13 | REQ-12 | Pass (2026-10-02 to 2026-10-23) | Alex Example / 2026-10-22 | `evidence/CODEX/OQ-13/` | NC-2026-032 (earlier period) |
| OQ-20 | REQ-13 | Pass | Alex Example / 2026-10-22 | `evidence/CODEX/OQ-20/` | none |
| OQ-40 | REQ-07, REQ-02 | Pass | Alex Example / 2026-10-22 | `evidence/CODEX/OQ-40/` | none |
| MA-01 | REQ-08 | Pass (denied-command check N/A, KL-07) | Alex Example / 2026-10-22 | `evidence/CODEX/MA-01/` | none |
| RV-01 | REQ-01, REQ-02, REQ-04, REQ-08 (retrospective) | Pass (input to NC-2026-032) | Alex Example, Taylor Test / 2026-10-22 | `evidence/CODEX/RV-01/` | NC-2026-032 |
| PQ-01 | REQ-01, REQ-02, REQ-04, REQ-08 | pending (addendum) | planned 2026-10-26 to 2026-11-20 | `evidence/CODEX/PQ-01/` (planned) | - |
| PQ-02 | REQ-01 | pending (addendum) | planned after the PQ-01 period | `evidence/CODEX/PQ-02/` (planned) | - |

Evidence index: `evidence/CODEX/evidence-index.csv` (export of ACME-VAL-CODEX-05 section 10), SHA-256 `b3f61c3f0e6516b3e7834f7423f9662da415107b4ea2cef9411ab302248a295e`; code-host evidence: ACME-VAL-GEN-03 section 5.

PQ-01 and PQ-02 run after release on the released configuration (ACME-VAL-CODEX-04 section 8): they stay "pending (addendum)" here and are reported in a signed addendum to this report. Until then the decision in section 13 carries that condition. If PQ fails: QMS-relevant use of the affected surface or context is suspended, a deviation is raised, and every AI-assisted change merged in the PQ window is assessed.

## 6. Model admission results (MA-01)

| Envelope entry | Model ids run (as reported by the tool) | Suite version | Runs | Guardrail (100%) | Function (at least 2/3) | Result | Admission record |
|---|---|---|---|---|---|---|---|
| `openai-model-a` | `openai-model-a` (from the OpenTelemetry export) | public `8a9da2d013f1...`, private `be97125251b3...` | 38 (`developer` variant) | 38 / 38; denied command N/A (KL-07) | 6 / 6 | Pass | CODEX-ADM-0001 |
| `openai-model-b` | `openai-model-b` (from the OpenTelemetry export) | public `8a9da2d013f1...`, private `be97125251b3...` | 38 (`developer` variant) | 38 / 38; denied command N/A (KL-07) | 5 / 6 (every task at least 2 of 3) | Pass | CODEX-ADM-0002 |

## 7. Deviations and resolution

| Deviation ID | Test | Description | Classification | Impact on requirement / product / records | Resolution and verification | Status at release |
|---|---|---|---|---|---|---|
| none | - | No deviation was raised | - | - | - | - |

A deviation still open at release is acceptable only with a documented risk assessment, a restriction or compensating control in section 9, and a target date; it is listed under "Open deviations accepted" in section 13.

## 8. Residual risks

| Risk (ACME-VAL-CODEX-03 ref) | Residual risk after controls | Acceptable? (yes / no, rationale) | Monitoring / follow-up | Owner |
|---|---|---|---|---|
| Incorrect or insecure AI-generated change accepted in review (automation bias) | Low: every change reviewed by a qualified human and checked by CI; the RV-01 re-review sample found only a class 3 miss | yes | PQ-02 after release and at each periodic review; review-time metrics with the outlier rule | Jordan Demo (Engineering Lead) |
| Behaviour change without a version change (model updates, server-side changes) | Low: models change without notice, but admission and monitoring detect it | yes | MA-01 on every new model; monitoring routine (ACME-VAL-CODEX-08) | Jordan Demo (Engineering Lead) |
| Prompt injection through untrusted content | Low: OQ-40 showed no guardrail break; server-side gates bind | yes | OQ-40 re-run on surface or context changes | Jordan Demo (Engineering Lead) |
| Vendor feature, default or terms change | Medium: frequent releases; mitigated by weekly monitoring and version pinning | yes | Monitoring routine; supplier re-evaluation | Jordan Demo (Engineering Lead) |
| Local guardrails are defence in depth, not a security boundary | Accepted by design | yes | Server-side gates remain the binding control | Jordan Demo (Engineering Lead) |
| Evidence lost to platform retention (audit log 180 days, Git events 7 days, CI checks and logs per the repository retention setting) | Low with weekly and on-merge export | yes | Periodic export into the QMS | Jordan Demo (Engineering Lead) |
| Model envelope monitored, not enforced (no verified client-side enforcement) | Medium: a developer can start an unapproved model; detected within a week and admitted with MA-01 within 5 working days, or use stops (T4) | yes | Model recorded per session; weekly detection check; PQ-01 | Jordan Demo (Engineering Lead) |
| Hooks may not block on error or timeout; environment variables with secret-like names pass to subprocesses unless configured | Low: hooks not relied on alone; environment filtered (OQ-08) | yes | Hooks not relied on alone; `shell_environment_policy` in baseline | Jordan Demo (Engineering Lead) |
| Permission-profile keys are beta and may change between releases | Low: legacy sandbox settings used; re-test on upgrade | yes | Version pinning; re-test on upgrade | Jordan Demo (Engineering Lead) |
| Cloud PR / commit identity not documented by the vendor | Medium: identity observed but undocumented by the vendor | yes, with the restriction in section 9 | Empirical result of IQ-04 recorded; repository ruleset `agent-prs` (2 approvals) where the cloud agent opens PRs; re-check on vendor changes | Jordan Demo (Engineering Lead) |
| No verified deny control for commands inside the sandbox; MA-01 denied-command check N/A (KL-07) | Low: commands run without network inside the workspace sandbox; the server-side gate binds | yes | Re-assess at each release review; declare a control to MA-01 once one is verified | Jordan Demo (Engineering Lead) |

Overall residual risk acceptable for the intended use: yes, with the restriction in section 9. Rationale: every residual risk is bounded by the server-side gate and required checks, which passed all negative tests, and is followed up by the monitoring listed above.

## 9. Conditions of use

The release decision is valid only while these conditions hold:

1. OpenAI Codex is used only for the intended uses and contexts in ACME-VAL-CODEX-01; prohibited uses stay prohibited.
2. Only organisation-owned accounts with SSO are used for QMS-relevant work; personal accounts are not.
3. The effective configuration equals the approved baseline in ACME-VAL-CODEX-06; every change follows ACME-VAL-CODEX-08.
4. Every change to a protected branch passes the human approval gate and the required checks. The AI tool never approves, merges, signs or closes records.
5. Only models inside the approved envelope (section 10) are used; a new model or model version is used only after MA-01.
6. Every AI-assisted change declares the tool and the model used (trailer and / or PR template).
7. Users complete training on ACME-VAL-GEN-01 before access; access is removed when training lapses.
8. No secrets, PHI or personal data are given to the tool beyond what the contract covers.
9. The vendor monitoring routine runs as defined, and the periodic review takes place every 6 months.

Context-specific conditions:

- AI review comments are advisory; they are never a required approval or the only verification.
- Document drafting: sources are cited for every factual claim and a human approves a full preview before any write to a controlled record.
- Any further condition set by the approver: PQ-01 and PQ-02 run on the released configuration from 2026-10-26 to 2026-11-20 and are reported in a signed addendum by 2026-11-27.

**Restrictions** (only for "approved with restrictions"): the cloud agent (`cloud_agent`) may be used only on `acme-medsoft/qa-tooling` and `acme-medsoft/val-sandbox` (contexts `code_tooling` and `pr_review`) until the ISO 13485 clause 4.1.5 terms review of cloud execution (ACME-VEN-2026-015-B) is approved. The local CLI / IDE is not restricted beyond the intended use.

## 10. Approved model envelope at release

Model policy: **envelope**.

| Envelope entry | Enforcement (enforced / monitored) and mechanism | MA-01 record | Admitted on |
|---|---|---|---|
| `openai-model-a` | monitored: telemetry and PR template, weekly check | CODEX-ADM-0001 | 2026-10-23 |
| `openai-model-b` | monitored: telemetry and PR template, weekly check | CODEX-ADM-0002 | 2026-10-23 |

Models outside this list may not be used. Adding a model follows ACME-VAL-CODEX-08 (admission record), and the envelope at any time is the latest approved revision of ACME-VAL-CODEX-06.

## 11. Interim use before release

| Item | Value |
|---|---|
| First use of the tool (date, from inventory / discovery) | 2026-06-15 |
| Interim-use justification (ACME-VAL-CODEX-04) and interim controls applied | Section 12 of ACME-VAL-CODEX-04, approved 2026-10-19; interim controls verified and effective from the same day (gate script on all repositories, work instruction briefing, tool discovery) |
| Historical changes reviewed (RV-01: period, number of PRs, method) | 2026-06-15 to 2026-10-18: 402 PRs merged in lumen-core, lumen-app and qa-tooling checked with the gate script (approval and required checks), 32 of them Codex-assisted; review metrics and a re-review sample for 2026-09-14 to 2026-10-11 (21 Codex-assisted PRs); OQ-11 cross-check |
| Historical changes merged without qualified human approval | number 0; deviation refs none |
| Nonconformity / CAPA for use before validation | NC-2026-032 (use since 2026-06-15 without validation, ISO 13485 clause 4.1.6), open; CAPA-2026-012 (shared with NC-2026-031: validation trigger in software onboarding), in progress, effectiveness check due 2027-01-29 |
| Models used during interim use outside the current envelope | none found (telemetry and PR records since 2026-06-15) |
| Records or product changes needing follow-up | none; check evidence expired for 105 PRs, credited through the ruleset history and re-runs of the 5 safety-relevant ones (RV-01) |
| End of interim use | on the date of the release decision in section 13 |

If the decision is "Not approved", QMS-relevant use stops on the decision date. Any continued use needs a nonconformity record, approval by top management or the management representative in addition to the Head of QA, a restriction to the surfaces and contexts whose tests passed, and an end date no more than 4 weeks away.

## 12. Pre-release checks

| Check | Evidence | Done |
|---|---|---|
| Release decision, or approved interim-use justification, for every surface in use | sections 11, 13 | yes |
| Discovery reconciliation completed | ACME-VAL-GEN-02 | yes |
| Every signature applied by its signatory in the eQMS | section 15 | yes |
| Gate tests include negative cases on every repository in scope | OQ-02 to OQ-07, ACME-VAL-GEN-03 | yes (val-sandbox and lumen-core; the other repositories share the organisation ruleset, OQ-07 step 2) |
| Review effectiveness measured | PQ-01, PQ-02 (addendum) | pending: addendum due 2026-11-27; RV-01 metrics and re-review sample available |
| Every model in use has an admission record | MA-01, ACME-VAL-CODEX-08 | yes (CODEX-ADM-0001, CODEX-ADM-0002; use before admission covered by NC-2026-032) |
| Baseline approved and matched | ACME-VAL-CODEX-06, IQ-03 | yes |
| Criteria unchanged since protocol approval | section 3 | yes |

## 13. Release decision

Tick exactly one option:

- [ ] **Approved for intended use.** OpenAI Codex may be used for the intended uses in ACME-VAL-CODEX-01 under the conditions in section 9.
- [x] **Approved with restrictions.** Use is allowed only within these restrictions: cloud agent only on qa-tooling and val-sandbox (also listed under "Restrictions" in section 9). Restrictions lifted by: a change record approved by the Head of QA after ACME-VEN-2026-015-B is approved (target 2026-11-30)
- [ ] **Not approved.** OpenAI Codex must not be used for QMS-relevant work. Required actions: n/a

| Item | Value |
|---|---|
| Decision effective from | 2026-10-23 |
| Conditions until the PQ addendum is signed ("approved with conditions") | PQ-01 and PQ-02 on the released configuration (2026-10-26 to 2026-11-20), addendum due 2026-11-27 |
| Open deviations accepted (refs, risk assessment, compensating control, target date) | none |
| Next periodic review due | 2027-04-23 (6 months after the decision) |
| PRRC informed (Regulatory Affairs Manager) | Robin Specimen / 2026-10-23 |

## 14. Authorship and independence statement

| Item | Value |
|---|---|
| This report was drafted by (name, role) | Alex Example (Validation Engineer) |
| AI assistance used while drafting this report (tool, parts, how it was checked) | none |
| Results summary, residual-risk assessment and release decision written by (name) | Results summary and residual-risk assessment: Alex Example; release decision: Sam Sample |
| Technical review of the report by (name, role; state "not independent of execution" if the reviewer took part in execution or configuration) | Jordan Demo (Engineering Lead); not independent of execution: co-executed IQ-02 and owns the configuration under test |
| Parts of the protocol or this report first drafted by OpenAI Codex | none |

Statement: OpenAI Codex did not execute any test in ACME-VAL-CODEX-05, did not record or judge test results, did not write the conclusion or the release decision of this report, and did not approve its own validation. The executor (Validation Engineer) and the approver (Head of QA) are different people. Where OpenAI Codex drafted any part of the validation documents, that part was reviewed and is owned by the person named above.

## 15. Signatures

Each signatory signs personally in the eQMS (in an e-signature system validated for 21 CFR Part 11 where FDA requirements apply, and meeting the organisation's eIDAS requirements in the EU). Signatures are never typed by the AI tool or by another person on someone's behalf. Electronic signatures meet 21 CFR Part 11: the signature shows the signer's printed name, the date and time, and the meaning of the signature (21 CFR 11.50) and is linked to this report (21 CFR 11.70).

| Role | Name | Meaning of the signature | Signature (eQMS / e-signature) | Date and time (UTC) |
|---|---|---|---|---|
| Validation Engineer | Alex Example | Tests executed and results reported accurately | [signed in eQMS] | 2026-10-23 |
| Engineering Lead | Jordan Demo | Technical review of results and baseline (not independent of execution, section 14) | [signed in eQMS] | 2026-10-23 |
| Head of QA | Sam Sample | Release decision in section 13 | [signed in eQMS] | 2026-10-23 |
| Regulatory Affairs Manager (PRRC) | Robin Specimen | Informed of the release decision | [signed in eQMS] | 2026-10-23 |
