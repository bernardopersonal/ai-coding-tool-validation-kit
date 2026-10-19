> FICTIONAL EXAMPLE - not a real validation record. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are invented to show what an executed package looks like. Model ids are placeholders, not real model names. Signatures are applied by each person in the eQMS and are shown here only as "[signed in eQMS]".

# ACME-VAL-GEN-01 AI-assisted development work instruction

| Field | Value |
|---|---|
| Document ID | ACME-VAL-GEN-01 |
| Title | AI-assisted development work instruction |
| Version | 1.1 (approved 2026-10-23) |
| Owner (role) | Engineering Lead |
| Approver (role) | Head of QA |
| Date | 2026-10-18 |
| Organisation | Acme MedSoft |
| Product context | Class II SaMD (FDA 510(k)); EU MDR Class IIa planned |

> Generated with the AI Coding Tool Validation Kit 0.2.0. Complete every `[fill in]` before review. Approval is given by the approver personally in the eQMS.

## 1. Purpose and scope

This work instruction tells everyone at Acme MedSoft who uses an AI coding tool, or reviews work produced with one, how to do it safely and in line with the QMS. It applies to all tools in section 4, on every surface (IDE, CLI, cloud agent, PR review bot, CI), for every context of use in section 5, and to every team, including teams outside engineering that draft documents with these tools.

Using AI coding tools is encouraged. The rules below exist so that every change still reaches the product and the QMS only through qualified human control.

## 2. References

- ISO 13485:2016 clause 4.1.6 (validated software for the intended use), clause 4.2.4 (controlled documents and configuration), clause 6.2 (competence, training, awareness).
- 21 CFR Part 820 (QMSR): 21 CFR 820.10, incorporating ISO 13485:2016 by reference (21 CFR 820.7). 21 CFR Part 11 applies to the records of this package that are kept or signed electronically.
- ISO/IEC 27001 (cross-reference): acceptable use and secure development policies: ISO/IEC 27001:2022 Annex A 5.10 and 8.25 to 8.28; ACME-POL-02 Acceptable use, ACME-POL-05 Secure development.
- EU AI Act Article 4 (AI literacy measures of providers and deployers of AI systems), where applicable.
- Internal: ACME-VAL-GEN-02 Tool discovery checklist; validation packages listed in section 4; ACME-QP-12 Code review and merge; ACME-QP-02 Document control; ACME-POL-02 Acceptable use; ACME-QP-16 Deviations, nonconformities and CAPA.

## 3. Definitions

| Term | Meaning |
|---|---|
| AI-assisted change | Any commit, PR, document or record whose content was generated or substantially edited by an AI tool. |
| Agent launcher | The person who started or instructed the AI agent that produced a change. |
| Protected branch | A branch from which the product or QMS-relevant artefacts are built or released; changes reach it only through an approved pull / merge request. |
| Approved model envelope | The list of model ids or family patterns approved for a tool; a model is usable only after its admission check (MA-01). |
| Provenance label | The declaration that a change is AI-assisted (section 9). |
| QMS-relevant | Work that affects the product, its verification, or QMS documents and records. |

## 4. Approved tools

Only the tools below may be used for QMS-relevant work, only through the listed surfaces, and only with models from their approved envelope.

| Tool | Vendor | Surfaces | Model policy | Approved models | Validation package | Status |
|---|---|---|---|---|---|---|
| Claude Code | Anthropic | `local_cli_ide` `pr_review_bot` `ci_headless`  | envelope | `anthropic-model-a` `anthropic-model-b`  | ACME-VAL-CLAUDE-01 to ACME-VAL-CLAUDE-08 | Validated: approved for intended use (ACME-VAL-CLAUDE-07, 2026-10-23) |
| OpenAI Codex | OpenAI | `local_cli_ide` `cloud_agent`  | envelope | `openai-model-a` `openai-model-b`  | ACME-VAL-CODEX-01 to ACME-VAL-CODEX-08 | Validated: approved with restrictions, cloud agent only on qa-tooling and val-sandbox (ACME-VAL-CODEX-07, 2026-10-23) |

