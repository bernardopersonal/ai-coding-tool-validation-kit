> FICTIONAL EXAMPLE, invented for illustration only. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are made up to show what an executed lite package looks like. Model ids are placeholders. Each person signs in the eQMS, shown here only as "[signed in eQMS]".

# ACME-VAL-CODEX-L01 Validation plan: OpenAI Codex

| Field | Value |
|---|---|
| Document ID, version | ACME-VAL-CODEX-L01, 1.0 (approved 2026-10-20), lite profile |
| Tool / vendor | OpenAI Codex / OpenAI |
| Owner / approver (roles) | Validation Engineer / Head of QA |
| Organisation, date | Acme MedSoft, 2026-10-19 |
| Product context | Class II SaMD (FDA 510(k)); EU MDR Class IIa planned |

> Generated with the AI Coding Tool Validation Kit 0.2.0, lite profile. Complete every `[fill in]`. Approved with ACME-VAL-CODEX-L02 **before** the first test, by the approver personally in the eQMS.

## 1. Purpose and profile

The **lite profile** is the risk-proportionate minimum where every AI output is independently verified downstream (qualified human review, required CI) before it takes effect (ISO 13485:2016 clause 4.1.6; FDA CSA; GAMP 5 Second Edition appendix D9). Requirement and test IDs and commands are those of the full profile; under a shared ID lite criteria equal or exceed full, and full adds tests and steps (upgrade: kit `docs/lite-vs-full.md`). Validated: tool, vendor, surface, context of use; models via the approved list and MA-01.

Software validation procedure clause adopting lite, L1 to L9 and section 8: ACME-QP-04 Validation of QMS and development software, clauses 6.3 (lite profile, L1 to L9) and 6.4 (predetermined change protocols).

## 2. When lite is not enough

| # | Condition (any "yes": full; hard stops cannot be overridden) | Applies? Why |
|---|---|---|
| L1 | Hard stop: pinned model policy (AI output is a control or evidence) | no (envelope) |
| L2 | Hard stop: QMS agents, or any agent writing to QMS systems outside the code-host gate | no (none declared): no MCP servers in `config.toml` or `requirements.toml`, no Codex connector, and no token for the eQMS, the issue tracker or the document system on developer machines |
| L3 | `doc_drafting` without independent source check of each draft | no (not selected) |
| L4 | GxP in scope with high-impact use | no (not selected) |
| L5 | Section 5 determination "high process risk" | no: not high process risk for every context, see section 5 |
| L6 | Notified body, FDA or customer expects more depth | no: as recorded in ACME-VAL-CLAUDE-L01 section 2 (ACME-QA-CORR-2026-088) |
| L7 | Audit findings on this tool or AI tool validation | no: none to date; the use before validation is handled as NC-2026-042 (section 9) |
| L8 | Hard stop: AI output (e.g. tests) used as verification evidence or QMS record without review of its adequacy | no: as for Claude Code (ACME-VAL-CLAUDE-L01 section 2): AI-written tests only through the reviewed PR with the ACME-QP-12 adequacy question; no verification evidence or QMS record comes from the tool |
| L9 | Hard stop: agent with write credentials or secrets beyond the PR path reads untrusted content | no: local CLI only, under the developer's own identity, with `network_access = false`; no cloud tasks, no GitHub connector, no MCP servers |

Decision: **lite**, by the Head of QA; re-checked on T9, T10, T14 and periodic review. A cloud agent surface or a Codex PR integration is trigger T9 and needs a new decision on L9.

## 3. Inventory

| Item | Value |
|---|---|
| Tool type, ID; surfaces | `codex`, CODEX; `local_cli_ide`  |
| Plan, contract / DPA, supplier evaluation | Enterprise workspace; contract ACME-PUR-2026-019 and DPA of 2026-06-01; supplier evaluation ACME-VEN-2026-015 (approved supplier, ISO 13485:2016 clause 7.4) |
| Organisation workspace, SSO, admins (REQ-16) | Workspace "Acme MedSoft", SAML single sign-on; `allowed_login_methods = ["chatgpt"]` and `allowed_chatgpt_workspaces` set to the organisation workspace in `requirements.toml`; admins Jordan Demo and Casey Admin |
| Seats reconciled with identity provider, training records (REQ-16, REQ-17) | 2026-10-19: 6 seats, 6 active employees, no external or personal accounts; 6 of 6 trained on ACME-VAL-GEN-L01 on 2026-10-19 (TR-2026-315 to TR-2026-320) |
| Validated version, update control | codex-cli 0.163.0; endpoint-managed package pinned to 0.163.0; `check_for_update_on_startup = false` in `requirements.toml`; raised only by change record (trigger T7a or T7) |
| Model policy, approved models | envelope: `openai-model-a`  |
| Vendor data terms: retention, training, region, source (REQ-09) | Workspace retention set by the workspace owner (value in the IQ-03 evidence); not used for training (enterprise workspace default); no residency commitment (accepted in DPIA-2026-03); source: ACME-PUR-2026-019 as of 2026-10-13 |
| GAMP 5 category | 4 (configured product): behaviour depends on `requirements.toml`, `config.toml`, command rules and `AGENTS.md` |
| Software development / configuration management plan; IEC 62304 safety class | Software development plan ACME-SDP-LUMEN revision 4, section 8; configuration management plan ACME-CMP-01; software safety class B |
| Status | In use since 2026-06-15 (section 9) |

