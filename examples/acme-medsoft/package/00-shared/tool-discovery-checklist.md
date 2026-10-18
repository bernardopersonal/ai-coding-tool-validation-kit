> FICTIONAL EXAMPLE - not a real validation record. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are invented to show what an executed package looks like. Model ids are placeholders, not real model names. Signatures are applied by each person in the eQMS and are shown here only as "[signed in eQMS]".

# ACME-VAL-GEN-02 Tool discovery checklist

| Field | Value |
|---|---|
| Document ID | ACME-VAL-GEN-02 |
| Title | AI tool discovery and inventory reconciliation checklist |
| Version | 1.0 (execution of 2026-10-19, approved) |
| Owner (role) | Validation Engineer |
| Approver (role) | Head of QA |
| Date | 2026-10-18 |
| Organisation | Acme MedSoft |

> Generated with the AI Coding Tool Validation Kit 0.1.0. This is a checklist template: copy it for each execution, record who did each check and when, and file the completed copy as a record. Approval of each completed execution is given in the eQMS.

## 1. Purpose and scope

AI coding tools spread faster than inventories are updated: IDE extensions, review bots, CI actions, cloud agents and personal accounts appear without a formal request. This checklist finds AI tools that are in use at Acme MedSoft and reconciles them with the software inventory, so that every QMS-relevant tool is registered, validated or stopped.

When to run it:

- before the validation plan of a tool is approved (initial validation, and as part of the interim-use justification);
- at every periodic review, every 6 months;
- when a trigger occurs: a new AI vendor invoice, a new GitHub / GitLab app or bot, a report under the work instruction ACME-VAL-GEN-01.

## 2. References

- ISO 13485:2016 §4.1.6 (software used in the QMS is validated before use), §7.4 (purchased products and suppliers are controlled).
- 21 CFR Part 820 (QMSR), §820.10, incorporating ISO 13485:2016 by reference (§820.7).
- ISO/IEC 27001 (cross-reference): inventory of information and associated assets, cloud services: ISO/IEC 27001:2022 Annex A 5.9 (inventory of information and other associated assets) and 5.23 (cloud services).
- Internal: ACME-VAL-GEN-01 AI-assisted development work instruction; ACME-QP-04 Validation of QMS and development software; software inventory ACME-INV-SW.

## 3. Execution record

| Item | Value |
|---|---|
| Execution date(s) | 2026-10-12 to 2026-10-19 (survey from 2026-10-12) |
| Executed by | Alex Example (Validation Engineer), with Casey Admin (IT administrator) for B1, E1 to E4 |
| Reason | Initial validation, before approval of the validation plans of both tools |
| Repositories in scope | All 5 active repositories of the GitHub organisation `acme-medsoft` |
| Previous execution | none (first execution) |

## 4. Registered tools (compare against these)

| Tool | Vendor | Tool ID | Surfaces | Inventory record |
|---|---|---|---|---|
| Claude Code | Anthropic | CLAUDE | `local_cli_ide` `pr_review_bot` `ci_headless`  | ACME-VAL-CLAUDE-01 |
| OpenAI Codex | OpenAI | CODEX | `local_cli_ide` `cloud_agent`  | ACME-VAL-CODEX-01 |
| No other registered AI tools | - | - | - | - |

## 5. Checks

Mark each check done with date and initials; record every finding in section 6.

### 5.1 Code hosting