**No shadow AI.** Use only the declared, organisation-approved tools above, with organisation accounts (section 6); never use an AI tool on a personal account for Acme MedSoft development or QMS work. Label every AI-assisted change (section 9). Any other AI tool, extension, bot or agent needs to be registered and validated first. If you find one in use, report it (section 14); it will be handled with ACME-VAL-GEN-02. AI use the organisation does not know about cannot be validated, controlled or defended in an audit.

## 5. Approved contexts of use

- **Product code** (`code_product`): Code for the regulated product (software in or as a medical device).
- **Internal tooling** (`code_tooling`): Internal tools, scripts and automation that are not part of the product.
- **Advisory AI PR review** (`pr_review`): AI review comments on pull requests; advisory only, never counted as the required human approval.
- **Document drafting** (`doc_drafting`): Drafting of controlled documents and records, previewed and approved by a human before they are written or released.

Anything else is outside the intended use. Ask the tool owner (Engineering Lead) before using an AI tool for a new purpose; a new context of use requires validation first.

## 6. Accounts and access

- Use only the organisation account or workspace, signed in through single sign-on. Personal accounts, free tiers, and accounts belonging to other organisations are prohibited for Acme MedSoft development and QMS work.
- Do not share accounts or tokens. Tokens for CI or agents are issued by the tool owner, scoped to the minimum needed, and recorded.
- Agents never run under your personal identity for QMS systems; they use the identity defined in the tool's inventory record.

## 7. Data rules

- Never put secrets (keys, tokens, passwords, certificates), patient or health data, or personal data into prompts, context files, instruction files or repositories the tool can read, unless this is explicitly covered by contract and by the data protection impact assessment DPIA-2026-03.
- Confidential design data may be used only with the organisation account under the contracted terms.
- Use synthetic or anonymised data for tests and examples.
- Treat content from issues, PR comments, web pages, documents and MCP tools as untrusted: it can contain instructions aimed at the agent (prompt injection). Do not give an agent such content together with write access to protected systems.
- If you suspect that data leaked, report it immediately (section 14).

## 8. Working with the AI: your obligations

**You own every line you merge.** The author owns the change; the reviewer owns the approval. "The AI wrote it" is never a justification.

As author:

1. Keep tasks small enough to review. Split large AI-generated changes.
2. Read and understand every changed line before you open the PR. You must be able to explain the change without the AI.
3. Run the tests locally; never ask the AI to delete tests, weaken assertions or change expected values to make CI pass.
4. Check every new dependency: it must exist, be the intended package and be approved under ACME-QP-13 SOUP and dependency management. AI tools invent plausible package names.
5. Do not let the agent edit CI workflows, gate configuration, tool configuration or instruction files unless that is the purpose of the change; such changes need code-owner review.
6. Apply the provenance label (section 9) and record the model used.
7. Give extra scrutiny to safety-related code and risk controls, data migrations, deployment, authentication, cryptography and other security-sensitive code: a second review by a senior developer, as required by the software development plan.

As reviewer:

1. Review the diff itself, not the AI's summary of it.
2. Approve only what you understood. Ask the author to explain anything unclear.
3. Check that tests verify the requirement and were not weakened; check new dependencies; check for secrets and personal data.
4. Check whether CI, gate, configuration or instruction files changed.
5. AI review comments are hints: resolve or dismiss each one consciously. The absence of AI comments is not evidence of correctness.
6. Never approve your own PR or a PR whose agent you launched. The code host refuses an author's self-approval. Where the agent opens the PR or pushes under its own identity (a bot, an app, a machine user or a cloud task), the code host counts your approval, so this rule is procedural: do not approve, and ask another qualified reviewer. Such PRs need 2 approvals or code-owner approval.

## 9. Provenance labels