Version: `codex --version`, `codex doctor`. In CI pin `openai/codex-action` and set `codex-version` (blank installs the latest CLI). No CI surface is in scope.

## 4. Intended use

The AI never approves, merges, signs or closes records; the responsible human approves under their own identity.

| Context | Users, repositories or systems; approver |
|---|---|
| `code_product` | Product developers (trained); `acme-medsoft/lumen-core`, `acme-medsoft/lumen-app`, branch `main`; a qualified reviewer other than author and launcher (ACME-QP-12), plus the second senior review for safety-related items |
| `code_tooling` | Developers and QA engineers (trained); `acme-medsoft/qa-tooling`, branch `main`; a qualified reviewer other than author and launcher |
| `pr_review` | Not used with OpenAI Codex: no Codex app or connector is installed on the GitHub organisation (ACME-VAL-GEN-L02, checks C1-C3). Advisory PR review is done only by Claude Code (ACME-VAL-CLAUDE-L01) |

Not intended: other contexts, surfaces or models; the AI as reviewer of record or validating itself; personal accounts. Rules: ACME-VAL-GEN-L01. Cloud tasks and the GitHub connector are not approved.

## 5. Risk determination

FDA CSA: **high process risk** when a tool failure may cause a quality problem that foreseeably compromises safety.
Crediting the tested gate and CI as independent verification is an interpretation: quote the CSA risk-determination section. The credit holds while PQ-02 passes.

| Context | Suggested | Determination, rationale |
|---|---|---|
| `code_product` | Not high when the tested gate and CI are the verification of record; otherwise high (L5) | **Not high process risk**, same rationale and quoted CSA passage as ACME-VAL-CLAUDE-L01 section 5: approval by a qualified human on the final commit, required checks, second senior review for safety-related items; device verification stays the verification of record. Valid while PQ-02 finds no class 1 miss |
| `code_tooling` | Not high; L8 if it produces QMS records or verification results | **Not high process risk.** `qa-tooling` produces no QMS records or verification results |
| `pr_review` | Not high if REQ-15 holds | **Not high process risk.** Not used with this tool; OQ-04 confirms that no Codex identity can review |

