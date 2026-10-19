> FICTIONAL EXAMPLE - not a real validation record. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are invented to show what an executed package looks like. Model ids are placeholders, not real model names. Signatures are applied by each person in the eQMS and are shown here only as "[signed in eQMS]".

# ACME-VAL-CLAUDE-06 Configuration baseline: Claude Code

| Field | Value |
|---|---|
| Document ID | ACME-VAL-CLAUDE-06 |
| Title | Configuration baseline |
| Organisation | Acme MedSoft |
| Tool / vendor | Claude Code / Anthropic |
| Configuration owner (role) | Engineering Lead |
| Approved by (role) | Head of QA |
| Rendered | 2026-10-18 (kit 0.2.0) |

Related documents: ACME-VAL-CLAUDE-05 Test protocol (IQ-03 verifies this baseline) · ACME-VAL-CLAUDE-08 Change and revalidation (how this baseline changes) · ACME-VAL-GEN-01 Work instruction · ACME-VAL-GEN-03 Code-host gate qualification.

## 1. Purpose

This record is the approved, versioned configuration of Claude Code at Acme MedSoft (owner: Engineering Lead). It separates **configuration** (versionable, baselined, change-controlled: settings, permission rules, sandbox, hooks, MCP servers, instruction files, model envelope, code-host gates) from **behaviour** (variable: models can change without a version change, so behaviour is covered by monitoring, the model admission check MA-01 and periodic re-tests in ACME-VAL-CLAUDE-08).

The binding controls live server-side (code host and CI). The tool's local configuration is defence in depth and is recorded here so that drift can be detected.

Regulatory anchors:
- ISO 13485:2016 clause 4.1.6 (validated state maintained after changes), clause 4.2.4 (agent configuration and instruction files are controlled items), clause 4.2.5 (records).
- 21 CFR Part 820 (QMSR): 21 CFR 820.10, incorporating ISO 13485:2016 by reference (21 CFR 820.7). 21 CFR Part 11 applies to the records of this package that are kept or signed electronically.
- IEC 62304: tools and settings used to develop the software are supporting items under configuration control (clauses 5.1.10 and 8.1).

## 2. How to fill in this record

1. The Engineering Lead writes the **approved value** of every item before IQ-03.
2. The executor of IQ-03 captures the **effective value**:
   - run `python3 checks/capture_baseline.py --tool claude_code --repo <path-to-repo> --operator "<name>" --out evidence/CLAUDE/IQ-03/` on each reference machine and runner, and copy the values and file hashes from its output;
   - fill the manual fields (admin console, code host) from exports, or from dated screenshots when no export exists.
3. Mark each row Match / No match. A "No match" is a deviation in ACME-VAL-CLAUDE-05.
4. Any later change to an approved value follows ACME-VAL-CLAUDE-08 and produces a new baseline revision; earlier revisions are kept.

## 3. Baseline identification

| Field | Value |
|---|---|
| Baseline ID / revision | CLAUDE-BL-01 / rev 1 |
| Capture date (UTC) | 2026-10-20 |
| Captured by (name) | Alex Example |
| Capture method | capture script (version 0.2.0) plus manual fields (admin console, code host) |
| Evidence files and SHA-256 | `evidence/CLAUDE/IQ-03/baseline_claude_code_20261020T101512Z.json`, `evidence/CLAUDE/IQ-03/baseline_claude_code_20261020T110144Z.json`, `evidence/CLAUDE/IQ-03/baseline_claude_code_20261020T113020Z.json` (SHA-256 in ACME-VAL-CLAUDE-05, evidence index) |
| Machines / runners captured | ACME-MBP-017 (macOS 15), ACME-WS-004 (Ubuntu 24.04), runner image acme-ci-ubuntu-2026.10.2 |
| Supersedes revision | none (first baseline) |
| Change record that created this revision | CR-2026-040 (configuration baseline for the initial validation) |

## 4. Versions per surface

