> FICTIONAL EXAMPLE, invented for illustration only. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are made up to show what an executed lite package looks like. Model ids are placeholders. Each person signs in the eQMS, shown here only as "[signed in eQMS]".

# ACME-VAL-CLAUDE-L01 Validation plan: Claude Code

| Field | Value |
|---|---|
| Document ID, version | ACME-VAL-CLAUDE-L01, 1.0 (approved 2026-10-20), lite profile |
| Tool / vendor | Claude Code / Anthropic |
| Owner / approver (roles) | Validation Engineer / Head of QA |
| Organisation, date | Acme MedSoft, 2026-10-19 |
| Product context | Class II SaMD (FDA 510(k)); EU MDR Class IIa planned |

> Generated with the AI Coding Tool Validation Kit 0.2.0, lite profile. Complete every `[fill in]`. Approved with ACME-VAL-CLAUDE-L02 **before** the first test, by the approver personally in the eQMS.

## 1. Purpose and profile

The **lite profile** is the risk-proportionate minimum where every AI output is independently verified downstream (qualified human review, required CI) before it takes effect (ISO 13485:2016 clause 4.1.6; FDA CSA; GAMP 5 Second Edition appendix D9). Requirement and test IDs and commands are those of the full profile; under a shared ID lite criteria equal or exceed full, and full adds tests and steps (upgrade: kit `docs/lite-vs-full.md`). Validated: tool, vendor, surface, context of use; models via the approved list and MA-01.

Software validation procedure clause adopting lite, L1 to L9 and section 8: ACME-QP-04 Validation of QMS and development software, clause 6.3 (lite profile and the conditions L1 to L9, adopted in revision 7) and clause 6.4 (predetermined change protocols).

## 2. When lite is not enough

| # | Condition (any "yes": full; hard stops cannot be overridden) | Applies? Why |
|---|---|---|
| L1 | Hard stop: pinned model policy (AI output is a control or evidence) | no (envelope) |
| L2 | Hard stop: QMS agents, or any agent writing to QMS systems outside the code-host gate | no (none declared): no MCP servers are configured (no `.mcp.json`; managed `allowManagedMcpServersOnly` with no managed servers), and no agent holds a token for the eQMS, the issue tracker or the document system |
| L3 | `doc_drafting` without independent source check of each draft | no (not selected) |
| L4 | GxP in scope with high-impact use | no (not selected) |
| L5 | Section 5 determination "high process risk" | no: not high process risk for every context, see section 5 |
| L6 | Notified body, FDA or customer expects more depth | no: no customer quality agreement covers development tools; the notified body audit plan for 2027 has no specific request (asked on 2026-10-13, reply on file in ACME-QA-CORR-2026-088) |
| L7 | Audit findings on this tool or AI tool validation | no: no internal or external finding on AI tools to date; the use before validation is handled as NC-2026-041 (section 9) |
| L8 | Hard stop: AI output (e.g. tests) used as verification evidence or QMS record without review of its adequacy | no: AI-written unit tests reach `main` only through the reviewed PR, where the ACME-QP-12 checklist asks whether each test can fail; design verification evidence is produced and reviewed by people under design control; `qa-tooling` produces no QMS records or verification results |
| L9 | Hard stop: agent with write credentials or secrets beyond the PR path reads untrusted content | no: the review workflow runs only on `pull_request` from organisation members (`allowed_non_write_users` empty), with contents read and pull-requests write for comments and the vendor API key as its only secret; the three repositories are private and only members open issues and PRs; the local CLI has no MCP servers |

Decision: **lite**, by the Head of QA; re-checked on T9, T10, T14 and periodic review.

## 3. Inventory

| Item | Value |
|---|---|
| Tool type, ID; surfaces | `claude_code`, CLAUDE; `local_cli_ide` `pr_review_bot`  |
| Plan, contract / DPA, supplier evaluation | Enterprise plan; contract ACME-PUR-2026-014 and DPA of 2026-01-05; supplier evaluation ACME-VEN-2026-011 (approved supplier, ISO 13485:2016 clause 7.4) |
| Organisation workspace, SSO, admins (REQ-16) | Organisation "Acme MedSoft", SAML single sign-on through the corporate identity provider; managed `forceLoginMethod` and `forceLoginOrgUUID`; admins Jordan Demo (Engineering Lead) and Casey Admin (IT) |
| Seats reconciled with identity provider, training records (REQ-16, REQ-17) | 2026-10-19: 14 seats, 14 active employees, no external or personal accounts; 14 of 14 trained on ACME-VAL-GEN-L01 on 2026-10-19 (training records TR-2026-301 to TR-2026-314) |
| Validated version, update control | 2.1.302; managed `requiredMinimumVersion` = `requiredMaximumVersion` = 2.1.302, `autoUpdatesChannel` "stable"; review workflow pins `anthropics/claude-code-action` to a commit SHA; raised only by change record (trigger T7a or T7) |
| Model policy, approved models | envelope: `anthropic-model-a` `anthropic-model-b`  |
| Vendor data terms: retention, training, region, source (REQ-09) | 30 days standard server retention; not used for training; no residency commitment (accepted in DPIA-2026-03); source: ACME-PUR-2026-014 and the vendor's commercial terms as of 2026-10-13 |
| GAMP 5 category | 4 (configured product): behaviour depends on managed settings, permission rules, sandbox and instruction files |
| Software development / configuration management plan; IEC 62304 safety class | Software development plan ACME-SDP-LUMEN revision 4, section 8 (tools, their configuration and model ids as configuration items); configuration management plan ACME-CMP-01; software safety class B |
| Status | In use since 2026-01-12 (section 9) |

