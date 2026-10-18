> FICTIONAL EXAMPLE - not a real validation record. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are invented to show what an executed package looks like. Model ids are placeholders, not real model names. Signatures are applied by each person in the eQMS and are shown here only as "[signed in eQMS]".

# ACME-VAL-CODEX-06 Configuration baseline: OpenAI Codex

| Field | Value |
|---|---|
| Document ID | ACME-VAL-CODEX-06 |
| Title | Configuration baseline |
| Organisation | Acme MedSoft |
| Tool / vendor | OpenAI Codex / OpenAI |
| Configuration owner (role) | Engineering Lead |
| Approved by (role) | Head of QA |
| Rendered | 2026-10-18 (kit 0.1.0) |

Related documents: ACME-VAL-CODEX-05 Test protocol (IQ-03 verifies this baseline) · ACME-VAL-CODEX-08 Change and revalidation (how this baseline changes) · ACME-VAL-GEN-01 Work instruction · ACME-VAL-GEN-03 Code-host gate qualification.

## 1. Purpose

This record is the approved, versioned configuration of OpenAI Codex at Acme MedSoft (owner: Engineering Lead). It separates **configuration** (versionable, baselined, change-controlled: settings, permission rules, sandbox, hooks, MCP servers, instruction files, model envelope, code-host gates) from **behaviour** (variable: models can change without a version change, so behaviour is covered by monitoring, the model admission check MA-01 and periodic re-tests in ACME-VAL-CODEX-08).

The binding controls live server-side (code host and CI). The tool's local configuration is defence in depth and is recorded here so that drift can be detected.

Regulatory anchors:
- ISO 13485:2016 §4.1.6 (validated state maintained after changes), §4.2.4 (agent configuration and instruction files are controlled items), §4.2.5 (records).
- 21 CFR Part 820 (QMSR), which incorporates ISO 13485:2016 by reference (§820.10). 21 CFR Part 11 applies to the records of this package that are kept or signed electronically.
- IEC 62304: tools and settings used to develop the software are supporting items under configuration control (§5.1.10, §8.1).

## 2. How to fill in this record

1. The Engineering Lead writes the **approved value** of every item before IQ-03.
2. The executor of IQ-03 captures the **effective value**:
   - run `python3 checks/capture_baseline.py --tool codex --repo <path-to-repo> --operator "<name>" --out evidence/CODEX/IQ-03/` on each reference machine and runner, and copy the values and file hashes from its output;
   - fill the manual fields (admin console, code host) from exports, or from dated screenshots when no export exists.
3. Mark each row Match / No match. A "No match" is a deviation in ACME-VAL-CODEX-05.
4. Any later change to an approved value follows ACME-VAL-CODEX-08 and produces a new baseline revision; earlier revisions are kept.

## 3. Baseline identification

| Field | Value |
|---|---|
| Baseline ID / revision | CODEX-BL-01 / rev 1 |
| Capture date (UTC) | 2026-10-20 |
| Captured by (name) | Alex Example |
| Capture method | capture script (version 0.1.0) plus manual fields (admin console, code host) |
| Evidence files and SHA-256 | `evidence/CODEX/IQ-03/baseline_codex_20261020T102030Z.json`, `evidence/CODEX/IQ-03/baseline_codex_20261020T110910Z.json`, `evidence/CODEX/IQ-03/baseline_codex_20261020T121540Z.json` (SHA-256 in ACME-VAL-CODEX-05, evidence index) |
| Machines / runners captured | ACME-MBP-017 (macOS 15, MDM payload), ACME-WS-004 (Ubuntu 24.04, `/etc/codex/requirements.toml`), test VM ACME-VM-SBX-01; cloud-managed requirements (export) |
| Supersedes revision | none (first baseline) |
| Change record that created this revision | CR-2026-040 (configuration baseline for the initial validation) |

## 4. Versions per surface

| Surface | Validated version(s) (ACME-VAL-CODEX-04 section 3.1) | Effective version | Install method and update control | Evidence | Match |
|---|---|---|---|---|---|
| Local CLI / IDE | codex-cli 0.163.0 | codex-cli 0.163.0 | Endpoint-managed package; `check_for_update_on_startup = false` in requirements | IQ-01 | Match |
| Cloud agent | vendor-hosted (no client version) | vendor-hosted, recorded 2026-10-20 | Vendor-controlled; workspace setting for group `acme-codex-cloud`; monitored (ACME-VAL-CODEX-08) | IQ-01 | Match |

