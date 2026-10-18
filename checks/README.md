# checks/ - evidence scripts

Scripts that produce objective evidence for the validation package: API exports,
hashes and timestamps instead of screenshots. Python 3.9+ standard library only;
`run_canary.sh` needs bash, the GitHub CLI (`gh`) and python3.

| Script | Produces evidence for | Requirements |
|---|---|---|
| `check_github_gates.py` | OQ-01 (human gate, historical sample, required checks passed), OQ-04 (bot / Actions approvals), OQ-05 (agent-authored PRs, launcher), OQ-06 (bypass), PQ-01 (in-use monitoring), RV-01 (retrospective review) | REQ-01, REQ-02, REQ-03, REQ-04, REQ-05 |
| `capture_baseline.py` | IQ-01 (version), IQ-03 (configuration baseline, hashed; drift with `--compare`); input for document 06 | REQ-06, REQ-08 |
| `find_ai_footprint.py` | Tool discovery checklist, periodic review reconciliation | REQ-05, REQ-06, REQ-12 |
| `canary/run_canary.sh` | OQ-02 (merge without approval), optional OQ-03, OQ-05, OQ-06, OQ-07 | REQ-01, REQ-03, REQ-04 |
| `mirror_protection.py` | Sandbox repository with the production protection, for the canary (OQ-02 to OQ-07) | REQ-01, REQ-03, REQ-04 |
| `soup_gate.py` | Required CI check against unapproved or non-existent dependencies (OQ-07 b) | REQ-03 |
| `client_regression.py` | Automated client regression on a candidate tool version (CS-3a in document 08) | REQ-06, REQ-07, REQ-12 |
| `../examples/github-workflow-evidence-export.yml` | Continuous export of the review record and check results of every merged PR (OQ-01, PQ-01) | REQ-01, REQ-02, REQ-05 |
| `../examples/github-workflow-soup-gate.yml` | Runs `soup_gate.py` as a required check | REQ-03 |

The model admission suite (MA-01) lives in `../admission/`.

## Common behaviour

- `--help` on every script; `--out DIR` (default `evidence/`).
- `--operator "<name>"` (or `$KIT_OPERATOR`) is required for every run that
  produces evidence. The evidence records who ran the script: the operator, the
  operating-system user, the host name, the SHA-256 of the machine id, and, for
  the GitHub scripts, the authenticated login (`GET /user`). Exploratory runs
  belong in `evidence/<TOOL_ID>/_exploratory/`, not in a test folder.
- Each run writes `<name>_<target>_<UTC timestamp>.json`, the same name with
  `.md`, and `<name>.json.sha256` (`sha256sum -c` compatible). The Markdown
  repeats the SHA-256 of the JSON, the UTC timestamp, the script name and version.
- Findings carry a severity (`fail`, `inconclusive`, `warn`, `info`), the
  requirement and the test they relate to.
- Exit codes: `0` pass (warnings allowed), `1` a check failed (or was
  inconclusive), `2` usage, authentication or network error. In the Python
  scripts, `--fail-on-warn` turns warnings into exit `1`.
- Secrets are never written to the evidence: `capture_baseline.py` redacts
  token-like values, header and key values and environment values that are not
  known non-secret toggles; the canary and admission runs replace their canary
  value before saving output.
- The scripts write evidence; they do not decide. Conclusions and approvals are
  recorded by the responsible people in the QMS (executor and approver are
  different people, and neither is the AI tool).

Name the output folder after the test and attach the `.json`, `.json.sha256`
and `.md` to the test record: `evidence/GEN/<TEST-ID>/` for the code-host gate
tests that are qualified once for all tools (OQ-01 to OQ-07, OQ-12), and
`evidence/<TOOL_ID>/<TEST-ID>/` for tool tests, e.g. `--out evidence/CLAUDE/IQ-03/`.

## check_github_gates.py

```
python3 checks/check_github_gates.py --repo OWNER/REPO --branch main --prs 20 --operator "<name>" --out evidence/GEN/OQ-01/
python3 checks/check_github_gates.py --repo OWNER/REPO --pr 123 --pr 124 --operator "<name>" --out ...   # specific PRs
python3 checks/check_github_gates.py --repo OWNER/REPO --pr 123 --launcher 123=<login> --operator "<name>" --out evidence/GEN/OQ-05/
python3 checks/check_github_gates.py --repo OWNER/REPO --prs 0 --operator "<name>" --out ...             # configuration only
```

