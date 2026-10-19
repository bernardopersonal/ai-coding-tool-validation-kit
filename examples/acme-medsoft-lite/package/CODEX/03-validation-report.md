> FICTIONAL EXAMPLE, invented for illustration only. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are made up to show what an executed lite package looks like. Model ids are placeholders. Each person signs in the eQMS, shown here only as "[signed in eQMS]".

# ACME-VAL-CODEX-L03 Validation report: OpenAI Codex

| Field | Value |
|---|---|
| Document ID, version | ACME-VAL-CODEX-L03, 1.0 (approved 2026-10-23), lite profile |
| Tool / vendor | OpenAI Codex / OpenAI |
| Drafted / technical review / release decision (roles) | Validation Engineer / Engineering Lead / Head of QA |
| Organisation, date | Acme MedSoft, 2026-10-19 |

> Generated with the AI Coding Tool Validation Kit 0.2.0, lite profile. Complete every `[fill in]` after execution.

## 1. Summary

| Item | Value |
|---|---|
| Surfaces; contexts | `local_cli_ide`; `code_product` `code_tooling` `pr_review` (not used with this tool) |
| Plan and record versions executed, amendments | ACME-VAL-CODEX-L01 1.0 and ACME-VAL-CODEX-L02 1.0 (records in 1.1); no amendments |
| Profile decision (ACME-VAL-CODEX-L01 section 2) | Lite: none of L1 to L9 applies (Head of QA, 2026-10-20) |
| Tool version(s) validated; IQ-03 baseline SHA-256 | codex-cli 0.163.0; `requirements.toml` `4e0d2b7a91c3...`, capture files in the evidence index of ACME-VAL-CODEX-L02 |
| Execution period (UTC); repositories | 2026-10-21 08:15 to 2026-10-22 16:45; lumen-core, lumen-app, qa-tooling, val-sandbox |
| Tests executed / passed / failed / N/A | 10 records (12 test IDs) before release / 10 / 0 / 0 (OQ-04 steps 2 and 3 and OQ-05 step 3 N/A with justification); PQ-01 and PQ-02 pending |

Summary of results (author named in section 5): all ten pre-release test records met their acceptance criteria. The code-host gates, executed once for both tools, refused every unapproved, direct and admin merge or push; OpenAI Codex's own merge and push attempts failed in the sandbox or were stopped by command rules and the server. No Codex identity exists on the code host that could approve. The sandbox, network restriction and admin-enforced requirements held, with the accepted limitation KL-01 reproduced. A model outside the list was accepted by the client (no enforcement), so the list is monitored only. `openai-model-a` passed MA-01, with the denied-command check recorded N/A (KL-07). No deviation.

Basis: ISO 13485:2016 clause 4.1.6, records under clause 4.2.5; 21 CFR 820.10 (QMSR, incorporating ISO 13485) and the record content of the FDA CSA guidance; ISO/TR 80002-2:2017. IEC 62304 (clauses 5.1.4, 5.1.10, 8.1): tool, configuration and model ids are configuration items, named in the software development plan where required.

## 2. Results per requirement

Result per requirement of ACME-VAL-CODEX-L01 section 6 (met / restricted / not met; deviations):

- REQ-01: met; PQ-01 and PQ-02 pending
- REQ-02: met; PQ-01 pending
- REQ-03: met
- REQ-04: met; PQ-01 pending
- REQ-05: met
- REQ-06: met
- REQ-07: met; KL-01 as accepted
- REQ-08: restricted: monitored only (OQ-10; weekly detection, grace period of ACME-VAL-CODEX-L01 section 8); PQ-01 pending
- REQ-09: met
- REQ-10: met (9 of 9 declared); PQ-01 pending
- REQ-15: met: no Codex review identity exists
- REQ-16: met
- REQ-17: met from 2026-10-19; earlier approvals relied on the code-review training then in force (rule of ACME-VAL-CODEX-L01 section 9; NC-2026-042)

Per-test results: ACME-VAL-CODEX-L02; PQ-01 and PQ-02 "pending" until the signed addendum. Deviations (ID, class, resolution, status): none; an open one needs a risk assessment, restriction and target date.

Residual risk: automation bias (PQ-01 outliers, PQ-02), silent model changes (MA-01), vendor changes (section 6), local guardrails as defence in depth, GitHub evidence retention (export); accepted limitations KL-01, KL-04, KL-06, KL-07 (ACME-VAL-CODEX-L01 section 5); the model list is monitored only. Acceptable: yes, because the binding controls are the server-side gate and the required checks, both shown to refuse violations, the sandbox has no network access, and a model outside the list is detected weekly and is a deviation with review of its changes.

## 3. Approved model list at release

Model policy **envelope**; only admitted ids are used, new ones only under ACME-VAL-CODEX-L01 section 8.

| Approved entry | Enforced (OQ-10 passed) or monitored | MA-01 admission record, date |
|---|---|---|
| `openai-model-a` | Monitored, not enforced (OQ-10: an outside id was accepted): weekly extract of `codex.conversation_starts` and PR template declarations; 5 working days grace period for MA-01, changes reviewed | CODEX-ADM-0001, 2026-10-22 |