Record the output of `codex --version`. Update control: `check_for_update_on_startup` (enforceable from requirements). Installs through a package manager need their own version pinning. For `openai/codex-action` record the pinned tag or SHA and the explicit `codex-version` input.

## 5. Account, workspace and identity

| Item | Approved value | Effective value | Evidence | Match |
|---|---|---|---|---|
| Plan / contract tier | Enterprise workspace (ACME-PUR-2026-019) | Enterprise workspace (ACME-PUR-2026-019) | IQ-05 | Match |
| Organisation / workspace identifier | workspace "Acme MedSoft", id `ws-7c21...` (fictional) | workspace "Acme MedSoft", id `ws-7c21...` (fictional) | IQ-02 | Match |
| SSO enforced (identity provider) | yes, corporate identity provider (SAML) | yes | IQ-02 | Match |
| Client login enforcement (method, organisation pin) | `allowed_login_methods` ["chatgpt"]; `allowed_chatgpt_workspaces` [Acme id]; `cli_auth_credentials_store` "auto" (local requirements and MDM) | as approved; sign-in tested on macOS, Linux and the headless test VM; foreign and personal logins refused | IQ-02 | Match |
| Owners / admins of the vendor console (names) | Jordan Demo, Casey Admin | Jordan Demo, Casey Admin | IQ-02 | Match |
| Seat list export (date, count, all trained) | all seats named and trained | 2026-10-20, 9 members, all trained | IQ-02 | Match |
| Personal accounts prohibited for QMS work | yes | yes (login enforcement and seat reconciliation) | IQ-02 | Match |
| CI / automation credentials (owner, scope, storage) | none (no CI use of Codex; API keys not issued) | as approved | IQ-02 | Match |
| Agent / bot identities (from IQ-04) | vendor GitHub connector identity for cloud tasks and `@codex review` (IQ-04) | as approved | IQ-04 | Match |

## 6. Permission mode and approval policy

| Item | Approved value | Effective value | Source (managed / project / user) | Match |
|---|---|---|---|---|
| Starting permission / approval mode | `approval_policy` "on-request" | "on-request" | requirements (`allowed_approval_policies` ["on-request"]) and user default | Match |
| Modes that are disabled | approval policy "never"; sandbox "danger-full-access" (not in `allowed_sandbox_modes`) | as approved (OQ-08, OQ-09: fallback with notice) | requirements | Match |
| Who decides escalated approvals (human only) | the user (`allowed_approvals_reviewers` ["user"]) | "user" | requirements | Match |
| Mode used in CI / headless invocations | n/a (no CI surface); MA-01 uses `codex exec --sandbox workspace-write` | as approved | runner command line | Match |
| Lower scopes may add permission rules (yes / no) | user rules may add restrictions only; the most restrictive decision wins | as approved | requirements | Match |

## 7. Allow, ask and deny rules

| Rule | Type (allow / ask / deny / forbidden / prompt) | Source | Purpose / requirement | Known limitation |
|---|---|---|---|---|
| prefix `git push` | prompt | requirements `[rules] prefix_rules` | A person confirms every push outside the sandbox (REQ-04) | Rules govern commands outside the sandbox; not a complete OS policy engine; server-side gate is binding |
| prefix `gh pr merge` | forbidden | requirements `[rules] prefix_rules` | AI does not merge (REQ-02) | As above |
| prefix `gh pr review` | forbidden | requirements `[rules] prefix_rules` | AI does not submit reviews or approvals (REQ-02) | As above |
| `deny_read` `/**/*.env`, `~/.ssh` | deny (read) | requirements `[permissions.filesystem]` | Keep secrets out of context (REQ-09) | Denying `~/.ssh` also blocks git over SSH; Acme uses HTTPS |

## 8. Sandbox and network

