> FICTIONAL EXAMPLE, invented for illustration only. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are made up to show what an executed lite package looks like. Model ids are placeholders. Each person signs in the eQMS, shown here only as "[signed in eQMS]".

# ACME-VAL-GEN-L02 Tool discovery checklist

| Field | Value |
|---|---|
| Document ID | ACME-VAL-GEN-L02 (lite profile) |
| Version | 1.0 (approved 2026-10-20) |
| Owner / approver (roles) | Validation Engineer / Head of QA |
| Date | 2026-10-19 |
| Organisation | Acme MedSoft |

> Generated with the AI Coding Tool Validation Kit 0.2.0, lite profile. Copy this checklist for each execution, record who did each check and when, and file the completed copy as a record approved in the eQMS.

## 1. Purpose and when to run

Find the AI tools actually in use at Acme MedSoft (including shadow AI: unsanctioned tools, personal accounts, undeclared AI-assisted changes) and reconcile them with the software inventory, so that every QMS-relevant tool is registered, validated or stopped (ISO 13485:2016 clauses 4.1.6 and 7.4). Run it before a validation plan is approved (and as part of the interim-use justification), at every periodic review (every 12 months), and on a trigger: a new AI vendor invoice, a new app or bot on the code host, or a report under ACME-VAL-GEN-L01.

| Execution date(s) | Executed by | Reason | Repositories in scope | Previous execution |
|---|---|---|---|---|
| 2026-10-19 | Alex Example (C4-C5, R1, R4, B3-B4, P1-P2), Jordan Demo (C1-C3, C6, B1-B2, E1-E3) | Initial, before the validation plans | lumen-core, lumen-app, qa-tooling, val-sandbox and 6 archived repositories | None (first execution) |

Registered tools to compare against: Claude Code (Anthropic, `CLAUDE`, plan ACME-VAL-CLAUDE-L01); OpenAI Codex (OpenAI, `CODEX`, plan ACME-VAL-CODEX-L01); no other AI tool is registered.

## 2. Checks

Run for every repository in scope and attach the output: `python3 checks/find_ai_footprint.py --path REPO_DIR --known-tools claude_code,codex,shared --operator "<name>" --out evidence/GEN/DISCOVERY/` (add `--org ORG` for app installations on GitHub); a detected tool outside the inventory fails the run.

Check IDs are those of the full checklist; a lite row may combine several.