Version: `claude --version`, `claude doctor`; update control: managed `requiredMinimumVersion` / `requiredMaximumVersion`, `autoUpdatesChannel` or `DISABLE_UPDATES` (invalid values are dropped: confirm the effect).

## 4. Intended use

The AI never approves, merges, signs or closes records; the responsible human approves under their own identity.

| Context | Users, repositories or systems; approver |
|---|---|
| `code_product` | Product developers (trained); `acme-medsoft/lumen-core`, `acme-medsoft/lumen-app`, branch `main`; a qualified reviewer other than author and launcher (ACME-QP-12), plus the second senior review for safety-related items required by the software development plan |
| `code_tooling` | Developers and QA engineers (trained); `acme-medsoft/qa-tooling`, branch `main`; a qualified reviewer other than author and launcher |
| `pr_review` | Workflow `claude-review.yml` (GitHub App `acme-claude-reviewer[bot]`, comments only) on every PR in the three repositories; advisory, the human reviewer decides |

Not intended: other contexts, surfaces or models; the AI as reviewer of record or validating itself; personal accounts. Rules: ACME-VAL-GEN-L01. Drafting controlled documents with AI (`doc_drafting`) is not approved at Acme MedSoft; adding it is trigger T10 and needs a new decision on L3.

## 5. Risk determination

FDA CSA: **high process risk** when a tool failure may cause a quality problem that foreseeably compromises safety.
Crediting the tested gate and CI as independent verification is an interpretation: quote the CSA risk-determination section. The credit holds while PQ-02 passes.

| Context | Suggested | Determination, rationale |
|---|---|---|
| `code_product` | Not high when the tested gate and CI are the verification of record; otherwise high (L5) | **Not high process risk.** No AI-written change takes effect without approval by a qualified human on the final commit and green required checks (unit and integration tests, SAST, secret scanning, SOUP gate); safety-related items get a second senior review; device verification remains the design-control verification of record, independent of the tool. Interpretation of the CSA risk-determination section, quoted in ACME-QP-04 annex B. Valid while PQ-02 finds no class 1 miss; re-assess if any of these controls is weakened |
| `code_tooling` | Not high; L8 if it produces QMS records or verification results | **Not high process risk.** `qa-tooling` produces no QMS records or verification results; tooling used as evidence is validated separately under ACME-QP-04 |
| `pr_review` | Not high if REQ-15 holds | **Not high process risk.** Advisory comments only; never a required approval or check (OQ-04) |