| Item | Approved value | Effective value | Source | Match |
|---|---|---|---|---|
| Sandbox enabled; fails closed if unavailable | `sandbox_mode` "workspace-write"; `allowed_sandbox_modes` ["read-only", "workspace-write"] | as approved | requirements and user default | Match |
| Unsandboxed retries allowed | only on request, decided by the user (`on-request`) | as approved | requirements | Match |
| Writable paths beyond the workspace | none (`[sandbox_workspace_write] writable_roots = []`) | none | user default | Match |
| Read-denied paths (credentials, secrets) | `/**/*.env`, `~/.ssh` | as approved | requirements | Match |
| Network allowlist (domains) and who may extend it | no network inside the local sandbox (`network_access = false`); `web_search` "disabled"; changed only by change record | as approved | user default; requirements `allowed_web_search_modes` | Match |
| Secret environment variables stripped from subprocesses | yes: `shell_environment_policy` `inherit = "all"`, `ignore_default_excludes = false`, filters `AWS_*`, `*PASSWORD*`, `*CREDENTIAL*` excluded | as approved (OQ-08 canary absent, build variables present) | user default | Match |
| Cloud environment network level (if a cloud surface is used) | environment `acme-sandbox-env`: internet access off during the agent phase | as approved | workspace admin console | Match |

## 9. Hooks

