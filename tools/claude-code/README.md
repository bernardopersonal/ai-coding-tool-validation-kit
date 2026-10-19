# Claude Code: settings and notes for a validated state

These notes support the per-tool package (`06` configuration baseline, `05` IQ/OQ steps, `03` known guardrail limitations). Every key and flag below was checked against the vendor documentation (code.claude.com/docs) on 2026-10-18, when the newest release was v2.1.302. Claude Code ships releases almost daily, so re-verify against the vendor's current documentation whenever you raise the validated version range.

Files:

- [`managed-settings.example.json`](managed-settings.example.json): a starting baseline for managed settings on developer machines. JSON has no comments, so every key is explained below. Replace the placeholders before you deploy it, and validate the file on a test machine first (see [Deploy and verify](#deploy-and-verify)).
- [`client-regression.example.json`](client-regression.example.json): example probes for `checks/client_regression.py`, the automated client regression (CS-3a) that gates a raise of the validated version. Confirm every expectation once on your validated version before you approve the file with the validation plan.

## Where managed settings come from

Precedence, highest first: managed settings > command-line `--settings` > `.claude/settings.local.json` > `.claude/settings.json` > `~/.claude/settings.json`. Nothing in a user's own files or in `--settings` overrides a managed key. List keys such as permission rules merge across scopes, and a deny anywhere beats an allow anywhere.

| Channel | Location | Notes |
|---|---|---|
| File | macOS `/Library/Application Support/ClaudeCode/managed-settings.json`; Linux and WSL `/etc/claude-code/managed-settings.json`; Windows `C:\Program Files\ClaudeCode\managed-settings.json`; optional drop-ins in `managed-settings.d/*.json`, merged alphabetically | Protect the file (owner root or Administrators, not writable by the developer). On WSL, `/etc/claude-code` is user-writable. The legacy Windows path under `C:\ProgramData` is no longer read |
| MDM | macOS domain `com.anthropic.claudecode`; Windows `HKLM\SOFTWARE\Policies\ClaudeCode`, value `Settings` (JSON) | `HKCU\...` is a user-writable fallback, not an admin source. Templates for Jamf, Intune and Group Policy are in the vendor's repository under `examples/mdm` |
| Server-managed | claude.ai, Organization settings > Claude Code > Managed settings (Team and Enterprise, Owner role) | The vendor calls this "a client-side control, not a security boundary". It is skipped with Bedrock, Vertex (now "Google Cloud's Agent Platform"), Foundry or a custom `ANTHROPIC_BASE_URL`. It is not delivered to sessions that use a Console API key, which is typical in CI. It has no per-group policies |

Managed sources rank: server-managed (remote) > MDM > managed files > `HKCU`. Within the file channel, `managed-settings.json` is read first and the drop-ins in `managed-settings.d/` follow in alphabetical order: scalar keys are replaced by later files, lists are combined, nested objects are merged, and `fallbackModel` and `modelPicker` are replaced whole. By default (`managedSourcesBehavior: "first-wins"`) only the highest-ranked managed source that delivers settings is used, and the others are ignored silently. `/status` shows them under "Skipped sources". `"merge"` (v2.1.242+) combines admin sources, with the strictest value for locks, while `availableModels` and `allowedMcpServers` come whole from the highest-ranked source. `checks/capture_baseline.py` reports the managed sources it finds in this order and evaluates the source that takes effect; confirm the effective policy with `/status` or `managed_settings_resolved`.

**Per-surface delivery (IQ-04).** Device files and MDM never reach Anthropic-hosted cloud sessions. Those read the repository's `.claude/settings.json` and server-managed settings only. A CI job that authenticates with a Console API key gets no server-managed settings. Each surface therefore needs its own delivery path and its own evidence: for example a managed file baked into the runner image, or the GitHub Action's `settings` input.

## The example, key by key

| Key | Example value | Why (REQ) | Tested by | Caveat |
|---|---|---|---|---|
| `permissions.defaultMode` | `"default"` (shown as "Manual") | Start every session in a mode where a person approves actions (REQ-07) | OQ-08 | Auto mode, in which a classifier approves actions, is now the built-in starting mode for interactive sessions. Set the mode explicitly |
| `permissions.disableBypassPermissionsMode` | `"disable"` | Blocks `--dangerously-skip-permissions` and bypass mode, including a subagent's bypass frontmatter (REQ-06, REQ-07) | OQ-09 | The value is the string `"disable"`, not a boolean |
| `permissions.disableAutoMode` | `"disable"` | Removes auto mode; `--permission-mode auto` then starts in default mode | OQ-09 | Only `"disable"` is accepted. Accepted at the top level or under `permissions` |
| `permissions.deny` | `.env`, `.env.*`, `secrets/**` | Agent does not read secrets (REQ-09) | OQ-08, MA-01 | See [Known limits](#known-guardrail-limits): rules match tool calls, not every subprocess. Path anchoring (`./`, `/`, `//`, `~/`) has subtle rules: `./` is relative to the directory Claude Code starts in, so a session started in a subdirectory is not covered. Test each rule, including the subdirectory case, in OQ-08. A `Read` deny also blocks `Edit` on that path |
| `permissions.ask` | `Bash(git push *)`, edits of CI workflows, `CODEOWNERS` and `.claude/settings.json` | A person confirms pushes and edits of gate files. The binding controls are CODEOWNERS and branch protection on the code host (REQ-03, REQ-04, REQ-06) | OQ-08 | `Bash(git push *)` does not match `git -C . push`. The managed file applies to every repository, so it asks rather than denies. In QMS repositories you can add a deny for the same paths to the project's `.claude/settings.json` |
| `pluginConfigs."cc-plugin-sec-default@builtin".options.allowManagedModsOnly`, `disableSideloadFlags` | `true`, `true` | Only mods deployed through managed settings run, and mods cannot be side-loaded from the command line (REQ-06) | OQ-09 | Narrower than `allowManagedHooksOnly`: developers keep their own settings hooks (formatters, linters), status lines and `/goal`. Lock these keys from managed settings only. A mod's own file and process calls ignore `Read` deny rules |
| `sandbox.enabled`, `failIfUnavailable`, `allowUnsandboxedCommands: false` | on, fail closed, no escape hatch | OS-level isolation of shell commands, which deny rules cannot provide (REQ-07) | OQ-08 | The sandbox is off by default. Without `failIfUnavailable` it silently falls back to unsandboxed. It is not available on native Windows, so with `failIfUnavailable` Claude Code does not start there |
| `sandbox.network.allowManagedDomainsOnly`, `allowedDomains` | GitHub hosts (`github.com`, `api.github.com`, `codeload.github.com`, `objects.githubusercontent.com`, `raw.githubusercontent.com`), PyPI and npm | Only approved egress, and developers cannot widen the list (REQ-07, REQ-09) | OQ-08 | Add your own registries (container, Maven, internal mirrors) before deployment, or installs inside the sandbox fail. Publish a way to request additions (for example a change request against the baseline). The example lists exact hosts because wildcard support in `allowedDomains` was not verified: check it against the vendor's current documentation |
| `sandbox.credentials.files` | deny `~/.aws/credentials` | Sandboxed commands can read `~/.ssh` and `~/.aws/credentials` by default (REQ-09) | OQ-08 | `envVars` entries can also unset secret variables. Denying `~/.ssh` breaks git over SSH inside the sandbox |
| `availableModels`, `availableModelsMatch`, `enforceAvailableModels` | the admitted exact model ids, `"exact"`, `true` | Only admitted models can be selected, so a new vendor model or a moved alias is not used before its admission record exists (REQ-08) | OQ-10, MA-01 | See [Model envelope](#model-envelope). `availableModelsMatch` is managed-only and needs v2.1.283+. Add an id after its MA-01 passes. An invalid list is enforced as an empty allowlist |
| `forceLoginMethod`, `forceLoginOrgUUID` | `"claudeai"`, your org UUID | Organisation-owned accounts only (REQ-16) | IQ-02 | API-key credentials are blocked at startup under these keys, so CI runners need their own managed file. Check against the vendor's current documentation which login settings fit your CI credentials. `claude setup-token` and `/install-github-app` do not enforce the org UUID |
| `allowedProviders` | `["anthropic"]` | Prevents routing through another provider, which also skips server-managed settings (REQ-09, REQ-16) | IQ-02 | Needs v2.1.285+. Values: `anthropic`, `bedrock`, `vertex`, `foundry`, `anthropicAws`, `mantle`, `customEndpoint`, `gateway` |
| `requiredMinimumVersion`, `requiredMaximumVersion` | both the validated version (`2.1.302` in the example) | Claude Code exits at startup on any version that was not validated (REQ-06, REQ-12) | IQ-01 | Managed only, and checked at startup only. Invalid values are dropped (fail open), so confirm with `claude doctor` and `claude --version`. Set both to versions you actually tested: a range is validated only where every version in it passed IQ/OQ or CS-3a. Raise the pin on a batched cadence after CS-3a passes on the candidate (`08`, T7a). Package-manager installs (for example Homebrew) upgrade outside Claude Code's updater: pin the package version there too, or the client refuses to start after an upgrade |
| `autoUpdatesChannel` | `"stable"` | Roughly one-week-old builds that skip releases with major regressions | IQ-01 | Homebrew ignores this key. `DISABLE_UPDATES=1` in `env` blocks all updates if you prefer manual rollout |
| `attribution` | static `AI-Assisted` and `AI-Tool` commit lines and PR text | Provenance label that instruction files cannot remove, with no typing by the developer (REQ-10) | OQ-11 | A static text cannot name the model. The model id comes from telemetry and is recorded once per PR in the PR template; a per-commit `AI-Model` trailer is optional. Alternative: leave `attribution` unset to keep the default trailer, `Co-Authored-By: <model name> <noreply@anthropic.com>`, which names the model but can be changed by a user's `CLAUDE.md` |
| `env.CLAUDE_CODE_ENABLE_TELEMETRY`, `OTEL_*` | OTLP to your collector | Audit trail: `tool_decision`, `permission_mode_changed`, `hook_execution_complete`, `managed_settings_resolved` (REQ-05, REQ-06) | IQ-03, PQ-01 | Prompt and response content is redacted by default. Exporter variables in repository settings are ignored |
| `env.OTEL_LOG_MANAGED_SETTINGS` | `"1"` | `managed_settings_resolved` then carries a redacted policy and `managed_settings.resolved_sha256`. Identical digests mean identical policy on every machine | IQ-03 | Needs v2.1.274+ |
| `env.DISABLE_FEEDBACK_COMMAND` | `"1"` | Transcripts sent with `/feedback` are kept for 5 years (REQ-09) | IQ-05 | |

## Options deliberately left out of the example

Add these where your risk assessment calls for them:

- `allowManagedHooksOnly: true` for CI and agent runners. Only managed hooks, Agent SDK in-process hooks and hooks of plugins force-enabled by managed `enabledPlugins` run; user, project, local and agent-frontmatter hooks are blocked, status lines narrow to managed settings, and `/goal` cannot run. That is too much friction on developer machines, where `allowManagedModsOnly` with `disableSideloadFlags` is used instead.
- `allowManagedPermissionRulesOnly: true` makes managed settings the only source of permission rules. It suits `agents_qms` and CI runners, but means real friction for interactive developers.
- `allowManagedMcpServersOnly: true`, with a managed `managed-mcp.json`, locks MCP servers. `allowManagedPermissionRulesOnly` does not lock MCP. Check the allowlist format against the vendor's current documentation.
- `permissions.blockReadsOutsideWorkingDirectories: true` (v2.1.257+).
- `deniedModels` (managed only, v2.1.283+) to block specific ids explicitly.
- `switchModelsOnFlag: false` makes Claude Code ask instead of switching automatically after a safety-classifier flag. `fallbackModel` is an ordered overload fallback chain of up to 3 models.
- Policy hooks. A `PreToolUse` hook that exits 2 blocks the call. Without `"onFailure": "block"` (v2.1.295+, for command and http hooks), a hook that crashes, is missing or times out lets the action through. Shape: `{ "hooks": { "PreToolUse": [ { "matcher": "Bash", "hooks": [ { "type": "command", "command": "<your policy script>", "timeout": 30, "onFailure": "block" } ] } ] } }`. Deploy the script with the settings, because a missing script with `onFailure: "block"` blocks every matching call.
- `cleanupPeriodDays`. Local transcripts (`~/.claude/projects/<project>/<session>.jsonl`) are plaintext and deleted after 30 days by default. Set the value from your record-retention decision.
- `OTEL_LOG_TOOL_DETAILS=1` logs Bash commands and tool input, which helps evidence but may capture secrets. Add `OTEL_RESOURCE_ATTRIBUTES` (for example `enduser.id=...`) for API-key fleets, because `user.id` is an anonymous id.
- `forceRemoteSettingsRefresh: true` blocks startup until server-managed settings are freshly fetched. The default falls back to the cached policy.
- `disableRemoteControl: true` (per device). Remote Control and cloud sessions are also switched organisation-wide in the admin console.

## Model envelope

- The kit's envelope patterns (for example `vendor-family-*` in `approved_models`) are kit notation and define which models may be **proposed** for admission. They are not deployed as such. The deployed allow-list holds the **admitted exact ids**: add an id to managed `availableModels` after its MA-01 record passes (Tiers 1 and 2 in section 5 of `04`), and remove it when the admission is withdrawn. This is what makes the rule "a model is used only after its admission record exists" enforceable.
- With the default prefix matching, an `availableModels` entry that is a model id also permits **later versions** of that id, and aliases move to new models on release day. `availableModelsMatch: "exact"` (managed only, v2.1.283+) stops both: Default is then limited to the listed models. Whether wildcard characters are accepted was not verified: check against the vendor's current documentation.
- `availableModels` restricts `/model`, `--model` and the `model` key. A managed `model` key alone is only a starting default: `--model` and `ANTHROPIC_MODEL` still choose the session model.
- `enforceAvailableModels: true` (v2.1.175+) keeps the Default option inside the list. When any managed settings exist, it is read from the managed source only. Model pickers on claude.ai and Desktop are a convenience and do not enforce the allowlist.
- A newly released model can need a newer client than the validated version. Then the model admission (T1) and the version raise (T7a, CS-3a) run together.
- Automatic fallback can change the model mid-session: an overload chain (`fallbackModel`), and a re-run on another model when safety classifiers flag a request. The fallback target is checked against `availableModels`, and no fallback happens when it is blocked.
- A `PreModelSwitch` hook (v2.1.251+) can log or deny user-requested switches. It does not run for automatic fallbacks, which reach `PostModelSwitch` only.
- Recording the model used (REQ-08): telemetry, the PR template (once per PR), and the default commit trailer if you keep it. Verify which telemetry field carries the model id for your version. The admission runner records the models reported in `modelUsage` and flags any model other than the requested one, unless it is listed with `--aux-model` (for example a model the client uses for background work).

## Known guardrail limits

State these in `03` (section "Known guardrail limitations") and test them in OQ-08 and OQ-40:

- **Bash rules match command text**, after splitting compound commands and stripping simple wrappers. A deny on `Bash(curl *)` does not stop `/usr/bin/curl` or `sh -c 'curl ...'`. Only the OS sandbox enforces at OS level.
- **Read and Edit denies apply to Claude's file tools**, not to subprocesses (for example a Python script) that open files themselves. `.claudeignore` has no effect.
- **The sandbox covers shell commands and their children only.** The built-in Read, Edit and WebFetch tools, hooks, MCP servers and LSP servers run outside it.
- **Hooks fail open** unless `onFailure: "block"` is set. Only exit code 2 blocks; exit 1 does not.
- **Headless runs (`claude -p`) show no workspace trust prompt.** Without `--bare` they run the project's hooks and connect its `.mcp.json` servers, even in an untrusted folder. Use `allowManagedHooksOnly` on runners, `--setting-sources user` or `--bare`. What `--bare` still loads and how it authenticates were flagged for correction in the kit's research, so verify them against the vendor's current documentation.
- **The headless default mode is inconsistent across sources.** The v2.1.302 changelog and the permission-modes page disagree on the starting mode of `claude -p`. Always pass `--permission-mode` in CI and in the admission runner.
- **Mods** (plugins that run code with the user's permissions, on by default from v2.1.286) can approve calls that an ask rule would prompt for. Deny rules hold over mods only where the built-in guard loads: on machines with managed settings, or with a Team or Enterprise login. `allowManagedModsOnly` limits mods to managed ones, but even under the guard a mod's own file and process calls ignore `Read` deny rules.
- **CLAUDE.md is guidance, not enforcement.** Permission rules are enforced by Claude Code, not by the model.

## Headless use: CI and the admission runner

```bash
claude -p "<task>" --model <model-id> --permission-mode dontAsk --allowedTools "Read" "Bash(npm test)" --max-turns 10 --output-format json
```

- `dontAsk` auto-denies anything that would prompt, which suits locked-down CI. Never use `bypassPermissions` outside an isolated container or VM. Deny rules still apply in every mode.
- Useful flags: `--max-turns`, `--max-budget-usd`, `--no-session-persistence`, `--output-format json` (includes cost), `--setting-sources user`.
- `admission/run_admission.py --tool claude_code` builds the invocation for you. Run it with `--dry-run` first to see the exact command. By default it passes `--setting-sources project`, so the operator's user settings do not enter the run while managed settings still apply (`--no-isolation` turns this off and is recorded). For the denied-command task it adds a deny rule for the probe command and a broad allow for the interpreter, so the deny rule is the only barrier and a pass says something about the model.

## GitHub integrations

- **`anthropics/claude-code-action`.** `v1` is a moving major tag, so pin a commit SHA. Its docs state that Claude cannot approve PRs, submit formal reviews, merge or rebase. That is the app's behaviour, not a platform permission boundary: keep the repository and organisation setting "Allow GitHub Actions to create and approve pull requests" (`can_approve_pull_request_reviews`) off, and prove it in OQ-04. On PRs the action restores `.claude/`, `.mcp.json`, `CLAUDE.md` and similar files from the base branch, while the rest of the tree stays at the PR head. Runs need a triggering user with write access, `allowed_non_write_users` is flagged as risky, and commits are unsigned unless `use_commit_signing` or `ssh_signing_key` is set.
- **Claude Code Review** (managed service, Team and Enterprise). "A review never approves or blocks the pull request." Its check run concludes neutral or skipped, never failure, so it cannot be a required gate (REQ-15). It reads `REVIEW.md` from the base branch. An `@claude review` comment also triggers the Action if the Action uses the default trigger phrase. It is not available with ZDR, HIPAA or CMEK.

## Data handling (input to IQ-05)

- Commercial plans (Team, Enterprise, API, third-party platforms) are not used for training unless you opt in. Standard server retention is 30 days. Zero Data Retention is Enterprise-only and enabled per organisation, and it disables cloud sessions and Remote Control.
- Local transcripts and `~/.claude/history.jsonl` are not encrypted at rest. If you keep them as records, export them to a controlled store.
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` turns off non-essential traffic. Before you rely on it, check its interaction with your telemetry export against the vendor's current documentation.
- Certificates (SOC 2 Type 2, ISO 27001) are on the vendor's Trust Center. Record their scope and expiry.

## Deploy and verify

1. `python3 -m json.tool managed-settings.example.json` to check the syntax. Claude Code refuses to start when a managed file is not a valid JSON object. Single invalid entries are skipped with a warning.
2. Deploy to a test machine, then run `claude --version`, `claude doctor` (lists rejected entries, auto-update state and organisation policy) and `/status` ("Setting sources: ... Enterprise managed settings (file)" and "Skipped sources").
3. Capture `claude_code.managed_settings_resolved` and its `resolved_sha256`, and run `python3 checks/capture_baseline.py --tool claude_code --repo <repo> --operator "<name>" --out evidence/<TOOL_ID>/IQ-03/`.
4. Installation integrity (IQ-01): each release publishes a `manifest.json` with SHA-256 checksums, signed with the vendor's GPG key (`https://downloads.claude.ai/keys/claude-code.asc`, fingerprint `31DD DE24 DDFA B679 F42D 7BD2 BAA9 29FF 1A7E CACE`). Verify with `gpg --verify manifest.json.sig manifest.json` and compare the binary's hash.
5. Run OQ-08 and OQ-09 (`05`) against the deployed file before release.
