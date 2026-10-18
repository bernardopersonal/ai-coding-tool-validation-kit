# OpenAI Codex: settings and notes for a validated state

These notes support the per-tool package (`06` configuration baseline, `05` IQ/OQ steps, `03` known guardrail limitations). Keys and flags were checked on 2026-10-18 against the official `openai/codex` and `openai/codex-action` repositories (configuration schema and source code at CLI 0.163.0, the latest stable release), and against a community mirror of the official documentation. The official documentation hosts could not be reached directly during the research, so spot-check the live pages before you include a setting in a controlled document. Codex changes quickly. Re-verify against the vendor's current documentation whenever you change the validated version.

Files:

- [`config.example.toml`](config.example.toml): **defaults**, for `~/.codex/config.toml`, `/etc/codex/config.toml` or managed defaults. Users can override these.
- [`requirements.example.toml`](requirements.example.toml): **admin-enforced requirements**, for `/etc/codex/requirements.toml`, MDM or cloud-managed policy. Users cannot override these.
- [`client-regression.example.json`](client-regression.example.json): example probes for `checks/client_regression.py`, the automated client regression (CS-3a) that gates a raise of the validated version. Confirm every expectation once on your validated version before you approve the file with the validation plan.

Both files parse as TOML. Replace the placeholder workspace id and paths before you deploy them.

## Two layers: defaults and requirements

**Defaults (users can override).** Lowest to highest precedence: built-in defaults, macOS managed preferences, system `/etc/codex/config.toml` (Windows `%ProgramData%\OpenAI\Codex\config.toml`), cloud config bundle, user `~/.codex/config.toml` (`CODEX_HOME`), profile file `~/.codex/<name>.config.toml`, project `.codex/config.toml` (only for trusted projects), runtime overrides (`--config`, UI). Legacy managed defaults (`/etc/codex/managed_config.toml`, MDM key `config_toml_base64`) override user config at launch, but users can still change settings during a run.

**Requirements (users cannot override).** Lowest to highest priority: `/etc/codex/requirements.toml` (Windows `%ProgramData%\OpenAI\Codex\requirements.toml`), cloud-managed requirements (Agent Security in the admin console, targeted by group, user or platform), legacy `managed_config.toml` fields reinterpreted as requirements, and macOS MDM `com.openai.codex` key `requirements_toml_base64`.

When a config value conflicts with a requirement, Codex **falls back to an allowed value and notifies the user**. OQ-09 should capture that notice. Note that legacy `managed_config.toml` values become allowlists: `approval_policy = X` becomes `allowed_approval_policies = [X]`, and `sandbox_mode = Y` becomes `allowed_sandbox_modes = ["read-only", Y]`.

**Cloud-managed requirements** are fetched at sign-in for ChatGPT Business and Enterprise. Codex keeps a signed cache, and loading fails rather than starting without the layer when there is no valid cache. Codex cloud environments do not inherit local device policy or MDM.

## Recent breaking changes to check in IQ

- `approval_policy = "untrusted"` was retired in 0.149.0 and can stop the client from starting. Use a per-project `trust_level = "untrusted"` in user config instead. `"on-failure"` is deprecated.
- `--full-auto` is no longer supported. Use `--sandbox workspace-write` explicitly.
- Since 0.134.0, profiles are separate files (`~/.codex/<name>.config.toml`, selected with `--profile`). `[profiles.x]` tables and the top-level `profile =` key are no longer read.
- Permission profiles (`default_permissions`, `[permissions.<name>]`, managed `allowed_permission_profiles`) are beta and need 0.138.0 or later. They do not compose with `sandbox_mode`: if `sandbox_mode` appears in any loaded config, or `--sandbox` is passed, the legacy settings win.
- Since 0.150.0, untrusted projects no longer supply project-level `AGENTS.md`.
- The commit-attribution setting was removed (May 2026), so add provenance trailers through the PR template or repository hooks (REQ-10).
- `codex mcp-server` was removed. Its replacement, the app server, is labelled experimental and not for production workloads.

`codex --strict-config` errors on config fields the installed version does not recognise. Use it in IQ-01 and IQ-03 to catch retired keys.