| Event | Matcher | Handler (command / URL) and SHA-256 | Source | Behaviour on failure (blocks / continues) | Purpose |
|---|---|---|---|---|---|
| `PreToolUse` | shell commands | `/etc/codex/hooks/deny-gate-edits.sh`, `6dbdc0cacaa1c022`... (hook configuration format verified against the vendor's current documentation on 2026-10-20) | managed (script delivered by MDM / endpoint management) | continues: only an explicit deny blocks (OQ-08) | Deny shell commands that modify `.github/`, `CODEOWNERS`, `AGENTS.md` or `.codex/` (REQ-06) |

Only managed hooks may run: yes (`allow_managed_hooks_only = true` with `[features] hooks = true` in requirements)

## 10. MCP servers, connectors and plugins

| Name | Identity (command or URL) | Access (read / write) and scope | Approval mode for tool calls | Allowed by (managed / project / user) | Purpose |
|---|---|---|---|---|---|
| none | - | - | - | - | No MCP servers are approved in this baseline |

Only managed MCP servers may run: yes (requirements `[mcp_servers]` is deliberately an empty table, which disables every server; no MCP server is approved in this baseline)

## 11. Instruction files and hashes

| Path | Scope (managed / user / repository) | SHA-256 | Commit | Protected by CODEOWNERS / code-owner review | Owner |
|---|---|---|---|---|---|
| `AGENTS.md` / `AGENTS.override.md` in `CODEX_HOME` | user / managed image | `AGENTS.md` `4ebacba7dae0b339`... (endpoint package); no override file | n/a | n/a | Engineering Lead |
| `AGENTS.md` / `AGENTS.override.md` (project root down to working directory) | repository | qa-tooling `b49fd24808265019`...; lumen-core `250d374595551df1`...; no override files | `c3e7b12`, `4f2a91c` | yes | Repository owner |
| `.codex/config.toml`, `.codex/hooks.json`, `.codex/rules/` | repository | absent in all repositories | - | yes (paths listed in CODEOWNERS) | Repository owner |
| Files named in `project_doc_fallback_filenames` | repository | key not set | - | n/a | Engineering Lead |
| CI workflows that invoke AI tools | repository | none for Codex | - | yes | Engineering Lead |
| PR template (AI-assistance and model fields) | repository | `.github/pull_request_template.md` `e726f005260dc211`... (same file in all repositories) | `0e19f7b` | yes | Head of QA |
| `CODEOWNERS` | repository | `393cfde55aaceeda`... | `77ac2e9` | n/a | Engineering Lead |

Agent instruction files are guidance to the model, not enforcement. Because some review bots read them from the PR branch, they must be protected by code-owner review so that a PR cannot rewrite its own review rules (example: `examples/github/CODEOWNERS.example`). Changes that do not alter permissions, hooks or MCP servers follow T8b of ACME-VAL-CODEX-08: the reviewed PR is the change record and the hashes above are refreshed at the periodic review.

## 12. Approved models and model policy

Model policy: **envelope**.

Any model matching an entry below may be used, because its output is independently verified downstream (human review and CI). Each new model or model version passes MA-01 before use, and the model used is recorded per PR / session.

| Envelope entry | Pre-authorised pattern (ACME-VAL-CODEX-04 section 5.2) | Admitted ids in the enforced allow-list | Enforcement mechanism | MA-01 admission record | Date admitted |
|---|---|---|---|---|---|
| `openai-model-a` | `openai-model-a-v*` | n/a: no enforced allow-list (admitted id `openai-model-a` recorded here) | monitored, not enforced (no verified client-side enforcement); recorded per session; weekly detection check, time-boxed admission after detection (ACME-VAL-CODEX-04 section 5.2) | CODEX-ADM-0001 | 2026-10-23 |
| `openai-model-b` | `openai-model-b-v*` | n/a (admitted id `openai-model-b` recorded here) | as above | CODEX-ADM-0002 | 2026-10-23 |

The enforced allow-list holds admitted model ids only, never the pre-authorised patterns; an id is added after its admission record is approved.

| Item | Approved value | Effective value | Match |
|---|---|---|---|
| Central model restriction available and enabled | not available (verified 2026-10-22 against the vendor's current documentation) | not available | Match |
| Default / starting model | `openai-model-a` (`model` in user default; a default only) | `openai-model-a` | Match |
| Fallback models (all inside the envelope) | none configured | none | Match |
| How the model used is recorded (trailer, PR template, log, telemetry) | PR template model field; `codex.conversation_starts` telemetry event; weekly model-use check against the envelope | as approved | Match |

No client-side model allowlist enforcement was verified: requirements `[models.new_thread]` only sets defaults, and explicit `--model`, `--config` or `--profile` overrides it. Unless the vendor's current documentation shows an enforcement key for your version, record "monitored, not enforced" and rely on recording (`codex.conversation_starts` telemetry, `codex exec --json`) plus PQ-01.

## 13. Logging, telemetry and retention

| Item | Approved value | Effective value | Match |
|---|---|---|---|
| Telemetry / audit export enabled, destination, set from a managed source | `[otel]` OTLP exporter to the internal collector, `log_user_prompt = false`, delivered with the managed defaults | as approved | Match |
| Prompt and response content logged (default redacted) | no (`log_user_prompt = false`) | no | Match |
| Local transcripts: location, retention, who can read them | `history.persistence = "none"`; session files under `~/.codex/sessions` removed by endpoint policy after 30 days; only the developer | as approved | Match |
| Vendor-side logs / compliance export and their retention | Workspace retention as contracted; Compliance API records (30 days) exported weekly; `analytics` and `feedback` disabled | as approved | Match |
| Code-host audit log export or streaming | Weekly export of the organisation audit log into the evidence store | as approved (last export 2026-10-14) | Match |
| CI log, check and artifact retention (GitHub: since 2026-10-01 also checks and commit statuses; private repositories up to 400 days) | 400 days on every repository in scope (raised from 90 on 2026-10-20); review records and check runs exported on merge | as approved | Match |
| Evidence archived into the QMS (where, how often) | eQMS evidence library VAL-2026-AI; on merge (workflow) and weekly (audit log, Compliance API) | as approved | Match |

## 14. Server-side controls (code host)

Evidence: the output of `python3 checks/check_github_gates.py --repo OWNER/REPO --branch main --prs 20 --operator "<name>" --out evidence/CODEX/IQ-03/` plus the exports below, per repository. Captured for this revision: the ACME-VAL-GEN-03 protection export `evidence/GEN/OQ-03/20261021-protection-export-4-repositories.json` and the gate-script runs in `evidence/GEN/OQ-01/` (configuration part, 2026-10-21).

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
| Agent-authored PRs (author is a bot or a machine user used by an agent) | 2 approvals, or code-owner approval by a human team | repository ruleset `agent-prs` (2 approving reviews) on qa-tooling and val-sandbox, the only repositories where the Codex cloud agent may open PRs | Match |
| Dependency / SOUP gate as a required check (`checks/soup_gate.py` or equivalent) | required, pinned to its app | `soup-gate` (built from `checks/soup_gate.py`), pinned to the GitHub Actions app | Match |
| PR template with AI-assistance fields (`examples/github/pull_request_template.md`) | present | `.github/pull_request_template.md` in all 5 repositories; `pr-template-check` required | Match |
| AI features of the code host (for example Copilot code review approval settings), even if not the tool under validation | approvals not counted | Copilot not licensed in the organisation; policy "Allow Copilot to approve pull requests" disabled at enterprise level; organisation and repository Copilot approval settings off; enterprise "Default policy for new features" set explicitly to disabled on 2026-10-20 (ACME-VAL-GEN-03 OQ-04) | Match |

Exports: `python3 checks/mirror_protection.py --from OWNER/REPO --operator "<name>" --out evidence/CODEX/IQ-03/` (export only, without `--to`), or `gh api repos/{owner}/{repo}/branches/main/protection`, `gh api "repos/{owner}/{repo}/rulesets?includes_parents=true"` and each ruleset by id, `gh api repos/{owner}/{repo}/rules/branches/main`, `gh api repos/{owner}/{repo}/actions/permissions/workflow`, `gh api orgs/{org}/actions/permissions/workflow`, `gh api repos/{owner}/{repo} --jq '.security_and_analysis'`. Ruleset history is limited to 180 days (and is an Enterprise Cloud feature), so keep each baseline export in the QMS.

## 15. Tool-specific configuration locations

Codex has two layers: **defaults** that users can override (config files, profiles, legacy managed defaults) and **admin requirements** that users cannot override. When a user value conflicts with a requirement, the client falls back to an allowed value and notifies the user.

| Location | Scope | What to record |
|---|---|---|
| `/etc/codex/requirements.toml` (Unix including macOS); `%ProgramData%\OpenAI\Codex\requirements.toml` (Windows) | requirements (system) | Content, SHA-256, owner and permissions |
| Cloud-managed requirements (admin console, Agent Security / managed configurations; targets by group, user, platform) | requirements (cloud) | Export or screenshot of policy, targets and raw TOML |
| `/etc/codex/managed_config.toml` (legacy; its fields are reinterpreted as requirements, so a "default" also acts as an allowlist) | requirements (legacy) | Content and SHA-256 |
| macOS MDM domain `com.openai.codex`: key `requirements_toml_base64` (requirements, highest priority) and key `config_toml_base64` (managed defaults) | MDM | Decoded payload and SHA-256 |
| `/etc/codex/config.toml` (Windows `%ProgramData%\OpenAI\Codex\config.toml`) | system defaults | Content and SHA-256 |
| `~/.codex/config.toml` (`CODEX_HOME`); profile files `~/.codex/<name>.config.toml` | user | Content and SHA-256 on reference machines |
| `<repo>/.codex/config.toml`, `.codex/hooks.json`, rules (loaded only for trusted projects) | repository | Content and SHA-256 |
| `[projects."<path>"] trust_level` in user config | user | Trust state of each repository |
| `~/.codex/hooks.json`; `rules/` folders next to config layers (for example `~/.codex/rules/default.rules`) | user | Content and SHA-256 |
| `~/.codex/auth.json` or OS keyring (`cli_auth_credentials_store`) | credentials | Storage mode (no plaintext file when keyring is required) |
| `~/.codex/history.jsonl`, `~/.codex/sessions`, `log_dir` | local records | Retention settings, access |
| `openai/codex-action` step (`permission-profile`, `safety-strategy`, `codex-version`, `allow-users`, `allow-bots`) | CI | Pinned tag or SHA and inputs |

Keys to record:

- Approvals: `approval_policy` (`"on-request"`, `"never"` or the granular table) and requirements `allowed_approval_policies`; `approvals_reviewer` and `allowed_approvals_reviewers` (keep `"user"` so a person decides every escalation).
- Sandbox: `sandbox_mode` (`read-only`, `workspace-write`, `danger-full-access`) and `[sandbox_workspace_write]` (`writable_roots`, `network_access`), or permission profiles (`default_permissions`, `[permissions.<name>]`; beta) with requirements `allowed_sandbox_modes` and `allowed_permission_profiles`. If `sandbox_mode` appears in any loaded config, the legacy settings win over profiles.
- Rules and reads: requirements `[rules] prefix_rules` (decision `"prompt"` or `"forbidden"`), `[permissions.filesystem] deny_read`.
- Hooks: `allow_managed_hooks_only`, `[features] hooks = true` in requirements; non-managed hooks must be trusted by hash.
- MCP: requirements `[mcp_servers]` allowlist by name and identity (an empty table disables all servers).
- Network and web: `web_search` and `allowed_web_search_modes`.
- Environment: `shell_environment_policy` (`inherit`, `ignore_default_excludes`, `filters`).
- Login: requirements `allowed_login_methods`, `allowed_chatgpt_workspaces`, `cli_auth_credentials_store` (honoured only in the local system file or MDM); user `forced_login_method`, `forced_chatgpt_workspace_id`.
- Data: `enforce_residency`, `history.persistence`, `[otel]` (an OTLP exporter is a table with endpoint and protocol), `analytics.enabled`, `feedback.enabled`, `check_for_update_on_startup`.
- Models: see section 12.

Effective-configuration evidence: `codex --strict-config doctor`, `codex features list`, `codex login status`, `/status` and `/hooks` in the TUI, and the `codex.conversation_starts` telemetry event (records sandbox and approval policy).

Cloud: record the workspace roles for cloud use and environment management, each environment's internet access and domain allowlist, and who can use each shared environment. Cloud environments do not inherit local device policy or MDM.

## 16. Who may change the configuration

| Configuration item | Owner | Who may change it | How the change is approved | Record |
|---|---|---|---|---|
| Managed / admin-enforced settings and requirements | Engineering Lead | Named administrators below | Change record approved by the Head of QA before deployment (ACME-VAL-CODEX-08) | New baseline revision |
| Vendor admin console (workspace, SSO, policies, model availability) | Engineering Lead | Named console administrators below | As above | Console audit log export + baseline revision |
| Repository agent configuration that alters permissions, hooks or MCP servers | Repository owner | Any developer, through a PR | Change record approved by the Head of QA (T8a) plus code-owner review | Change record + PR history + baseline revision |
| Other repository instruction files and agent configuration | Repository owner | Any developer, through a PR | Code-owner review by a designated QA reviewer; the reviewed PR is the change record (T8b); hashes refreshed at the periodic review | PR history |
| CI workflows that invoke AI tools | Repository owner | Any developer, through a PR | Code-owner review | PR history |
| Code-host protection, rulesets, Actions / approval settings | Engineering Lead | Organisation owners only | Change record approved before the change | Ruleset history / audit log export + baseline revision |
| Approved model envelope | Engineering Lead | Through an admission record (MA-01) or change record | Head of QA | ACME-VAL-CODEX-08 |
| User-level settings | Each developer | Each developer | Not controlled; they cannot weaken enforced settings (OQ-09) | n/a |

Named people with administrative rights (reviewed at every periodic review):

| Name | System | Right (owner / admin / local admin) | Granted on | Last reviewed |
|---|---|---|---|---|
| Jordan Demo | GitHub organisation `acme-medsoft` | owner | 2025-01-15 | 2026-10-20 |
| Casey Admin | GitHub organisation `acme-medsoft` | owner | 2025-01-15 | 2026-10-20 |
| Jordan Demo | Vendor admin console (workspace) | owner | 2026-06-01 | 2026-10-20 |
| Casey Admin | Vendor admin console (workspace) | admin | 2026-06-01 | 2026-10-20 |
| Casey Admin | Endpoint management (managed configuration files) | admin; local admin on managed laptops | 2025-01-15 | 2026-10-20 |

## 17. Approval of this baseline revision

Signed by the people themselves in the eQMS (in an e-signature system validated for 21 CFR Part 11 where FDA requirements apply, and meeting the organisation's eIDAS requirements in the EU); never typed by the AI tool or by another person.

| Step | Role | Name | Signature (eQMS / e-signature) | Date and time (UTC) |
|---|---|---|---|---|
| Approved values defined | Engineering Lead | Jordan Demo | [signed in eQMS] | 2026-10-19 |
| Effective values captured (IQ-03) | Validation Engineer | Alex Example | [signed in eQMS] | 2026-10-20 |
| Baseline approved | Head of QA | Sam Sample | [signed in eQMS] | 2026-10-23 |