Overall (highest context): **not high process risk**. Known guardrail limitations (verify against the vendor's current documentation):
KL-01 In hooks only an explicit deny blocks. KL-02 Variables named like KEY, SECRET or TOKEN reach spawned commands by default. KL-03 Only `requirements.toml` enforces; `managed_config.toml` gives defaults. KL-04 Model defaults are not enforcement. KL-05 The cloud-task identity is undocumented. KL-06 Vendor logs miss local actions. KL-07 Command rules govern only commands run outside the sandbox.
Accepted before execution, with compensating controls: KL-01 (hooks are not relied on; the binding controls are the server-side gate and the sandbox); KL-07 (the MA-01 denied-command check is N/A; compensated by `network_access = false`, the workspace-write sandbox and the server-side gate, OQ-02 to OQ-06); KL-04 (no client-side model enforcement: "monitored only", section 8); KL-06 (the model per session comes from `codex.conversation_starts` telemetry and the PR template). Closed by configuration and tested in OQ-08: KL-02 (`shell_environment_policy` excludes secrets) and KL-03 (only `requirements.toml` is relied on). KL-05 does not apply (no cloud tasks).

## 6. Applicable requirements (lite subset, abridged)

Verified by (after the colon); "lite:" marks verification in place of a full-only test.

- REQ-01 Approval by a qualified human other than author and agent launcher, on the final commit: OQ-01, OQ-02, OQ-05, PQ-01, PQ-02
- REQ-02 AI, bot, app and CI approvals not counted; AI cannot merge: OQ-04, OQ-05, PQ-01
- REQ-03 Required checks (tests, SAST, secrets, dependency / SOUP) block violations: OQ-07
- REQ-04 No direct push; admin bypass prevented, or logged and reviewed: OQ-03, OQ-06, PQ-01
- REQ-05 Every change traceable to a named human; agent activity distinguishable: OQ-01 (lite: for IQ-02, IQ-04)
- REQ-06 Configuration baselined; managed settings not overridable: IQ-03, OQ-09
- REQ-07 Local guardrails behave as configured: OQ-08
- REQ-08 Approved models only (enforced where possible), recorded per PR, new models via MA-01: OQ-10, MA-01, PQ-01
- REQ-09 No secrets, PHI or personal data beyond contract; vendor terms as contracted: OQ-07 (lite: section 3, for IQ-05)
- REQ-10 AI-assisted changes declared (trailer, PR template): lite: OQ-01, PQ-01, for OQ-11
- REQ-15 AI review advisory only: OQ-04
- REQ-16 Organisation accounts with SSO: lite: section 3, for IQ-02
- REQ-17 Users trained on ACME-VAL-GEN-L01 before use: section 3; OQ-01, PQ-01 approvers

Full profile only: REQ-11 to REQ-14; IQ-01, IQ-02, IQ-04, IQ-05, OQ-11 to OQ-13, OQ-20, OQ-30, OQ-40, RV-01.

## 7. Approach, samples, roles, acceptance

Negative gate tests, server-side binding controls, limited scripted tests, historical samples, automated MA-01; criteria and minimum samples: ACME-VAL-CODEX-L02.

Planned: OQ-01, OQ-10: 3 PRs per repository in lumen-core (at least 1 safety-related), lumen-app and qa-tooling, drawn from the whole period since 2026-06-15, and the model id of each of these 9 PRs; OQ-02 to OQ-07: code-host part shared with Claude Code (`evidence/GEN/`, recorded in ACME-VAL-CLAUDE-L02), Codex agent steps in this record; MA-01: `openai-model-a`; PQ: 2026-10-26 to 2026-11-20 and at least 20 AI-assisted PRs; if fewer than 20 by then, extended until 20 are reached. Sample rule (random, seed recorded): AI-assisted PRs identified by the PR template declaration ("AI-Tool: OpenAI Codex"); the safety-related PR chosen from those touching items classified safety-related in the software development plan; PQ-02 draws 10% of the Codex-assisted PRs merged in the PQ-01 period, at least 5. PQ-01 outlier: approval within 5 minutes of ready-for-review, or without comment, on a diff over 300 lines; reviewed by Jordan Demo (Engineering Lead, qualified reviewer; approver excluded). PQ-02 missed-defect classes: 1 could affect safety, a risk control or a verification result (limit 0); 2 functional or critical coding-rule defect (limit 1); 3 other.

Roles: the Validation Engineer executes and drafts ACME-VAL-CODEX-L03, never approves; the Head of QA approves plan, record, release, admissions and PQ addendum, never executes; the Engineering Lead owns configuration (frozen during execution), change control and vendor monitoring. Minimum team: one engineer, one approver, sandbox test accounts. OpenAI Codex is only the object under test.

Deviation classes: **critical**, a gate or guardrail does not hold (unapproved merge, push or bypass; an AI approval counts; a denied action runs beyond accepted limitations); **major**, any other failed criterion, including guardrail tests IQ-03, OQ-09, OQ-10, MA-01, or a sampled change without qualified approval; **minor**, a record defect changing no result. Critical and major block release of the affected surface or context until corrected and re-tested.

Acceptance: guardrail criteria hold in 100% of cases and runs. Release rests on IQ-03, OQ and MA-01, "approved with conditions" until the signed PQ addendum to ACME-VAL-CODEX-L03, due within 6 weeks; if PQ fails, suspend use and assess merged changes. Evidence store: validation area of the eQMS, linked from the evidence index of ACME-VAL-CODEX-L02; retention per ACME-QP-02 (device lifetime plus 2 years), at least the device lifetime and two years from release (ISO 13485:2016 clause 4.2.5).

## 8. Model change protocol (three tiers)

If the procedure (section 1) forbids predetermined change protocols, model changes follow normal change control.

1. **Initial validation:** MA-01 on every approved model, fixed here (changes by amendment): tasks as in ACME-VAL-CLAUDE-L01 section 8 (`function-fix-failing-test`, `guardrail-denied-command`, `guardrail-no-ci-edit`, `guardrail-protected-paths`; `doc-citation-probe` dropped because `doc_drafting` is out of scope; no private tasks); baseline variants: `developer` (production `requirements.toml` on test VM ACME-VM-SBX-01); 3 runs per task; auxiliary models: none; suite SHA-256 over the sorted per-file SHA-256 of tasks and fixtures, as `run_admission.py --list` prints it: `271a22d74c0f84528b23bc0678543db8127dd3999b7b5a9a4d2f00a60269b4a0` (same suite as Claude Code). MA-01 screens for gross regression only.
2. **Model admission:** a new id matching a pattern below, with tool version and IQ-03 baseline unchanged and no guardrail-relevant item in the screened release notes, needs MA-01 only. Pass: admission record (ACME-VAL-CODEX-L03 section 7) approved by the Head of QA; the exact id joins the monitored list. Repointable ids (`*-latest`, unversioned names) are never admitted.

| Approved entry | Pre-authorised pattern | Excluded |
|---|---|---|
| `openai-model-a` | `openai-model-a-*` (dated versions of the same model) | `*-latest`, preview ids, any id without a date suffix |

3. **Re-baseline:** on the change triggers in ACME-VAL-CODEX-L03. New vendor: new initial validation.

Enforcement: none verified (check the vendor's current documentation): "monitored only".
Weekly detection (extract of the `codex.conversation_starts` telemetry events, then the PR template declarations, reviewed by the Engineering Lead): model ids from telemetry, session logs or vendor exports, then trailers, PR template. Use before admission is a deviation (T4): changes made with the model are reviewed and its use stops, unless a grace period for MA-01 is accepted here: 5 working days from detection for an id that matches a pre-authorised pattern; the deviation is raised and the changes made with the model are reviewed in every case.

## 9. Interim use

Use before validation is a nonconformity (ISO 13485:2016 clause 4.1.6), declared openly.

| Item | Content |
|---|---|
| First known use; contexts, surfaces; why use continues | 2026-06-15 (first invoice; developer interviews during ACME-VAL-GEN-L02). `code_product`, `code_tooling`; local CLI only. Use continues because the look-back below shows every change in the Codex period passed the server-side gate and required checks |
| Interim controls verified before approval: REQ-01 to REQ-04 on every repository, REQ-09, REQ-16, REQ-17 | Evidence `evidence/CODEX/INTERIM/`: the gate-script runs of ACME-VAL-CLAUDE-L01 section 9 (same repositories, cited), seat list against the identity provider, `requirements.toml` login restriction captured, briefing records; effective from 2026-10-19 |
| Restrictions until release | Local CLI only; no cloud tasks, no GitHub connector; no new repositories or models |
| Look-back since first use (gaps go to the nonconformity) | 1. Every protected-branch commit matched to an approved merged PR (`check_github_gates.py --commits-since 2026-01-12`, ACME-VAL-CLAUDE-L01 section 9): no commit outside an approved merged PR since 2026-02-05, so none in the Codex period. 2. Bypass history: audit-log export from 2026-04-22 covers the whole Codex period: no bypass. 3. Models used: `openai-model-a` (inside) in 41 PRs; 3 PRs of June unknown (PR template field added on 2026-07-01, telemetry from 2026-08-01). 4. Product impact: lumen-core 3.3.0 contains Codex-assisted changes, all approved with green checks and verified under design control; no impact found. 5. OQ-01 sample over the whole period; for approvals before ACME-VAL-GEN-L01 was issued (2026-10-19), the training that counts is the ACME-QP-12 code-review training then in force |
| ACME-VAL-GEN-L02 executed; release decision deadline | Executed 2026-10-19; release decision by 2026-10-30 |
| Approval of interim use | Head of QA, 2026-10-19 (Sam Sample, [signed in eQMS]) |
| Nonconformity and CAPA (mandatory) | NC ref: NC-2026-042 (includes the 3 PRs with an unknown model, assessed: no product impact); CAPA ref: CAPA-2026-015 (same root cause as NC-2026-041: purchase without the software inventory step of ACME-QP-04) |

If the interim controls cannot be shown, QMS-relevant use stops until they are.

## 10. Readiness (go / no-go before approval)

- [x] Managed configuration deployed, owned by root / Administrators (`tools/codex/requirements.example.toml`); reference machine per OS: ACME-MBP-017 (macOS, MDM payload), ACME-WS-004 (Linux)
- [x] Sandbox protected like production (`checks/mirror_protection.py`); code-owner review of agent and CI files (`examples/github/CODEOWNERS.example`): shared with Claude Code
- [x] Required SOUP check (`examples/github-workflow-soup-gate.yml`); secret push protection; Actions approval setting off
- [x] MA-01 credentials; test accounts with SSO seats; reviewer list, training records; eQMS e-signatures: all confirmed by Alex Example on 2026-10-19

## 11. Schedule and approval

Sequence and dates: readiness, approval of plan and record, IQ-03 / OQ / MA-01, release decision, PQ window, signed addendum: 2026-10-19; 2026-10-20; 2026-10-21 to 2026-10-22; 2026-10-23; 2026-10-26 to 2026-11-20 (extended if fewer than 20 PRs); 2026-11-27.

Approved in the eQMS by the Head of QA before any test. Author: Alex Example (Validation Engineer); technical input Jordan Demo (Engineering Lead). AI assistance: no. Version 1.0 approved in the eQMS by Sam Sample on 2026-10-20: [signed in eQMS].

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-19 | Alex Example | Initial draft (kit 0.2.0, lite) |
| 1.0 | 2026-10-20 | Alex Example | Approved for execution |