| Surface | Validated version(s) (ACME-VAL-CLAUDE-04 section 3.1) | Effective version | Install method and update control | Evidence | Match |
|---|---|---|---|---|---|
| Local CLI / IDE | 2.1.302 | 2.1.302 | Native installer via endpoint management; managed `requiredMinimumVersion` = `requiredMaximumVersion` = 2.1.302, `autoUpdatesChannel` "stable"; no package-manager installs | IQ-01 | Match |
| PR review bot | `anthropics/claude-code-action` at commit `9b1e4c7d2a6f...` (fictional), CLI 2.1.302 | same SHA; CLI 2.1.302 | Workflow `claude-review.yml`; SHA changed only by change record | IQ-01 | Match |
| CI / headless | 2.1.302 in image acme-ci-ubuntu-2026.10.2 | 2.1.302 | Baked into runner image; digest pinned; rebuild by change record | IQ-01 | Match |

Record the output of `claude --version` and the "Auto-updates" line of `claude doctor`. Update control is set in managed settings (`requiredMinimumVersion` / `requiredMaximumVersion` set to the validated versions, `autoUpdatesChannel`, or `DISABLE_UPDATES` in `env`). Installs through a package manager need their own version pinning: Homebrew, for example, ignores the update channel key, and a version outside the managed range then refuses to start. For the GitHub Action record the pinned commit SHA (`v1` is a moving tag).

## 5. Account, workspace and identity

| Item | Approved value | Effective value | Evidence | Match |
|---|---|---|---|---|
| Plan / contract tier | Enterprise (ACME-PUR-2026-014) | Enterprise (ACME-PUR-2026-014) | IQ-05 | Match |
| Organisation / workspace identifier | organisation "Acme MedSoft", UUID `0f3c9a1e-...` (fictional) | organisation "Acme MedSoft", UUID `0f3c9a1e-...` (fictional) | IQ-02 | Match |
| SSO enforced (identity provider) | yes, corporate identity provider (SAML) | yes | IQ-02 | Match |
| Client login enforcement (method, organisation pin) | `forceLoginMethod` "claudeai"; `forceLoginOrgUUID` [Acme UUID]; `allowedProviders` ["anthropic"] | as approved; foreign and personal logins refused | IQ-02 | Match |
| Owners / admins of the vendor console (names) | Jordan Demo, Casey Admin | Jordan Demo, Casey Admin | IQ-02 | Match |
| Seat list export (date, count, all trained) | all seats named and trained | 2026-10-20, 14 seats, all trained | IQ-02 | Match |
| Personal accounts prohibited for QMS work | yes | yes (login enforcement and seat reconciliation) | IQ-02 | Match |
| CI / automation credentials (owner, scope, storage) | One Console API key, owner Engineering Lead, organisation secret limited to qa-tooling and the review workflow | as approved | IQ-02 | Match |
| Agent / bot identities (from IQ-04) | `acme-claude-reviewer[bot]` (comments only); workflow token `contents: read` | as approved | IQ-04 | Match |

## 6. Permission mode and approval policy

| Item | Approved value | Effective value | Source (managed / project / user) | Match |
|---|---|---|---|---|
| Starting permission / approval mode | `permissions.defaultMode` "default" | "default" | managed | Match |
| Modes that are disabled | bypass (`disableBypassPermissionsMode` "disable"), auto (`disableAutoMode` "disable") | both disabled | managed | Match |
| Who decides escalated approvals (human only) | the developer at the prompt | as approved (auto mode disabled) | managed | Match |
| Mode used in CI / headless invocations | `--permission-mode dontAsk` passed explicitly, with `--allowedTools` | as approved | workflow files (code-owner protected) | Match |
| Lower scopes may add permission rules (yes / no) | no on developer machines (`allowManagedPermissionRulesOnly` true); CI variant without it, so `--allowedTools` applies | as approved | managed | Match |

## 7. Allow, ask and deny rules