| # | Check | How | Done (date, initials) | Findings |
|---|---|---|---|---|
| C1-C3 | Apps, bots and AI settings on the code host | Installed GitHub Apps and authorised OAuth apps with AI functions; third-party coding agents hosted by GitHub (search the audit log, they are not in the installed-apps list); Copilot policies, including whether approvals count, "Default policy for new features" and "Default availability for released models" | [x] 2026-10-19, JD | GitHub App `acme-claude-reviewer` (registered); no Codex, Copilot or other AI app or OAuth app; audit log: no third-party coding agent activity; Copilot not licensed, its policies disabled, "Default policy for new features" set to disabled |
| C4-C5, R2-R3 | AI in workflows and PRs | AI actions or CLIs in `.github/workflows/*`; reviews whose `user.type` is "Bot"; agent branches such as `copilot/`; AI co-author trailers | [x] 2026-10-19, AE | `claude-review.yml` in the 3 product and tooling repositories (registered); Bot reviews only by `acme-claude-reviewer[bot]`; trailers name Claude Code or OpenAI Codex only |
| C6 | Automation tokens | Tokens, deploy keys and service accounts used by bots or agents, and who owns each | [x] 2026-10-19, JD | Review App private key and `ANTHROPIC_API_KEY` secret for the review workflow (owner Jordan Demo); 2 deploy keys for releases (owner Casey Admin); no personal tokens used by bots |
| R1 | Agent configuration and instruction files | `.claude/`, `CLAUDE.md`, `.mcp.json`, `AGENTS.md`, `.codex/`, `.cursor/`, `.github/copilot-instructions.md`, `.github/instructions/`, `.github/hooks/`, `.gemini/`, `GEMINI.md` (output of the script above) | [x] 2026-10-19, AE | `CLAUDE.md`, `.claude/settings.json` and `AGENTS.md` in lumen-core, lumen-app, qa-tooling; nothing in the archived repositories; no `.mcp.json`, `.codex/`, `.cursor/` or Copilot files |
| R4 | CODEOWNERS coverage | The files from R1 and the CI definitions require code-owner review | [x] 2026-10-19, AE | Covered in all 3 repositories (`@acme-medsoft/qualified-reviewers`, `@acme-medsoft/eng-leads` for `.github/` and agent files) |
| B1-B2 | Identity provider and vendor consoles | AI applications in the SSO catalogue; seat lists of each registered tool against the identity provider (leavers, external accounts) | [x] 2026-10-19, JD | SSO catalogue: Claude and the OpenAI workspace only; 14 and 6 seats, all active employees, no leavers or external accounts |
| B3-B4 | Purchasing | Expense reports, card statements and invoices from AI vendors (including individual subscriptions) against the approved supplier list | [x] 2026-10-19, AE | Invoices from Anthropic and OpenAI (approved suppliers); no expense claims for individual AI subscriptions in 2026 |
| E1-E3 | Endpoints and CI images | IDE extensions, AI CLIs and desktop apps on developer machines; AI CLIs in CI images; AI vendor credentials stored as CI secrets (names only) | [x] 2026-10-19, JD | Claude Code and Codex CLI on 18 laptops (registered); an AI code-completion IDE extension with a personal free-tier login on 2 laptops (item 3 below); no AI CLIs in CI images; CI secret `ANTHROPIC_API_KEY` (review workflow) only |
| P1-P2 | People | Ask every team, including non-engineering teams that draft documents, which AI tools, accounts and models they use, and who runs scheduled or autonomous agents | [x] 2026-10-19, AE | Product, QA, RA and IT teams asked: answers match the findings above, including item 3; RA confirms no AI drafting of controlled documents; no scheduled or autonomous agents |

## 3. Reconciliation and decision rules

| # | Found item (tool, surface, account) | Check | On inventory? | QMS-relevant? | Action, owner, due | Record ref |
|---|---|---|---|---|---|---|
| 1 | Claude Code: local CLI and review App, organisation account | C1-C3, C4-C5, R1, B1-B2, E1-E3 | yes | yes | Validate (lite); interim use with nonconformity; Alex Example, release decision by 2026-10-30 | ACME-VAL-CLAUDE-L01, NC-2026-041 |
| 2 | OpenAI Codex: local CLI, organisation workspace | R1, B1-B2, E1-E3 | yes | yes | Validate (lite); interim use with nonconformity; Alex Example, release decision by 2026-10-30 | ACME-VAL-CODEX-L01, NC-2026-042 |
| 3 | AI code-completion IDE extension, personal free-tier login, 2 laptops, used on qa-tooling | E1-E3, P1-P2 | no | yes (code in qa-tooling) | Removed and blocked by endpoint policy (Casey Admin, 2026-10-19); the 5 qa-tooling PRs made with it were checked with the gate script: approved by qualified humans, checks green; CAPA-2026-015 scope extended to cover it | IT-CHG-2026-118, CAPA-2026-015 |

- **QMS-relevant tool not on the inventory:** register it, stop QMS-relevant use or document an interim-use justification, raise a deviation per ACME-QP-09 and plan its validation.
- **Not QMS-relevant:** record the determination; re-check at the next execution.
- **Registered tool on a new surface, model or context:** a change trigger of that tool's validation (see its validation report).
- **Personal or foreign account used for QMS work:** stop that use, move to the organisation account, assess the records produced.
- **Instruction or configuration files without CODEOWNERS protection:** raise a change to protect them.

## 4. Conclusion

Unregistered QMS-relevant tools found: 1 (item 3, removed). Actions raised: removal and endpoint block IT-CHG-2026-118; CAPA-2026-015 scope extended. Inventory updated: yes, software inventory revision 23. Conclusion: **complete after actions**.

Written by: Alex Example. Approved in the eQMS by the Head of QA: Sam Sample, 2026-10-20, [signed in eQMS].

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-19 | Alex Example | Initial draft generated with the kit (0.2.0, lite profile) |
| 1.0 | 2026-10-20 | Alex Example | Executed 2026-10-19; approved |