## Defaults: `config.example.toml`

| Key | Example | Why (REQ) | Caveat |
|---|---|---|---|
| `approval_policy` | `"on-request"` | The agent asks before escalating (REQ-07) | Accepts `"on-request"`, `"never"` or a granular table |
| `approvals_reviewer` | `"user"` | A person, not a reviewer agent, decides escalations (REQ-02) | `"auto_review"` sends escalations to a reviewer agent, which the vendor calls "not a deterministic security guarantee" |
| `sandbox_mode` + `[sandbox_workspace_write]` | `"workspace-write"`, no network, no extra writable roots | Writes stay in the workspace, and commands get no network (REQ-07) | In workspace-write, `.git`, `.codex`, `.agents` and `.aws` stay read-only even inside writable roots |
| `web_search` | `"disabled"` | Fewer untrusted inputs (REQ-07) | The default is `"cached"`, an OpenAI-maintained index. It becomes `"live"` under full access |
| `check_for_update_on_startup` | `false` | Keep the validated version (REQ-06) | Only when updates are rolled out centrally |
| `forced_login_method`, `forced_chatgpt_workspace_id` | `"chatgpt"`, your workspace | Organisation accounts only (REQ-16) | If the credentials do not match, Codex logs the user out and exits |
| `[shell_environment_policy]` | `inherit = "all"`, `ignore_default_excludes = false`, explicit `filters` | Secrets in environment variables do not reach agent commands, while builds keep the variables they need (REQ-09) | The default of `ignore_default_excludes` is `true`: variables named `*KEY*`, `*SECRET*` and `*TOKEN*` are passed on. `inherit = "core"` also strips `JAVA_HOME`, `VIRTUAL_ENV`, `NODE_OPTIONS`, proxy and CA variables, so builds and tests fail. `filters` cannot be combined with the legacy `exclude` / `include_only` arrays in the same layer. Prove the effect with an environment canary in OQ-08 |
| `[history] persistence` | `"save-all"` | Local session history as a record, if your retention decision needs it | `"none"` stops writing `~/.codex/history.jsonl`; `codex exec --ephemeral` skips session files |
| `[analytics] enabled`, `[feedback] enabled` | `false` | Data minimisation (REQ-09) | Analytics controls the built-in exporter, not your own OTLP collector |
| `[otel]` with `[otel.exporter.otlp-http]` | your collector, prompts not logged | Audit trail (REQ-05) | OTel export is off by default. The string form of an exporter accepts only `"none"` or `"statsig"`: an OTLP exporter must be a table, despite a doc example that uses a string. `[otel]` is ignored in project config |
| `[projects."<path>"] trust_level` | `"trusted"` for validated repositories | Untrusted projects skip project config, hooks, rules and `AGENTS.md` | Setting `approval_policy` explicitly overrides the policy derived from trust |

The `model` key and `[models.new_thread]` in requirements are **defaults, not enforcement**. An explicit `--model`, `--config` or `--profile` overrides them.

## Requirements: `requirements.example.toml`