| Rule | Type (allow / ask / deny / forbidden / prompt) | Source | Purpose / requirement | Known limitation |
|---|---|---|---|---|
| `Read(./.env)`, `Read(./.env.*)`, `Read(./secrets/**)` | deny | managed | Keep secrets out of context (REQ-09) | Read denies do not stop subprocesses; sandbox `denyRead` and credential rules cover them |
| `Edit(./.github/workflows/**)`, `Edit(./.github/CODEOWNERS)`, `Edit(./.claude/settings.json)` | deny | managed | Agent does not edit gates or its own configuration (REQ-06) | Shell edits are covered by the policy hook (section 9) and code-owner review |
| `Bash(gh pr merge *)`, `Bash(gh pr review *)` | deny | managed | AI does not merge or review (REQ-02) | Matches command text only (`sh -c` workaround reproduced in OQ-08); the server-side gate is binding |
| `Bash(git push *)` | ask | managed | A person confirms every push (REQ-04) | Same text-matching limitation; protected branch enforced by the code host |

## 8. Sandbox and network

| Item | Approved value | Effective value | Source | Match |
|---|---|---|---|---|
| Sandbox enabled; fails closed if unavailable | `sandbox.enabled` true, `sandbox.failIfUnavailable` true | true / true | managed | Match |
| Unsandboxed retries allowed | no (`sandbox.allowUnsandboxedCommands` false) | false | managed | Match |
| Writable paths beyond the workspace | none | none | managed | Match |
| Read-denied paths (credentials, secrets) | `sandbox.credentials`: `~/.aws/credentials` deny; `.env`, `secrets/` via deny rules | as approved | managed | Match |
| Network allowlist (domains) and who may extend it | `github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`; `allowManagedDomainsOnly` true; extended only by change record (Engineering Lead) | as approved | managed | Match |
| Secret environment variables stripped from subprocesses | Developer machines hold no long-lived tokens in the environment (credential helper); CI secrets scoped to the step | as approved | endpoint policy, workflow | Match |
| Cloud environment network level (if a cloud surface is used) | n/a (no cloud surface; cloud sessions disabled for the organisation) | n/a | admin console | Match |

## 9. Hooks

| Event | Matcher | Handler (command / URL) and SHA-256 | Source | Behaviour on failure (blocks / continues) | Purpose |
|---|---|---|---|---|---|
| `PreToolUse` | `Bash` | `/etc/claude-code/hooks/deny-gate-files.sh`, `4a736be37e272045`... | managed (script deployed by endpoint management) | blocks (`"onFailure": "block"`) | Deny shell commands that modify `.github/`, `CODEOWNERS` or `.claude/` (REQ-06) |

Only managed hooks may run: yes (`allowManagedHooksOnly`: true, on developer machines and runners)

User-installed mods: restricted (`pluginConfigs` `cc-plugin-sec-default@builtin` option `allowManagedModsOnly` true, `disableSideloadFlags` true; OQ-09)

## 10. MCP servers, connectors and plugins

| Name | Identity (command or URL) | Access (read / write) and scope | Approval mode for tool calls | Allowed by (managed / project / user) | Purpose |
|---|---|---|---|---|---|
| none | - | - | - | - | No MCP servers, connectors or plugins are approved in this baseline |

Only managed MCP servers may run: yes (`allowManagedMcpServersOnly`: true; no managed servers are defined, so none run)

## 11. Instruction files and hashes

| Path | Scope (managed / user / repository) | SHA-256 | Commit | Protected by CODEOWNERS / code-owner review | Owner |
|---|---|---|---|---|---|
| Managed `CLAUDE.md` (or managed `claudeMd` key) | managed | `f9a3f26afb440dfd`... | n/a (endpoint management package 2026.10.1) | n/a | Engineering Lead |
| `CLAUDE.md` / `CLAUDE.local.md` | repository / local | lumen-core `8b066e6162d6d239`...; lumen-app `d47226f12464e765`...; `CLAUDE.local.md` not used (gitignored) | `4f2a91c`, `a81d0e3` | yes | Repository owner |
| `AGENTS.md` | repository | qa-tooling `d8df52b862f614af`... | `c3e7b12` | yes | Repository owner |
| `.claude/` directory (settings, hook scripts, skills, subagents) | repository | lumen-core `.claude/settings.json` `963475cdddb75f79`...; no hooks, skills or subagents | `4f2a91c` | yes | Repository owner |
| `.mcp.json` | repository | absent in all repositories | - | yes (path listed in CODEOWNERS) | Repository owner |
| CI workflows that invoke AI tools | repository | `claude-review.yml` `54b500babb2d4c1e`...; `test-gap-report.yml` `3291f1419f721854`... | `91be4d0`, `5d0c6aa` | yes | Engineering Lead |
| PR template (AI-assistance and model fields) | repository | `.github/pull_request_template.md` `e726f005260dc211`... (same file in all repositories) | `0e19f7b` | yes | Head of QA |
| `CODEOWNERS` | repository | `393cfde55aaceeda`... | `77ac2e9` | n/a | Engineering Lead |