| # | Check | How | Done | Findings |
|---|---|---|---|---|
| C1 | Installed GitHub Apps and OAuth apps with AI functions | Organisation settings: installed GitHub Apps, authorised OAuth apps; list review bots and coding agents | [x] 2026-10-19 AE | 2 apps with AI functions: `acme-claude-reviewer` (custom, registered); the vendor GitHub connector used by Codex (registered) |
| C2 | Third-party coding agents hosted by GitHub | Copilot policies "Allow Claude coding agent" / "Allow Codex coding agent". Their GitHub App does not appear in the installed-apps list, but its actions appear in the audit log: search the audit log | [x] 2026-10-19 AE | Copilot not licensed; audit-log search of the last 90 days: no third-party coding agent activity |
| C3 | Copilot policies | Enterprise and organisation Copilot settings: code review (and whether approvals count), cloud agent, automations, MCP servers, "Default policy for new features", "Default availability for released models" | [x] 2026-10-19 AE | Copilot not licensed; no Copilot policy enabled |
| C4 | AI actions in workflows | Search `.github/workflows/*` in every repository for AI actions (for example `anthropics/claude-code-action`, `openai/codex-action`) and for AI CLI invocations | [x] 2026-10-19 AE | `anthropics/claude-code-action` in `claude-review.yml` (lumen-core, lumen-app, qa-tooling); `claude -p` in `test-gap-report.yml` (qa-tooling); no other AI actions or CLIs |
| C5 | Bot reviews and agent PRs | For recent PRs, list reviews whose `user.type` is "Bot" (`gh api repos/OWNER/REPO/pulls/N/reviews`), agent branches such as `copilot/`, and co-author trailers naming an AI tool | [x] 2026-10-19 AE | Bot reviews only by `acme-claude-reviewer[bot]` and the Codex connector; AI trailers only for registered tools |
| C6 | Tokens used by automation | Fine-grained tokens and deploy keys used by bots or agents; who owns each | [x] 2026-10-19 AE | 1 Console API key (Claude Code CI), owner Jordan Demo; no fine-grained tokens or deploy keys used by bots |

### 5.2 Repositories

Run for every repository in scope and attach the output:

```
python3 checks/find_ai_footprint.py --path REPO_DIR
```

| # | Check | How | Done | Findings |
|---|---|---|---|---|
| R1 | Agent configuration and instruction files | Look for `.claude/`, `CLAUDE.md`, `CLAUDE.local.md`, `.mcp.json`, `REVIEW.md`, `AGENTS.md`, `AGENTS.override.md`, `.codex/`, `.cursor/` (including `.cursor/rules/`, `.cursor/BUGBOT.md`), `.github/copilot-instructions.md`, `.github/instructions/`, `.github/hooks/`, `.aider.conf.yml`, `.gemini/`, `GEMINI.md` | [x] 2026-10-19 AE | `CLAUDE.md` (lumen-core, lumen-app), `AGENTS.md` (lumen-core, qa-tooling), `.claude/settings.json` (lumen-core); nothing for unregistered tools |
| R2 | AI-related CI workflows | `.github/workflows/*` or other CI definitions invoking AI actions or CLIs | [x] 2026-10-19 AE | The two workflows of C4 |
| R3 | AI attribution in history | Commit trailers and co-authors naming AI tools, bot authors, agent branch names | [x] 2026-10-19 AE | Trailers naming registered tools only (`--git-log 500` on each repository) |
| R4 | CODEOWNERS coverage | The files from R1 and R2 are covered by CODEOWNERS with required code-owner review | [x] 2026-10-19 AE | `AGENTS.md` in qa-tooling not covered: reconciliation item 3 |

### 5.3 Identity, purchasing and billing

| # | Check | How | Done | Findings |
|---|---|---|---|---|
| B1 | SSO application catalogue | AI applications connected to the identity provider | [x] 2026-10-19 AE | AI applications in the SSO catalogue: the two registered vendors only |
| B2 | Vendor admin consoles | Seat and member lists of each registered tool, compared with the identity provider (leavers, external accounts) | [x] 2026-10-19 AE | Claude Code 15 seats, Codex 9 members; 1 leaver seat: reconciliation item 4 |
| B3 | Expenses and invoices | Expense reports, corporate card statements, invoices and subscriptions from AI vendors, including individual subscriptions | [x] 2026-10-19 AE | One individual subscription to a general-purpose AI chat assistant (RA team): reconciliation item 2 |
| B4 | Supplier list | AI vendors on the approved supplier list versus vendors found in B1 to B3 | [x] 2026-10-19 AE | Both registered vendors on the approved supplier list (ACME-VEN-2026-011, ACME-VEN-2026-015) |

### 5.4 Endpoints and CI images