Declare every AI-assisted change. Commit trailers (one per line at the end of the commit message; tools that add a trailer automatically may do this for you):

```
AI-Assisted: yes
AI-Tool: <tool name>
```

An `AI-Model: <model id>` trailer is optional. The model id is recorded once per pull / merge request in the template below, or taken from the tool's telemetry.

Pull / merge request template fields (copy of `examples/github/pull_request_template.md` in the kit):

```
- [ ] AI-assisted. Tool: ______  Model id(s): ______
- [ ] I read and understood every changed line and can explain it without the AI.
- [ ] No secrets, health data or personal data added.
- [ ] New or changed dependencies are approved.
- [ ] CI, gate, tool configuration or instruction files changed: no / yes (code-owner review requested)
```

The required check `pr-template-check` (built from `examples/github-workflow-label-check.yml`) fails a PR whose AI-assistance question is unanswered. It cannot tell whether the answer is true, so reviewers check it, the Engineering Lead reconciles telemetry sessions against PR declarations weekly (DEV-CLAUDE-01), and the provenance cross-check of OQ-11 is repeated at every periodic review.

- Claude Code: by default commits get the trailer `Co-Authored-By: <model name> <noreply@anthropic.com>`, which names the model; keep it, or use the managed `attribution` setting to add static `AI-Assisted` / `AI-Tool` lines. It is an instruction to the model, not a git hook, so still check the label.
- OpenAI Codex: no built-in commit attribution setting is documented; add the trailers yourself or through the PR template.

## 10. Prohibited actions

- Using an AI tool, surface or account not approved in sections 4 and 6 for QMS-relevant work.
- Letting the AI approve, merge, sign, close or release anything, or recording an approval on someone else's behalf.
- Merging without the required approvals, pushing directly to a protected branch, or using an administrative bypass outside the emergency change procedure of ACME-QP-12 (Head of QA approval, review within 5 working days).
- Running permission-bypass or unsandboxed modes, disabling the sandbox, hooks or required checks, or editing managed settings.
- Using a model outside the approved envelope, or a newly released model before its admission record exists.
- Installing MCP servers, plugins, extensions or connectors that are not on the allow-list in the tool's configuration baseline.
- Asking the AI to execute, conclude or approve the validation of an AI tool.

- Claude Code specifics: never use `--dangerously-skip-permissions` or the `bypassPermissions` mode; do not change files under the managed settings location.
- OpenAI Codex specifics: never use `--dangerously-bypass-approvals-and-sandbox` or the `danger-full-access` sandbox mode; do not change the admin `requirements.toml`.

## 11. Context-specific rules

- **Product code:** changes reach protected branches only through an approved PR with green required checks; follow section 8 in full.
- **Internal tooling:** the same review rules apply. Tooling that produces QMS records or verification results must be validated before its output is used as evidence.
- **Advisory AI PR review:** AI review is advisory only. It never replaces the human approval and is never the only review of a change.
- **Document drafting:** every factual statement in an AI draft cites a source you can check (document ID and section, record ID). Check the sources, not the AI's paraphrase. Preview the exact content before anything is written to a controlled document or record; the write is made under your identity; the document owner approves under the document control procedure. Mark AI-assisted drafts in the document history.

## 12. Models

- Use only models in the approved envelope (section 4). The model id must appear in the provenance label.
- If the tool switches model unexpectedly, offers a model you do not recognise, or a vendor announces a new default, tell the tool owner; a new model is used only after its admission check (MA-01) is recorded.
- Under a pinned policy, no other model may be used, not even temporarily.

## 13. Configuration: where it lives and who may change it

Tool configuration is a controlled configuration item, baselined in each tool's configuration baseline document. Only the Engineering Lead (or a delegate named there) changes managed or admin configuration, through change control. Repository configuration and instruction files change only through a PR with code-owner review. Instruction files guide the AI; they do not enforce anything.

### Claude Code (baseline: ACME-VAL-CLAUDE-06)