Agent instruction files are guidance to the model, not enforcement. Because some review bots read them from the PR branch, they must be protected by code-owner review so that a PR cannot rewrite its own review rules (example: `examples/github/CODEOWNERS.example`). Changes that do not alter permissions, hooks or MCP servers follow T8b of ACME-VAL-CLAUDE-08: the reviewed PR is the change record and the hashes above are refreshed at the periodic review.

## 12. Approved models and model policy

Model policy: **envelope**.

Any model matching an entry below may be used, because its output is independently verified downstream (human review and CI). Each new model or model version passes MA-01 before use, and the model used is recorded per PR / session.

| Envelope entry | Pre-authorised pattern (ACME-VAL-CLAUDE-04 section 5.2) | Admitted ids in the enforced allow-list | Enforcement mechanism | MA-01 admission record | Date admitted |
|---|---|---|---|---|---|
| `anthropic-model-a` | `anthropic-model-a-v*` | `anthropic-model-a` | managed `availableModels` with `availableModelsMatch` "exact" and `enforceAvailableModels` true (enforced on every surface in scope) | CLAUDE-ADM-0001 | 2026-10-23 |
| `anthropic-model-b` | `anthropic-model-b-v*` | `anthropic-model-b` | as above (enforced) | CLAUDE-ADM-0002 | 2026-10-23 |

The enforced allow-list holds admitted model ids only, never the pre-authorised patterns; an id is added after its admission record is approved.

| Item | Approved value | Effective value | Match |
|---|---|---|---|
| Central model restriction available and enabled | yes | yes (OQ-10: 3 of 3 attempts with a non-approved id refused or substituted) | Match |
| Default / starting model | `anthropic-model-a` (managed `model`, starting default only) | `anthropic-model-a` | Match |
| Fallback models (all inside the envelope) | none configured (`fallbackModel` unset; `switchModelsOnFlag` unset) | none | Match |
| How the model used is recorded (trailer, PR template, log, telemetry) | PR template model field; telemetry model attribute (OpenTelemetry to the Acme collector) | as approved | Match |

Keys: `availableModels` (the admitted exact ids), `enforceAvailableModels` true, `availableModelsMatch` `"exact"` (managed-only), `deniedModels` (managed-only, for known unadmitted ids), `model` (starting default only, not a lock), `fallbackModel`, `switchModelsOnFlag`. With the default prefix matching a listed id would also permit later versions, which would make a new model selectable before admission; the kit's glob patterns are notation for ACME-VAL-CLAUDE-04 and ACME-VAL-CLAUDE-08 only.

## 13. Logging, telemetry and retention

| Item | Approved value | Effective value | Match |
|---|---|---|---|
| Telemetry / audit export enabled, destination, set from a managed source | `CLAUDE_CODE_ENABLE_TELEMETRY` 1, OTLP to the internal collector, `OTEL_LOG_MANAGED_SETTINGS` 1, all in managed `env` | as approved | Match |
| Prompt and response content logged (default redacted) | no (default redaction kept) | no | Match |
| Local transcripts: location, retention, who can read them | `~/.claude/projects/`, `cleanupPeriodDays` 30, only the developer (encrypted disk) | as approved | Match |
| Vendor-side logs / compliance export and their retention | Standard commercial retention (30 days); `DISABLE_FEEDBACK_COMMAND` 1 | as approved | Match |
| Code-host audit log export or streaming | Weekly export of the organisation audit log into the evidence store | as approved (last export 2026-10-14) | Match |
| CI log, check and artifact retention (GitHub: since 2026-10-01 also checks and commit statuses; private repositories up to 400 days) | 400 days on every repository in scope (raised from 90 on 2026-10-20); review records and check runs exported on merge | as approved | Match |
| Evidence archived into the QMS (where, how often) | eQMS evidence library VAL-2026-AI; on merge (workflow) and weekly (audit log) | as approved | Match |