| Key | Example | Why (REQ) | Caveat |
|---|---|---|---|
| `allowed_approval_policies` | `["on-request"]` | Blocks `-a never` (REQ-07) | Add `"untrusted"` only to preserve the policy derived from `trust_level` |
| `allowed_approvals_reviewers` | `["user"]` | Keeps humans on escalations (REQ-02) | |
| `allowed_sandbox_modes` | read-only, workspace-write | Blocks `danger-full-access` (REQ-07) | `"external-sandbox"` is also recognised here. For permission profiles use `allowed_permission_profiles` (a complete allowlist; omitted profiles are denied) |
| `allowed_web_search_modes` | `["cached"]` | Restricts live web access | `"disabled"` is always allowed |
| `allowed_login_methods`, `allowed_chatgpt_workspaces`, `cli_auth_credentials_store` | ChatGPT, your workspace, `"auto"` | Organisation accounts; credentials in the OS store where one exists (REQ-16) | Honoured **only** in the local system file or macOS MDM, and ignored in cloud-managed requirements. If no login method is available, Codex refuses to start. Store values: `file` (plaintext `~/.codex/auth.json`), `keyring`, `auto`, `ephemeral`. An enforced `keyring` breaks login on headless Linux, WSL, devcontainers and disposable admission VMs. Check how `auto` falls back against the vendor's current documentation, or choose the value per platform, and test login on every platform in IQ-02 |
| `[rules] prefix_rules` | prompt on `git push`; forbid `gh pr merge` and `gh pr review` | Defence in depth for REQ-02 and REQ-04 | Decision must be `"prompt"` or `"forbidden"`. Rules are experimental and govern commands that run outside the sandbox. The vendor says they are not a complete OS policy engine. Test them offline with `codex execpolicy check --rules <file> -- <command>` (hidden from `--help`) |
| `[permissions.filesystem] deny_read` | `*.env`, `~/.ssh` | Secrets are not read (REQ-09) | When present, full-access permissions are rejected |
| `[mcp_servers]` | commented out, with an example entry | No MCP server runs unless allowlisted by name **and** identity (REQ-06) | Deployed as an **empty table it disables every MCP server** for everyone, so uncomment it only together with your approved servers. The string form of `identity.command` does not inspect arguments. A structured matcher does |
| `allow_managed_hooks_only` + `[features] hooks = true` | commented out | Enforce managed policy hooks (REQ-06) | Codex does not distribute hook scripts, so deliver them by MDM. See [Known limits](#known-guardrail-limits) on hook failures |
| `enforce_residency` | commented out | Data residency (REQ-09) | Only `"us"` is accepted. Enabling it in a cloud policy disables local computer access |

## Model envelope

- No admin-enforced model allowlist was verified for Codex. Treat the envelope as **recorded and monitored** (envelope policy), and use process controls plus detection for the pinned policy. Check the vendor's current documentation for workspace-level model controls.
- Because a new or changed vendor default can be used before MA-01, the validation plan allows a **time-boxed admission after detection** for such tools: a model first seen in telemetry is admitted with MA-01 within the plan's number of working days. Its use in between is a recorded deviation, pre-classified as minor when MA-01 then passes and every change it touched passed review and CI. Detect new models automatically from telemetry and from the admission runner's reported models.
- The `codex.conversation_starts` telemetry event records the model, reasoning settings and sandbox and approval policy. Metrics also carry the model. PQ-01 matches the observed model ids against the envelope.
- The `codex exec --json` stream may not name the model. In MA-01, pass the files written during the run (OTel export, session files) to the runner with `--model-log` so that the evidence holds the model actually used.
- Vendors retire models. In October 2026 a model was retired from Codex with ChatGPT sign-in on a fixed date, and configurations pinning it had to change (API-key sessions were not affected). Plan Tier 2 or Tier 3 actions before such dates ([docs/model-change-protocol.md](../../docs/model-change-protocol.md)).

## Known guardrail limits

State these in `03` and test them in OQ-08 and OQ-40:

- **Hooks.** Only an explicit deny blocks a `PreToolUse` call: `permissionDecision: "deny"`, the legacy `decision: "block"`, or exit code 2. Unsupported outputs mark the hook as failed and the tool call continues. Timeouts and errors may not block either. Test the failure paths, and do not rely on a hook alone. Non-managed hooks must be trusted by hash in `/hooks`, and `--dangerously-bypass-hook-trust` skips that check.
- **Project config.** Project `.codex/config.toml` cannot set providers, base URLs, `notify`, profiles or `otel`; Codex ignores them with a warning. Untrusted projects load no project layer at all.
- **Environment variables** reach commands unless `ignore_default_excludes = false` is set (see above).
- **Prefix rules** match command prefixes. They are not an OS boundary, and they govern only commands run outside the sandbox. A command inside `workspace-write` is not stopped by a rule, which is why the admission runner records its denied-command check as N/A for Codex unless a verified control is declared (`admission/README.md`).
- **`--dangerously-bypass-approvals-and-sandbox`** is meant only for environments that are sandboxed externally. Include it in OQ-09 and record whether your requirements make Codex fall back to allowed values.
- **Safety monitoring** can pause a task. In the CLI, and under Zero Data Retention, the task ends instead and cannot be resumed.

## Headless use: CI and the admission runner

```bash
CODEX_API_KEY=<api-key> codex exec --json --sandbox workspace-write --model <model-id> "<task>" > run.jsonl
```

- `codex exec` runs read-only by default. `--json` emits JSONL events (`thread.started`, `turn.started`, `turn.completed`, `turn.failed`, `item.*`, `error`). Other useful flags: `--ephemeral`, `--ignore-user-config`, `--output-schema`, `-o/--output-last-message`, `--skip-git-repo-check`.
- Set `CODEX_API_KEY` for the Codex invocation only. Never set it, or `OPENAI_API_KEY`, as a job-level variable in workflows that run repository code.
- `admission/run_admission.py --tool codex` builds the invocation for you, with `--ignore-user-config` so that the executor's own configuration stays out of the run. Run it with `--dry-run` first.
- OQ-08 probes of the sandbox can run without a model: `codex sandbox -- <command>` runs a command under the configured sandbox (for example `codex sandbox -- sh -c 'touch ~/outside.txt'`; there is no platform subcommand in 0.163.0, and `-P/--permission-profile` selects a profile). `codex execpolicy check --pretty --rules <file> -- <command>` evaluates command rules offline.

**`openai/codex-action`.** The repository publishes tags, not releases, and the floating `v1` tag moves. Pin a tag or commit SHA, and set `codex-version` explicitly (an empty value installs the latest CLI). Prefer `permission-profile` (`":read-only"` or `":workspace"`) over the legacy `sandbox` input; the two are mutually exclusive. Keep `safety-strategy: drop-sudo` (the default). It is irreversible on reused self-hosted runners, and `read-only` still runs as a sudo-capable user that could read the key. Keep `allow-bots: false`. By default only users with write access can trigger it. The action outputs `final-message` and does not post reviews or approvals itself.

## GitHub code review and cloud

- **Codex code review** is enabled per repository in the Codex settings and triggered by `@codex review` or automatic reviews. It flags P0 and P1 issues and follows review rules in `AGENTS.md`. The vendor states that these rules "don't replace tests, branch protections, or required approvals". Observed reviews are comment-type, and no official source says Codex submits APPROVE. Prove in OQ-04 that its review does not change the review decision. `@codex fix ...` starts a cloud task that can push to the PR branch when permitted, so make sure stale approvals are dismissed on push.
- **Codex cloud** is off by default for Enterprise workspaces and requires ChatGPT sign-in (with MFA for email and password accounts). Internet access is set per environment. It does not support GitLab or GitHub Enterprise Server. The vendor does not document which GitHub identity opens cloud PRs or authors commits, so determine it empirically in IQ-04 (PR author, `git log --format=fuller`, trailers).

## Data handling (input to IQ-05)

- With ChatGPT sign-in, usage follows the workspace's permissions, retention and residency settings. With an API key, it follows the API organisation's settings. Business, Enterprise and Edu data is not used for training by default. API Zero Data Retention does not define retention for ChatGPT Work.
- Local files: `~/.codex/history.jsonl`, `~/.codex/sessions`, `log_dir` (default `$CODEX_HOME/log`), and `~/.codex/auth.json` unless the keyring is used.
- Compliance API records (`codex_log`, `conversation_message`) are available for 30 days. The vendor states that these sources and local OTel do not form a complete record of every local action. Combine OTel, managed hooks, proxy logs and the Compliance API, and test that each one recorded your verification session.

## Deploy and verify

1. `codex --version` (prints `codex-cli <version>`), `codex --strict-config doctor`, `codex features list`, `codex login status`.
2. In the TUI: `/status` and `/hooks`. Try `codex -a never` and `codex --sandbox danger-full-access` and record the fallback notice (OQ-09).
3. `python3 checks/capture_baseline.py --tool codex --repo <repo> --operator "<name>" --out evidence/<TOOL_ID>/IQ-03/` to hash the configuration and requirements files.
4. Check that `/etc/codex/requirements.toml` is owned by root or Administrators and is not writable by the user.