## 4. Release decision

Conditions: intended use of ACME-VAL-CODEX-L01 only; organisation SSO accounts; baseline configuration, changed only under section 6; human gate and required checks on every protected-branch change, the AI never approving, merging, signing or closing records; admitted models only; changes declared; trained users; no secrets or personal data beyond the contract. Further: local CLI only (no cloud tasks, no GitHub connector); second senior review of every AI-assisted change to safety-related items; signed PQ-01 and PQ-02 addendum.

- [x] **Approved with conditions** for the intended use: PQ-01 and PQ-02 addendum due 2026-11-27; "approved for intended use" once it is signed
- [ ] **Approved with restrictions:** not applicable (the local-CLI-only scope is the intended use)
- [ ] **Not approved:** no QMS-relevant use from the decision date (continued use needs a nonconformity, top-management approval and an end date); actions not applicable

Effective from 2026-10-23; accepted open deviations none; interim use (look-back, NC / CAPA) since 2026-06-15, NC-2026-042 and CAPA-2026-015, ends on the decision date; next periodic review October 2027 (12 months).

## 5. Authorship and signatures

Drafted by Alex Example (Validation Engineer); summary, residual risk and decision by Alex Example (summary and residual risk) and Sam Sample (decision); AI assistance: none. OpenAI Codex did not execute or judge tests, write the conclusion or approve its validation, and the AI tool did not draft the conclusion without independent review; executor and approver differ. Each signatory signs personally in the eQMS; signatures show name, date and time and meaning, linked to this report (21 CFR 11.50, 11.70).

| Role | Name | Meaning | Signature | Date (UTC) |
|---|---|---|---|---|
| Validation Engineer | Alex Example | Tests executed and reported accurately | [signed in eQMS] | 2026-10-23 08:50 |
| Engineering Lead | Jordan Demo | Technical review | [signed in eQMS] | 2026-10-23 09:40 |
| Head of QA | Sam Sample | Release decision | [signed in eQMS] | 2026-10-23 10:20 |

## 6. Change triggers and revalidation

Subset of the full profile's T1 to T19 (same numbers): action required before further use, criteria as in ACME-VAL-CODEX-L02; anything else: normal change control.

- T1 new id matching a pre-authorised pattern: MA-01, admission record (section 7)
- T3 other new model id, family or tier: MA-01, OQ-08, OQ-10
- T4, T5 model used unadmitted; MA-01 fails: stop its use, review its changes, deviation; MA-01 (T4); OQ-08, OQ-09 if a guardrail failed
- T7a client version, no guardrail-relevant release note: IQ-03 `--compare`; approved `checks/client_regression.py` probes
- T7 guardrail-relevant or major release: impact assessment, IQ-03, OQ-08 to OQ-10
- T8a, T8b managed configuration change; instruction files only: IQ-03, OQ-09, test of the control; code-owner reviewed PR
- T9, T10 new surface; new context of use: plan update, IQ-03, OQ-04 or OQ-08, ACME-VAL-CODEX-L01 section 2 again
- T11, T12 new repository; code-host rule change: OQ-02 and OQ-03 there; OQ-02 to OQ-07
- T13, T14 vendor terms or plan change; account, workspace or SSO change: supplier re-evaluation; REQ-16 check, OQ-04 and OQ-05 with the new identities
- T15, T16 incident or deviation; vendor drops a feature a control relies on: investigation, CAPA; impact assessment, re-test of the control
- T17, T18 new vendor or tool; retirement: new initial validation; retirement record (evidence archived, shared `evidence/GEN/` records moved to a remaining tool, seats and keys revoked)
- T19 every 3 months: MA-01
- Periodic review every 12 months: ACME-VAL-GEN-L02, IQ-03 `--compare`, OQ-01 sample, models, seats against training

The Engineering Lead screens vendor releases at least weekly and logs each screening (vendor monitoring log ACME-ENG-LOG-07, started 2026-10-19).

## 7. Admission record (copy for each new model id)

| Field | Value |
|---|---|
| Record CODEX-ADM-0001: model id as reported; matched pattern; first seen; used before (deviation) | `openai-model-a`; approved entry itself (initial validation); 2026-06-15; yes, interim use under NC-2026-042 |
| Tool version; IQ-03 SHA-256 unchanged; release notes screened (log) | codex-cli 0.163.0; yes (capture of 2026-10-21); ACME-ENG-LOG-07 entry of 2026-10-19 |
| Suite SHA-256, tasks, runs; results: guardrail (every run), function (2 of 3); evidence SHA-256 | `271a22d74c0f...`, the four tasks of ACME-VAL-CODEX-L01 section 8, 3 runs; guardrail 12 of 12 (denied-command check N/A, KL-07), function 3 of 3; `b4407f0d45d1222e...` |
| Decision (admitted / not); executed by; approved by the Head of QA (eQMS, date) | Admitted; Alex Example; Sam Sample, [signed in eQMS] 2026-10-23 |

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-19 | Alex Example | Initial draft (kit 0.2.0, lite) |
| 1.0 | 2026-10-23 | Alex Example | Results, release decision |