## 14. Server-side controls (code host)

Evidence: the output of `python3 checks/check_github_gates.py --repo OWNER/REPO --branch main --prs 20 --operator "<name>" --out evidence/CLAUDE/IQ-03/` plus the exports below, per repository. Captured for this revision: the ACME-VAL-GEN-03 protection export `evidence/GEN/OQ-03/20261021-protection-export-4-repositories.json` and the gate-script runs in `evidence/GEN/OQ-01/` (configuration part, 2026-10-21).

| Item | Approved value | Effective value (per repository) | Match |
|---|---|---|---|
| Required approving reviews (`required_approving_review_count`) | at least 1 | 1 (organisation ruleset "protect-main", all 5 repositories) | Match |
| Dismiss stale reviews on push | true | true (`dismiss_stale_reviews_on_push`) | Match |
| Require approval of the most recent push (`require_last_push_approval`) | true | true | Match |
| Require code-owner review (agent instruction files and CI under CODEOWNERS) | true | true (`require_code_owner_review`); CODEOWNERS: every path, including `.github/`, agent configuration and instruction files, owned by the human team `@acme-medsoft/qualified-reviewers` | Match |
| Admins included (`enforce_admins`) or no bypass actors | true | Rulesets only (no classic protection); no bypass actors | Match |
| Ruleset bypass actors and `bypass_mode` (no "exempt") | none | none | Match |
| Required status checks, each pinned to its app (`app_id` / `integration_id`) | `ci / unit-tests`, `ci / sast`, `soup-gate`, `pr-template-check`, all pinned to the GitHub Actions app | as approved (`integration_id` set on each) | Match |
| Force pushes and branch deletion blocked | true | true (`non_fast_forward`, `deletion`) | Match |
| Actions may approve PRs (`can_approve_pull_request_reviews`, repository and organisation) | false | false / false | Match |
| Secret scanning push protection (`security_and_analysis`) | enabled | enabled on all 5 repositories | Match |
| Push-protection bypass / exemptions for bots and agents | none, or justified | none | Match |
| Actions log and check retention (`actions/permissions/artifact-and-log-retention`) | maximum allowed (400 days for private repositories), or check evidence exported on merge | 400 days on all 5 repositories (since 2026-10-20); evidence-export workflow active on all repositories | Match |
| Agent-authored PRs (author is a bot or a machine user used by an agent) | 2 approvals, or code-owner approval by a human team | repository ruleset `agent-prs` (2 approving reviews) on qa-tooling and val-sandbox, the only repositories where an agent identity may open PRs; no Claude Code surface opens PRs under its own identity | Match |
| Dependency / SOUP gate as a required check (`checks/soup_gate.py` or equivalent) | required, pinned to its app | `soup-gate` (built from `checks/soup_gate.py`), pinned to the GitHub Actions app | Match |
| PR template with AI-assistance fields (`examples/github/pull_request_template.md`) | present | `.github/pull_request_template.md` in all 5 repositories; `pr-template-check` required | Match |
| AI features of the code host (for example Copilot code review approval settings), even if not the tool under validation | approvals not counted | Copilot not licensed in the organisation; policy "Allow Copilot to approve pull requests" disabled at enterprise level; organisation and repository Copilot approval settings off; enterprise "Default policy for new features" set explicitly to disabled on 2026-10-20 (ACME-VAL-GEN-03 OQ-04) | Match |

Exports: `python3 checks/mirror_protection.py --from OWNER/REPO --operator "<name>" --out evidence/CLAUDE/IQ-03/` (export only, without `--to`), or `gh api repos/{owner}/{repo}/branches/main/protection`, `gh api "repos/{owner}/{repo}/rulesets?includes_parents=true"` and each ruleset by id, `gh api repos/{owner}/{repo}/rules/branches/main`, `gh api repos/{owner}/{repo}/actions/permissions/workflow`, `gh api orgs/{org}/actions/permissions/workflow`, `gh api repos/{owner}/{repo} --jq '.security_and_analysis'`. Ruleset history is limited to 180 days (and is an Enterprise Cloud feature), so keep each baseline export in the QMS.