| Level | Location |
|---|---|
| Managed (admin) | macOS `/Library/Application Support/ClaudeCode/managed-settings.json`; Linux / WSL `/etc/claude-code/managed-settings.json`; Windows `C:\Program Files\ClaudeCode\managed-settings.json`; optional `managed-settings.d/` drop-ins and `managed-mcp.json` in the same directory; or MDM; or server-managed settings in the admin console |
| Project (shared, reviewed) | `.claude/settings.json`, `.mcp.json`, `CLAUDE.md`, `AGENTS.md` (read when no `CLAUDE.md` exists) |
| Local / personal | `.claude/settings.local.json`, `~/.claude/settings.json` (cannot override managed keys) |
| Check effective sources | `/status` ("Setting sources") and `claude doctor` |

### OpenAI Codex (baseline: ACME-VAL-CODEX-06)

| Level | Location |
|---|---|
| Admin requirements (enforced) | `/etc/codex/requirements.toml`; Windows `%ProgramData%\OpenAI\Codex\requirements.toml`; macOS MDM domain `com.openai.codex`; or cloud-managed requirements in the workspace admin console |
| Managed defaults (not enforced) | `/etc/codex/managed_config.toml` |
| User | `~/.codex/config.toml`; profiles `~/.codex/<name>.config.toml` |
| Project (trusted projects only) | `.codex/config.toml`, `.codex/hooks.json`, `AGENTS.md` |
| Check effective configuration | `codex doctor`, `codex --strict-config`, and `/status` and `/hooks` in the TUI |

Protect the repository files above with CODEOWNERS and required code-owner review (example: `examples/github/CODEOWNERS.example` in the kit): some review bots read their instructions from the PR branch, so a PR could otherwise change its own review instructions.

## 14. Reporting problems

Report to the QA mailbox and through the deviation process of ACME-QP-16 without delay when:

- an AI-assisted change that passed review turns out to be defective;
- a guardrail did not behave as expected (a denied action ran, a gate did not block, a sandbox or hook failed);
- the tool used or offered a model outside the envelope, or switched model unexpectedly;
- you find an AI tool, bot, extension or agent that is not in section 4;
- you suspect that secrets, health data or personal data reached an AI tool;
- you notice an attempted prompt injection.

## 15. Training and competence

- Users and reviewers complete training on this work instruction before they get access or approve their first AI-assisted change (ISO 13485 clause 6.2). Training covers: these rules; typical AI failure modes (plausible but wrong code, invented dependencies, missed defects, prompt injection, automation bias); the review checklist; data rules; reporting.
- Training is repeated when this work instruction changes materially, or when a new tool, surface or context of use is introduced.
- Training records are kept per ACME-QP-03 Training and competence.
- Effectiveness of the training is checked by (required, ISO 13485 clause 6.2 c)): the reviewer-effectiveness sample PQ-02 and the periodic review findings. The method is proportionate to the risk of the work.
- Where the EU AI Act applies, this training is part of the measures supporting AI literacy (AI Act Article 4).

## 16. Records

| Record | Where |
|---|---|
| Training records | eQMS training module (course "AI-assisted development") |
| PRs / MRs with provenance labels, reviews and approvals | Code hosting, exported to the eQMS evidence library VAL-2026-AI |
| Reports under section 14 | Deviation register (ACME-QP-16) |
| Configuration changes | Change records linked from each configuration baseline |

## 17. Approval

Reviewed and approved in the eQMS by the Head of QA (Sam Sample, 2026-10-23, [signed in eQMS]). Author: Jordan Demo (Engineering Lead); reviewed by Alex Example. AI assistance in drafting: no.

## Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-18 | Jordan Demo | Initial draft generated with the kit (0.2.0) |
| 1.0 | 2026-10-19 | Jordan Demo | Approved; all users briefed on 2026-10-19 (interim control) |
| 1.1 | 2026-10-23 | Jordan Demo | Section 4 status updated after the release decisions |