Overall (highest context): **not high process risk**. Known guardrail limitations (verify against the vendor's current documentation):
KL-01 Bash deny rules match text; the OS sandbox covers shell commands only. KL-02 Without `sandbox.failIfUnavailable` a failed sandbox runs unsandboxed. KL-03 Hooks fail open unless `"onFailure": "block"`. KL-04 Auto mode can be the starting mode. KL-05 Server-managed settings are client-side and miss some surfaces. KL-06 Headless runs have no workspace-trust prompt. KL-07 Fallbacks can change the model. KL-08 Local transcripts are unencrypted.
Accepted before execution, with compensating controls: KL-01 (the server-side gate, OQ-02 to OQ-06; the OS sandbox for filesystem and network); KL-05 and KL-03 (managed settings come from the root-owned file, and no hook is a control); KL-08 (full-disk encryption on every laptop, ACME-IT-07). Closed by configuration and tested in OQ-08: KL-02 (`sandbox.failIfUnavailable`) and KL-04 (bypass and auto modes disabled); KL-07 is covered by the exact allow-list (OQ-10); KL-06 does not apply (no headless surface). Organisation-specific ACME-A1: `anthropics/claude-code-action` documents that it cannot approve or merge, but that limit lives in the action, not on the platform (compensating: Actions approval setting off, the App's approval not counted, action pinned to a commit SHA; OQ-04).

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

Negative gate tests, server-side binding controls, limited scripted tests, historical samples, automated MA-01; criteria and minimum samples: ACME-VAL-CLAUDE-L02.

Planned: OQ-01, OQ-10: 3 repositories, 4 PRs in lumen-core (at least 1 safety-related), 3 in lumen-app, 3 in qa-tooling, drawn from the whole period since 2026-01-12, and the model id of each of these 10 PRs; OQ-02 to OQ-07: val-sandbox and lumen-core, code-host part once for Claude Code and OpenAI Codex (same repositories and rulesets), recorded in this tool's record under `evidence/GEN/`, agent steps per tool; MA-01: `anthropic-model-a`, `anthropic-model-b`; PQ: 2026-10-26 to 2026-11-20, all three repositories, and at least 20 AI-assisted PRs. Sample rule (random, seed recorded): AI-assisted PRs identified by the trailer or the PR template declaration; the safety-related PR chosen from those touching items classified safety-related in the software development plan; PQ-02 draws 10% of the AI-assisted PRs merged in the PQ-01 period, at least 5. PQ-01 outlier: approval within 5 minutes of ready-for-review, or without comment, on a diff over 300 lines; reviewed by Jordan Demo (Engineering Lead, qualified reviewer; approver excluded). PQ-02 missed-defect classes: 1 could affect safety, a risk control or a verification result (limit 0); 2 functional or critical coding-rule defect (limit 1); 3 other.

Roles: the Validation Engineer executes and drafts ACME-VAL-CLAUDE-L03, never approves; the Head of QA approves plan, record, release, admissions and PQ addendum, never executes; the Engineering Lead owns configuration (frozen during execution), change control and vendor monitoring. Minimum team: one engineer, one approver, sandbox test accounts. Claude Code is only the object under test.

Deviation classes: **critical**, a gate or guardrail does not hold (unapproved merge, push or bypass; an AI approval counts; a denied action runs beyond accepted limitations); **major**, any other failed criterion, including guardrail tests IQ-03, OQ-09, OQ-10, MA-01, or a sampled change without qualified approval; **minor**, a record defect changing no result. Critical and major block release of the affected surface or context until corrected and re-tested.

Acceptance: guardrail criteria hold in 100% of cases and runs. Release rests on IQ-03, OQ and MA-01, "approved with conditions" until the signed PQ addendum to ACME-VAL-CLAUDE-L03, due within 6 weeks; if PQ fails, suspend use and assess merged changes. Evidence store: validation area of the eQMS, linked from the evidence index of ACME-VAL-CLAUDE-L02; retention per ACME-QP-02 (device lifetime plus 2 years), at least the device lifetime and two years from release (ISO 13485:2016 clause 4.2.5).

## 8. Model change protocol (three tiers)

If the procedure (section 1) forbids predetermined change protocols, model changes follow normal change control.

1. **Initial validation:** MA-01 on every approved model, fixed here (changes by amendment): tasks `function-fix-failing-test`, `guardrail-denied-command`, `guardrail-no-ci-edit`, `guardrail-protected-paths` of `admission/tasks/` (kit 0.2.0); `doc-citation-probe` dropped because `doc_drafting` is out of scope; no private tasks; baseline variants: `developer` (laptop managed settings on test VM ACME-VM-SBX-01); the review bot runs comments-only with read-only contents and is covered by OQ-04 alone; 3 runs per task; auxiliary models: none; suite SHA-256 over the sorted per-file SHA-256 of tasks and fixtures, as `run_admission.py --list` prints it: `271a22d74c0f84528b23bc0678543db8127dd3999b7b5a9a4d2f00a60269b4a0` (output filed as `evidence/GEN/MA-01/20261019-admission-suite-list.txt`). MA-01 screens for gross regression only.
2. **Model admission:** a new id matching a pattern below, with tool version and IQ-03 baseline unchanged and no guardrail-relevant item in the screened release notes, needs MA-01 only. Pass: admission record (ACME-VAL-CLAUDE-L03 section 7) approved by the Head of QA; the exact id, never the pattern, joins the enforced allow-list. Repointable ids (`*-latest`, unversioned names) are never admitted.

| Approved entry | Pre-authorised pattern | Excluded |
|---|---|---|
| `anthropic-model-a` | `anthropic-model-a-*` (dated versions of the same model) | `*-latest`, preview ids, any id without a date suffix |
| `anthropic-model-b` | `anthropic-model-b-*` (dated versions of the same model) | `*-latest`, preview ids, any id without a date suffix |

3. **Re-baseline:** on the change triggers in ACME-VAL-CLAUDE-L03. New vendor: new initial validation.

Enforcement: managed `availableModels` with `availableModelsMatch: "exact"`, `enforceAvailableModels: true` and `deniedModels`.
Weekly detection (extract of the model ids in the OpenTelemetry export and the vendor's usage export, then commit trailers and the PR template, reviewed by the Engineering Lead): model ids from telemetry, session logs or vendor exports, then trailers, PR template. Use before admission is a deviation (T4): changes made with the model are reviewed and its use stops.

## 9. Interim use

Use before validation is a nonconformity (ISO 13485:2016 clause 4.1.6), declared openly.

| Item | Content |
|---|---|
| First known use; contexts, surfaces; why use continues | 2026-01-12 (first invoice; first AI-attributed commit in lumen-core). `code_product`, `code_tooling`, `pr_review`; local CLI and review bot. Use continues because the look-back below shows every change since 2026-02-05 passed the server-side gate and required checks, and the two earlier commits outside a PR are tooling-only and assessed |
| Interim controls verified before approval: REQ-01 to REQ-04 on every repository, REQ-09, REQ-16, REQ-17 | Evidence `evidence/CLAUDE/INTERIM/`: `check_github_gates.py --prs 300 --commits-since 2026-01-12` on lumen-core, lumen-app and qa-tooling (gate configuration pass, no bot approval counted, no bypass in the last month), push protection for secrets on, seat list against the identity provider, briefing records; effective from 2026-10-19 |
| Restrictions until release | No new repositories, surfaces or models; no AI-assisted changes to items classified safety-related without the second senior review |
| Look-back since first use (gaps go to the nonconformity) | 1. Every protected-branch commit matched to an approved merged PR (`check_github_gates.py --commits-since 2026-01-12`): 424 commits (squash merges); 422 in approved merged PRs, and 2 commits in qa-tooling of 2026-02-02 pushed by an admin before the ruleset existed (2026-02-05). 2. Bypass history: rule-suite insights show 0 bypasses in the last month; the organisation audit log export (2026-04-22 to 2026-10-19) shows no bypass on the three repositories; 2026-01-12 to 2026-04-21 can no longer be exported: gap recorded. 3. Models used: `anthropic-model-a` and `anthropic-model-b` (inside); an older id `anthropic-model-0` until 2026-03-15 in 23 PRs (outside); 4 PRs unknown (no trailer, no telemetry before 2026-03-01). 4. Product impact: released versions lumen-core 3.2.0 and 3.3.0 contain AI-assisted changes, all approved by qualified humans with green checks and verified under design control; no impact found. 5. OQ-01 sample over the whole period; for approvals before ACME-VAL-GEN-L01 was issued (2026-10-19), the training that counts is the ACME-QP-12 code-review training then in force |
| ACME-VAL-GEN-L02 executed; release decision deadline | Executed 2026-10-19; release decision by 2026-10-30 |
| Approval of interim use | Head of QA, 2026-10-19 (Sam Sample, [signed in eQMS]) |
| Nonconformity and CAPA (mandatory) | NC ref: NC-2026-041 (includes the two pre-ruleset commits, the bypass-history gap, the 23 PRs with `anthropic-model-0` and the 4 with an unknown model, each assessed: no product impact); CAPA ref: CAPA-2026-015; root cause: seats were bought on a department budget without the software inventory step of ACME-QP-04, so no validation was triggered; the CAPA adds an AI-tool registration step to purchasing and to the tool-discovery checklist |

If the interim controls cannot be shown, QMS-relevant use stops until they are.

## 10. Readiness (go / no-go before approval)

- [x] Managed configuration deployed, owned by root / Administrators (`tools/claude-code/managed-settings.example.json`); reference machine per OS: ACME-MBP-017 (macOS), ACME-WS-004 (Linux)
- [x] Sandbox protected like production (`checks/mirror_protection.py`); code-owner review of agent and CI files (`examples/github/CODEOWNERS.example`): `val-sandbox` compared on 2026-10-19
- [x] Required SOUP check (`examples/github-workflow-soup-gate.yml`); secret push protection; Actions approval setting off
- [x] MA-01 credentials; test accounts with SSO seats; reviewer list, training records; eQMS e-signatures: all confirmed by Alex Example on 2026-10-19

## 11. Schedule and approval

Sequence and dates: readiness, approval of plan and record, IQ-03 / OQ / MA-01, release decision, PQ window, signed addendum: 2026-10-19; 2026-10-20; 2026-10-21 to 2026-10-22; 2026-10-23; 2026-10-26 to 2026-11-20; 2026-11-27.

Approved in the eQMS by the Head of QA before any test. Author: Alex Example (Validation Engineer); technical input Jordan Demo (Engineering Lead). AI assistance: no. Version 1.0 approved in the eQMS by Sam Sample on 2026-10-20: [signed in eQMS].

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-19 | Alex Example | Initial draft (kit 0.2.0, lite) |
| 1.0 | 2026-10-20 | Alex Example | Approved for execution |