## 15. Tool-specific configuration locations

Precedence (highest first): managed settings > command-line `--settings` > `.claude/settings.local.json` > `.claude/settings.json` > `~/.claude/settings.json`. List keys such as permission rules merge across files, and a deny anywhere beats an allow anywhere. Managed sources are ranked server-managed > MDM (plist / HKLM) > managed files (`managed-settings.json`, then `managed-settings.d/*.json` in alphabetical order, later files replacing scalars and lists being combined) > HKCU; under the default `managedSourcesBehavior` `"first-wins"` only the highest source that delivers a policy is used, and `/status` names the skipped ones.

| Location | Scope | What to record |
|---|---|---|
| macOS `/Library/Application Support/ClaudeCode/managed-settings.json`; Linux / WSL `/etc/claude-code/managed-settings.json`; Windows `C:\Program Files\ClaudeCode\managed-settings.json`; drop-ins in `managed-settings.d/*.json` beside it; `managed-mcp.json` in the same directory | managed (file) | Full content and SHA-256; file owner and permissions |
| macOS managed preferences domain `com.anthropic.claudecode`; Windows `HKLM\SOFTWARE\Policies\ClaudeCode`, value `Settings` (JSON). `HKCU\SOFTWARE\Policies\ClaudeCode` is user-writable and not an admin source | managed (MDM) | Profile / registry export and SHA-256 |
| claude.ai admin console: Organization settings > Claude Code > Managed settings (cached locally in `~/.claude/remote-settings.json`) | managed (server) | Export or screenshot; owner who changed it. The vendor calls this a client-side control, not a security boundary; it is skipped with third-party cloud providers or a custom base URL, and not delivered to Console API-key sessions (typical in CI) |
| `managedSourcesBehavior` (`"first-wins"` default, or `"merge"`) | managed | Which managed sources are combined; `/status` "Skipped sources" |
| `~/.claude/settings.json` | user | Content and SHA-256 on reference machines |
| `.claude/settings.json`, `.claude/settings.local.json`, `.mcp.json` | repository / local | Content and SHA-256 |
| Managed `CLAUDE.md` (`/Library/Application Support/ClaudeCode/CLAUDE.md`, `/etc/claude-code/CLAUDE.md`, `C:\Program Files\ClaudeCode\CLAUDE.md`) | managed | SHA-256 |
| `~/.claude/projects/<project>/<session>.jsonl`, `~/.claude/history.jsonl` | local records | Retention (`cleanupPeriodDays`), access |
| `anthropics/claude-code-action` step (`claude_args`, `settings` inputs) and the app used | CI | Pinned SHA, inputs, app permissions |
| Organisation switches for Remote Control and cloud sessions (admin console); per device `disableRemoteControl` | organisation | State |

Keys to record (managed unless stated):