Reads, for the branch: classic branch protection
(`GET /repos/{o}/{r}/branches/{b}/protection`), the effective ruleset rules
(`GET /repos/{o}/{r}/rules/branches/{b}`) and the details and bypass lists of the
rulesets behind them, ruleset bypass events of the last month
(`GET /repos/{o}/{r}/rulesets/rule-suites`), the Actions setting
`can_approve_pull_request_reviews` for the repository and, when readable, the
organisation (`GET .../actions/permissions/workflow`), the secret scanning push
protection status, and the last N merged PRs with their reviews.

A merged PR passes when it has at least one (or the configured number of)
**qualifying approval**: state `APPROVED`, by a user of type `User` (not a
`[bot]` login and not listed with `--non-human`), not the PR author, submitted
before the merge, still the reviewer's latest decision at merge time, and on the
head commit when last-push approval is required (`--require-head-approval auto`,
the default), and, unless `--no-checks`, every required check passed on the
merged head commit (check runs and commit statuses). Approvals by bots or apps,
PRs merged by non-human identities and approvals given only on an earlier
commit are flagged as warnings. Check results that are no longer readable
(expired under the retention setting) are `inconclusive`, not a pass.

Agent-authored PRs (OQ-05): the approval of the person who launched the agent
does not count. Give the launcher with `--launcher PR=LOGIN` (for example from a
cloud task record); otherwise the script scans PR and issue comments for the
trigger mentions (`--trigger`, default `@claude`, `@codex`, `@copilot`) and
treats the commenter as the launcher. When the launcher is unknown, an
agent-authored PR needs `--agent-pr-min-approvals` qualifying approvals
(default 2, the compensating control in the work instruction), and fewer is
flagged.

Configuration findings include: no required approving review (fail); GitHub
Actions allowed to approve PRs (fail); a ruleset bypass actor in `exempt` mode,
which runs no rules and creates no bypass audit entry (fail); no required status
check or required workflow (fail); administrators not included in classic
protection, bypass lists, app / integration bypass actors, recent bypass events,
force pushes allowed, required checks not pinned to an app (any writer can set a
status), final-commit approval not enforced (warnings).

Authentication: `GITHUB_TOKEN` or `GH_TOKEN` (sent with urllib), otherwise the
login of the GitHub CLI through `gh api`. Active rulesets are readable with read
access. Classic protection, the Actions workflow permissions and the organisation
setting may need repository or organisation admin rights; verify the required
token scopes or fine-grained permissions against GitHub's current documentation.
Items that cannot be read are reported as `inconclusive`
(repository settings) or `info` (organisation settings, rule insights). For
GitHub Enterprise Server pass `--api-url https://HOST/api/v3`. Requests pin
`X-GitHub-Api-Version: 2022-11-28`; the version is recorded in the evidence.

Limitations to record in the test report:

- The API does not show who launched an agent. The comment scan finds only
  launches by mention. For agent tasks started elsewhere (IDE, cloud console),
  pass `--launcher` from the task record or rely on the compensating control
  (OQ-05).
- Whether approvals by apps or machine users count toward required reviews is
  not documented consistently; demonstrate it with a negative test (OQ-04) and
  list machine users used by agents with `--non-human`.
- Copilot code review can be configured to approve PRs, and such approvals can
  count toward merge requirements when enabled at repository, organisation and
  enterprise level. The script flags them as non-human approvals; record the
  Copilot approval settings in the baseline.
- Rule insights cover at most the last month, and the organisation audit log
  shows 180 days (Git events 7 days). Export regularly or stream the audit log.
- Check runs, statuses and logs follow the repository retention setting
  (`GET /repos/{o}/{r}/actions/permissions/artifact-and-log-retention`, in days;
  default 90, at most 400 for private repositories; from 2026-10-01 it also
  covers checks and statuses). The script records the setting and flags a
  sample older than it. Export the check evidence of every merged PR with
  `../examples/github-workflow-evidence-export.yml` and archive it in the QMS
  within the retention period.
- GitLab and other code hosts are not covered: use the manual alternative in
  the test protocol.

## capture_baseline.py

```
python3 checks/capture_baseline.py --tool claude_code --repo PATH --operator "<name>" --out evidence/<TOOL_ID>/IQ-03/
python3 checks/capture_baseline.py --tool codex --repo PATH --operator "<name>" --out evidence/<TOOL_ID>/IQ-03/
python3 checks/capture_baseline.py --tool claude_code --repo PATH --compare evidence/<TOOL_ID>/IQ-03/<approved>.json --approved-version <version> --operator "<name>" --out ...
python3 checks/capture_baseline.py --tool other --name "Tool X" --version-cmd "toolx --version" --config ~/.toolx/config.json --repo PATH --operator "<name>" --out ...
```

Run it on each machine image or runner in scope (developer laptop, CI runner),
as the user who runs the tool. It records the CLI version (`claude --version`,
`codex --version` or `--version-cmd`), and hashes and parses the configuration
files at these locations:

| Tool | Scope | Locations |
|---|---|---|
| Claude Code | managed | Linux / WSL `/etc/claude-code/`, macOS `/Library/Application Support/ClaudeCode/`, Windows `C:\Program Files\ClaudeCode\`: `managed-settings.json`, `managed-settings.d/*.json`, `managed-mcp.json`, `CLAUDE.md`; on Windows also the registry value `Settings` under `HKLM\SOFTWARE\Policies\ClaudeCode` (and the user-writable `HKCU` fallback) |
| Claude Code | server-managed cache | `~/.claude/remote-settings.json` |
| Claude Code | user | `~/.claude/settings.json`, `~/.claude/CLAUDE.md` |
| Claude Code | project / local | `<repo>/.claude/settings.json`, `<repo>/.claude/settings.local.json`, `<repo>/.mcp.json`, every file under `<repo>/.claude/`; instruction files `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`, `REVIEW.md` |
| Codex | admin-enforced | `/etc/codex/requirements.toml` (Windows `%ProgramData%\OpenAI\Codex\requirements.toml`) |
| Codex | managed defaults | `/etc/codex/managed_config.toml` (Windows `~/.codex/managed_config.toml`) |
| Codex | system | `/etc/codex/config.toml` (Windows `%ProgramData%\OpenAI\Codex\config.toml`) |
| Codex | user / profiles | `$CODEX_HOME` (default `~/.codex`): `config.toml`, `<name>.config.toml`, `hooks.json`, `rules/*.rules`, `AGENTS.md`, `AGENTS.override.md`; `auth.json` presence only (never read) |
| Codex | project | `<repo>/.codex/config.toml`, `<repo>/.codex/hooks.json`, `<repo>/.codex/rules/*.rules`; `AGENTS.md`, `AGENTS.override.md` and any `project_doc_fallback_filenames` |
| Other | declared | files given with `--config`; repository instruction files of common tools (Copilot, Cursor, Gemini, Aider) |

Selected keys are extracted with secrets redacted, for example: Claude Code
`permissions.*` (default mode, allow / ask / deny, `disableBypassPermissionsMode`),
`disableAutoMode`, `allowManagedPermissionRulesOnly`, `allowManagedHooksOnly`,
`allowManagedMcpServersOnly`, `pluginConfigs`, `disableSideloadFlags`,
`managedSourcesBehavior`, `sandbox`, `hooks`, `availableModels`,
`availableModelsMatch`, `enforceAvailableModels`, `deniedModels`, `model`,
`fallbackModel`, version pins, login and provider restrictions, `attribution`,
`cleanupPeriodDays`, MCP servers; Codex `approval_policy`, `approvals_reviewer`,
`sandbox_mode`, `sandbox_workspace_write`, `default_permissions`, `permissions`,
`shell_environment_policy`, `web_search`, `model`, `model_provider`,
`model_reasoning_effort`, `mcp_servers`, `hooks`, `otel`, project trust levels and
the `allowed_*` lists of `requirements.toml`.

Claude Code managed sources are evaluated in the client's own order:
server-managed (from the local cache) > MDM (Windows registry) > managed file
and drop-ins (`managed-settings.json`, then `managed-settings.d/*.json`
alphabetically) > `HKCU`. With `managedSourcesBehavior: "first-wins"` (the
default) only the highest-ranked source counts; with `"merge"` the admin
sources are combined. Each finding names the source that sets the key, and the
Markdown shows the effective policy. Confirm it with `/status`.

Findings: unparseable configuration files and a configured
`bypassPermissions` default mode fail; missing managed settings, a managed
policy without `disableBypassPermissionsMode = "disable"`, without
`disableAutoMode` or without `availableModels`, `availableModels` without
`availableModelsMatch: "exact"`, a missing `requirements.toml`,
`danger-full-access` or an `approval_policy` of `never` are warnings.

With `--compare` (drift against the approved baseline, REQ-06), an added,
removed or changed file in the managed, MDM, requirements, managed-defaults,
system, project or declared scope fails. Changes in user-scope files and caches
are warnings, and server-managed settings are compared by their selected values,
not bytes. A changed CLI version is `info` when it is one of the
`--approved-version` values and a failure otherwise. Only tools present in both
captures are compared.

Not read by the script (listed as manual fields in the Markdown): macOS MDM
profiles (`com.anthropic.claudecode`, `com.openai.codex`), the server-managed /
cloud-managed policy consoles, and the `/status`, `claude doctor`,
`codex --strict-config doctor` and `codex features list` output. Attach those
separately. On Python 3.9 / 3.10 TOML is parsed by a small built-in parser for
the subset used in configuration files; the parser used is recorded per file.

## find_ai_footprint.py

```
python3 checks/find_ai_footprint.py --path REPO_DIR --out evidence/discovery/
python3 checks/find_ai_footprint.py --path REPO_DIR --known-tools claude_code,codex --org ORG --out ...
```

Lists agent configuration and instruction files (`.claude/`, `CLAUDE.md`,
`.mcp.json`, `AGENTS.md`, `.codex/`, `.agents/`, `.cursor/`,
`.github/copilot-instructions.md`, `.github/instructions/`, `.github/hooks/`,
`GEMINI.md`, `.gemini/`, `.aider.conf.yml`, ...), CI workflows that use AI actions
or agent CLIs, AI SDK dependencies in package manifests, and AI attribution in
the last `--git-log` commit messages (counts and commit SHAs only, no names or
e-mails). Instruction files not covered by CODEOWNERS are flagged: some review
bots read instructions from the PR head branch, so a PR can change its own
review instructions unless those files need code-owner review.

Workflow risks: `--dangerously-skip-permissions`, Codex approval and sandbox
bypass flags, `bypassPermissions`, `allowed_non_write_users` and
`safety-strategy: unsafe` fail; AI workflows on `pull_request_target` or
`workflow_run`, bots allowed to trigger, `write-all` permissions, action refs that
are not a commit SHA, and `openai/codex-action` without `codex-version` are
warnings. With `--known-tools`, any detected tool outside the validated
inventory fails (tool discovery reconciliation). With `--org`, the organisation's
GitHub App installations are listed (`GET /orgs/{org}/installations`, needs an
organisation owner token) and AI-related apps are flagged. The apps installed by
GitHub's "Allow Claude / Codex coding agent" policies are not listed among
installations; review the audit log for them.

The scan is heuristic text matching. Review every hit and record the
reconciliation in the tool-discovery checklist.

## canary/run_canary.sh

See [`canary/README.md`](canary/README.md).

## mirror_protection.py

```
python3 checks/mirror_protection.py --from OWNER/PROD --operator "<name>" --out evidence/GEN/OQ-02/        # export only
python3 checks/mirror_protection.py --from OWNER/PROD --to OWNER/SANDBOX --operator "<name>" --out ...    # plan
python3 checks/mirror_protection.py --from OWNER/PROD --to OWNER/SANDBOX --apply --operator "<name>" --out ...
```

Exports classic branch protection, repository rulesets and the Actions approval
setting of the production repository, and copies them to a sandbox repository
(plan only unless `--apply`), then compares the two. Bypass actors, dismissal
and push allowances are copied only with `--copy-actors`, because their ids
differ between repositories. Run the canary against the sandbox when you may
not open test PRs in production, and attach the comparison to the test record:
the canary result is valid for production only where the comparison matches.
Writing protection needs admin rights on the sandbox.

## soup_gate.py

```
python3 checks/soup_gate.py --approved approved-components.json --base origin/main --operator "$GITHUB_ACTOR" --out evidence/soup-gate/
```

Compares the direct dependencies in `requirements*.txt` and `package.json`
between the base and head revisions and fails when a new or changed dependency
is not on the approved component (SOUP) list, or, with `--check-registry`, does
not exist in PyPI or npm (an invented package name). Versions in the list may
use glob patterns. Example list:
`../examples/github/approved-components.example.json`; example workflow:
`../examples/github-workflow-soup-gate.yml`. Make the job a required check on
the protected branch and demonstrate it in OQ-07 b with the canary. Other
ecosystems need their own parser; the gate fails closed only for the files it
knows.

## client_regression.py

```
python3 checks/client_regression.py --probes tools/claude-code/client-regression.example.json --candidate-version 2.1.303 --var repo=PATH --var baseline=evidence/CLAUDE/IQ-03/<approved>.json --dry-run
python3 checks/client_regression.py --probes <approved probe file> --candidate-version <version> --var ... --operator "<name>" --out evidence/<TOOL_ID>/CS-3a/
```

Runs a fixed list of probes (command, expected exit code, output patterns,
files that must or must not exist) on a candidate client version and records
each outcome. The probe file is approved with the validation plan; the example
files in `../tools/` are a starting point and every expectation in them must be
confirmed once on the validated version. `--skip-credentials` skips probes that
need a vendor login and records them as skipped. A pass is the gate for the
batched version raise (T7a in document 08); a skipped probe must be covered by
the manual CS-3.

## Tests

`python3 -m unittest discover -s tests` runs the unit tests of these scripts with
mocked HTTP and mocked subprocess calls; no network access and no agent calls.