| # | Check | How | Done | Findings |
|---|---|---|---|---|
| E1 | IDE extensions | Extension inventory of VS Code, JetBrains and other IDEs via endpoint management, or a script run by each developer | [x] 2026-10-19 AE | Cursor installed on one managed laptop (ACME-MBP-022) with a personal free account: reconciliation item 1 |
| E2 | AI CLIs and desktop apps | AI command-line tools on developer machines (for example `claude --version`, `codex --version`) and AI desktop apps | [x] 2026-10-19 AE | `claude` and `codex` CLIs only on laptops of registered users |
| E3 | CI runner images | AI CLIs installed in CI images; AI vendor credentials stored as CI secrets (names only, never values) | [x] 2026-10-19 AE | Runner image contains the Claude Code CLI only; one AI credential stored as an organisation secret (name recorded, value not read) |
| E4 | Network signals | With the ISMS: proxy or DNS logs for AI vendor API domains (list kept in the ISMS network register) | [x] 2026-10-19 AE | Proxy logs of the last 30 days: AI vendor traffic only from registered users' devices |

### 5.5 People

| # | Check | How | Done | Findings |
|---|---|---|---|---|
| P1 | Short survey | Ask every team, including non-engineering teams that draft documents, which AI tools, surfaces, models and accounts they use and for what | [x] 2026-10-19 AE | Survey 2026-10-12 to 2026-10-14: 31 of 33 people answered; answers consistent with the checks above |
| P2 | Agents and schedules | Ask who runs scheduled or autonomous agents, under which account, and what they write to | [x] 2026-10-19 AE | No scheduled or autonomous agents in use |

## 6. Reconciliation

| # | Found item (tool, surface, account) | Source (check #) | Users / team | On inventory? | QMS-relevant? | Action | Owner | Due | Record ref |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Cursor IDE, personal free account, laptop ACME-MBP-022 | E1 | Dev Three | no | no: no use on company repositories or records (R1, R3 and interview) | Uninstalled from the managed laptop; inventory entry "not permitted" | Casey Admin | 2026-10-19 | INV-SW-118 (done) |
| 2 | General-purpose AI chat assistant, individual subscription | B3 | RA team (1 person) | no | no: text rephrasing, no repository or record access | Inventory entry; use governed by ACME-POL-08 | Robin Specimen | 2026-10-24 | INV-SW-119 |
| 3 | `AGENTS.md` in qa-tooling not covered by CODEOWNERS | R4 | Engineering | yes (registered tools) | yes | CODEOWNERS updated | Jordan Demo | 2026-10-19 | qa-tooling #205 (done) |
| 4 | Claude Code seat of a person who left on 2026-10-03 | B2 | - | yes | yes | Seat removed before IQ-02 | Jordan Demo | 2026-10-19 | Console audit log export (done) |

Decision rules:

- **QMS-relevant tool not on the inventory:** register it (inventory and intended use document), stop QMS-relevant use or document an interim-use justification with interim controls, raise a deviation per ACME-QP-16, and plan its validation.
- **Tool found but not QMS-relevant:** record the determination in the inventory and re-check it at the next execution.
- **Registered tool used through a new surface, model or context:** treat as a re-baseline or admission trigger of that tool's validation plan.
- **Personal or foreign account used for QMS-relevant work:** stop that use and move it to the organisation account; assess the records produced.
- **Instruction or configuration files not protected by CODEOWNERS:** raise a change to protect them.

## 7. Conclusion

| Item | Value |
|---|---|
| Unregistered QMS-relevant tools found | 0 |
| Actions raised | 4 (3 closed on 2026-10-19; item 2 due 2026-10-24) |
| Inventory updated | yes: INV-SW-118, INV-SW-119 |
| Conclusion | Inventory complete after actions |

Written by: Alex Example. Reviewed and approved in the eQMS by the Head of QA (Sam Sample, 2026-10-19, [signed in eQMS]).

## Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-18 | Alex Example | Initial draft generated with the kit (0.1.0) |
| 1.0 | 2026-10-19 | Alex Example | First execution completed (initial validation) |