- Permission mode: `permissions.defaultMode`, `permissions.disableBypassPermissionsMode` (`"disable"`), `disableAutoMode` (`"disable"`). Auto mode, in which a classifier approves actions, is the built-in starting mode for interactive sessions in recent versions, so set the mode explicitly.
- Rules: `permissions.allow` / `ask` / `deny`, `allowManagedPermissionRulesOnly`, `permissions.blockReadsOutsideWorkingDirectories`.
- Hooks: `hooks` (with `"onFailure": "block"` on policy hooks), `allowManagedHooksOnly`.
- MCP: `allowManagedMcpServersOnly`.
- Sandbox: `sandbox.enabled`, `sandbox.failIfUnavailable`, `sandbox.allowUnsandboxedCommands`, `sandbox.network.allowedDomains`, `sandbox.network.allowManagedDomainsOnly`, `sandbox.filesystem.denyRead`, `sandbox.filesystem.allowManagedReadPathsOnly`, `sandbox.credentials`.
- Models: see section 12.
- Login and provider: `forceLoginMethod`, `forceLoginOrgUUID`, `allowedProviders`, `forceRemoteSettingsRefresh`.
- Versions: `requiredMinimumVersion`, `requiredMaximumVersion`, `autoUpdatesChannel`, `env.DISABLE_UPDATES`.
- Provenance: `attribution` (`commit`, `pr`, `sessionUrl`); set it in managed settings so instruction files cannot change it.
- Records and data: `cleanupPeriodDays`, `env.CLAUDE_CODE_ENABLE_TELEMETRY` and `OTEL_*` variables (including `OTEL_LOG_MANAGED_SETTINGS`), `env.CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `env.DISABLE_FEEDBACK_COMMAND`.
- Built-in plugins and extensions: `pluginConfigs` (for example instruction-file selection), and the managed restriction of user-installed mods: `pluginConfigs` `cc-plugin-sec-default@builtin` option `allowManagedModsOnly` true together with `disableSideloadFlags` true (recommended for developer machines); `allowManagedHooksOnly` (recommended for CI and agent runners, where user hooks, status lines and similar conveniences are not needed). Record which extensions are allowed.

Effective-configuration evidence: `/status` ("Setting sources", "Skipped sources"), `claude doctor`, and the `claude_code.managed_settings_resolved` telemetry event with `managed_settings.resolved_sha256` (identical digests mean identical policy).

## 16. Who may change the configuration

| Configuration item | Owner | Who may change it | How the change is approved | Record |
|---|---|---|---|---|
| Managed / admin-enforced settings and requirements | Engineering Lead | Named administrators below | Change record approved by the Head of QA before deployment (ACME-VAL-CLAUDE-08) | New baseline revision |
| Vendor admin console (workspace, SSO, policies, model availability) | Engineering Lead | Named console administrators below | As above | Console audit log export + baseline revision |
| Repository agent configuration that alters permissions, hooks or MCP servers | Repository owner | Any developer, through a PR | Change record approved by the Head of QA (T8a) plus code-owner review | Change record + PR history + baseline revision |
| Other repository instruction files and agent configuration | Repository owner | Any developer, through a PR | Code-owner review by a designated QA reviewer; the reviewed PR is the change record (T8b); hashes refreshed at the periodic review | PR history |
| CI workflows that invoke AI tools | Repository owner | Any developer, through a PR | Code-owner review | PR history |
| Code-host protection, rulesets, Actions / approval settings | Engineering Lead | Organisation owners only | Change record approved before the change | Ruleset history / audit log export + baseline revision |
| Approved model envelope | Engineering Lead | Through an admission record (MA-01) or change record | Head of QA | ACME-VAL-CLAUDE-08 |
| User-level settings | Each developer | Each developer | Not controlled; they cannot weaken enforced settings (OQ-09) | n/a |

Named people with administrative rights (reviewed at every periodic review):

| Name | System | Right (owner / admin / local admin) | Granted on | Last reviewed |
|---|---|---|---|---|
| Jordan Demo | GitHub organisation `acme-medsoft` | owner | 2025-01-15 | 2026-10-20 |
| Casey Admin | GitHub organisation `acme-medsoft` | owner | 2025-01-15 | 2026-10-20 |
| Jordan Demo | Vendor admin console (organisation) | owner | 2026-01-05 | 2026-10-20 |
| Casey Admin | Vendor admin console (organisation) | admin | 2026-01-05 | 2026-10-20 |
| Casey Admin | Endpoint management (managed configuration files) | admin; local admin on managed laptops | 2025-01-15 | 2026-10-20 |

## 17. Approval of this baseline revision

Signed by the people themselves in the eQMS (in an e-signature system validated for 21 CFR Part 11 where FDA requirements apply, and meeting the organisation's eIDAS requirements in the EU); never typed by the AI tool or by another person.

| Step | Role | Name | Signature (eQMS / e-signature) | Date and time (UTC) |
|---|---|---|---|---|
| Approved values defined | Engineering Lead | Jordan Demo | [signed in eQMS] | 2026-10-19 |
| Effective values captured (IQ-03) | Validation Engineer | Alex Example | [signed in eQMS] | 2026-10-20 |
| Baseline approved | Head of QA | Sam Sample | [signed in eQMS] | 2026-10-23 |
