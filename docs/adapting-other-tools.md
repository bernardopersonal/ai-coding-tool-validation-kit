# Adapting the kit to other AI coding tools

Most of the validation does not depend on the tool. The human approval gate, required checks, the canary tests and the review record of merged PRs all live on the code host (OQ-01 to OQ-07, PQ-01), and `checks/check_github_gates.py` covers them for any tool on GitHub. What changes from tool to tool:

| Area | Tests | Question |
|---|---|---|
| Installation and accounts | IQ-01, IQ-02 | How is the version identified and pinned? Can personal accounts be excluded? |
| Configuration | IQ-03, OQ-09 | Where does admin-enforced configuration live? Can users override it? Does it reach every surface? |
| Identities | IQ-04 | Which identity writes commits, opens PRs and posts reviews? Can it approve? |
| Data terms | IQ-05 | Retention, training use, residency, local transcripts |
| Local guardrails | OQ-08, OQ-40 | Permission modes, sandbox, network, hooks, and what they do **not** cover |
| Models | OQ-10, MA-01 | Which models are selectable? Can the admin restrict them? How is the model used recorded? |
| Attribution | OQ-11 | Built-in trailer or label, or the PR template only? |

In the wizard, choose the tool type `copilot`, `cursor` or `other`. The templates then add tool-specific blocks or `[fill in]` prompts.

## GitHub Copilot

**Surfaces.** IDE chat and agent modes and the Copilot CLI (`local_cli_ide`); Copilot code review (`pr_review_bot`); Copilot cloud agent, formerly "Copilot coding agent" (`cloud_agent`). The third-party Claude and Codex agents hosted on GitHub (public preview) are further cloud agents. Each one enabled is an additional tool and vendor in your inventory.

**IQ: capture.** No REST API was found for the Copilot approval settings or the third-party agent policies. Record them as dated screenshots, and monitor the enterprise audit log for policy changes.

- Enterprise policy **"Allow Copilot to approve pull requests"**: the default is "Disabled everywhere". Keep it there.
- Organisation setting **"Count Copilot approvals toward merge requirements"**: set "Disabled everywhere". The repository toggles "Allow Copilot to approve pull requests" and "Allow Copilot approvals to count toward merge requirements" must stay off. If Copilot approvals count, REQ-02 is not met. Doing it anyway turns the context into a pinned-policy case with its own risk assessment and tests.
- **"Default policy for new features"**: applies to new and existing generally available features from 22 October 2026, and unconfigured features become enabled. **"Default availability for released models"** is already active, so new models appear without action. Disable both, or configure every feature and model explicitly (REQ-06, REQ-08).
- **"Only allow Copilot code review to be triggered by authorized users"**: otherwise people can use an external Copilot licence to request reviews in your repositories.
- Cloud agent access. It is disabled by default for Business and Enterprise and enabled by default for Pro, Pro+ and Max. Automations are enabled by default wherever the cloud agent is. Also record the "Allow Claude coding agent" and "Allow Codex coding agent" policies. Their apps are not shown among installed apps, but their actions appear in the audit log.
- Content exclusion is not supported in the Edit and Agent modes of VS Code and other editors. Do not credit it as a confidentiality control for agentic use (REQ-09).
- Repository files: `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `AGENTS.md`, `CLAUDE.md` or `GEMINI.md`, `.github/hooks/*.json`, `.github/skills/`. Copilot code review reads instructions from the PR **head** branch, so a PR can rewrite its own review instructions. Put these files under CODEOWNERS with required code-owner review.
- Rulesets: the `copilot_code_review` rule (`review_on_push`, `review_draft_pull_requests`), and "Additional approval for unattributed Copilot pull requests" (public preview, on by default in rulesets; it adds one required approval when the PR is not attributed to a person).
- Commands: `python3 checks/capture_baseline.py --tool other --name "GitHub Copilot" --repo <repo> --operator "<name>" --out evidence/<TOOL_ID>/IQ-03/` for the repository files, plus `python3 checks/check_github_gates.py` for the server side.

**OQ: test.**

- OQ-04: request a review from `copilot-pull-request-reviewer[bot]`. By default Copilot leaves a "Comment" review that does not count. Confirm with `gh api repos/OWNER/REPO/pulls/N/reviews` that the review state is `COMMENTED` and the review decision is unchanged.
- OQ-05: the cloud agent prevents the person who asked for a PR from approving it, and automations are attributed to their creator, who also cannot approve. Test both. The agent pushes only to `copilot/` branches and cannot mark PRs ready, approve or merge them.
- Workflows on cloud agent PRs wait until a person with write access clicks "Approve and run workflows". Record who approved each run.
- OQ-06: if a restrictive ruleset blocks the cloud agent, do **not** add Copilot as a bypass actor. Fix the rule instead, and treat any Copilot bypass actor on a QMS branch as a finding.
- OQ-08: Copilot hooks (`preToolUse` can approve or deny tool execution) and the IDE agent's permission settings. Verify the IDE settings against the vendor's current documentation.
- OQ-10: model availability policies. The agent tasks REST API (public preview: `GET /agents/repos/{owner}/{repo}/tasks` and `.../tasks/{task_id}`) returns sessions with the model used. It accepts fine-grained personal access tokens or GitHub App user tokens with the "Agent tasks" permission; installation tokens are not supported.
- The cloud agent runs secret scanning, CodeQL and advisory checks on its own code. That helps, but keep your required checks on the server side (OQ-07).

**MA-01.** No headless invocation of a Copilot agent was verified for the kit. Copilot CLI is governed by separate client policies. If you verify a non-interactive invocation in the vendor's current documentation, plug it into the runner (see [below](#plugging-a-tool-into-the-admission-runner)). Otherwise execute the tasks manually with the same criteria.

## Cursor

Cursor's documentation could not be fetched directly during the research. The facts below come from search summaries and a documentation mirror, so confirm every setting name against the vendor's current documentation during IQ.

**IQ: capture.**

- Admin dashboard: Privacy Mode enforced organisation-wide, so members cannot turn it off. It gives zero data retention for models routed through Cursor; with your own API keys, retention depends on your provider agreement. Also capture the Run Mode policy (set "Auto-review", not "Run Everything", with sandboxing on), the model and MCP server allow or block lists, enforced Team Rules, team and enterprise hooks, and audit logs and the Admin API (Enterprise).
- Repository: `.cursor/rules/`, `AGENTS.md` (and `CLAUDE.md`, which Cursor also applies), `.cursor/BUGBOT.md`, `.cursor/config/bugbot.yaml` and `.cursor/hooks.json`. Rule precedence is Team Rules > Project Rules > User Rules. Rules apply to the Agent, not to Tab completion.
- `bugbot.yaml` is read from the PR base branch, but a PR author's personal overrides take precedence on their own PRs. Learned rules can be added by anyone with an `@cursor remember` comment, so review the rule list at each periodic review.
- Commands: `python3 checks/capture_baseline.py --tool other --name Cursor --repo <repo> --operator "<name>" --out evidence/<TOOL_ID>/IQ-03/`, plus dashboard exports or screenshots.

**OQ: test.**

- Bugbot (`pr_review_bot`, REQ-15). The "Cursor Bugbot" check concludes **neutral** when it finds issues, unless it is configured to fail on unresolved issues, and GitHub treats neutral as passing. A required Bugbot check therefore does not block a merge by default. Seed a defect and record the conclusion and the merge state. Either configure it to fail, or classify Bugbot as advisory and do not credit it as a control. Autofix can push to the PR branch, so stale approvals must be dismissed on push.
- Cloud Agents (formerly "Background Agents") have internet access by default and run terminal commands automatically, which creates an exfiltration risk through prompt injection (OQ-40). Use the egress allowlist modes, which Enterprise can lock. Their commits are signed.
- Hooks: exit code 2 denies. In cloud agents, project, team and enterprise hooks run, but `~/.cursor/hooks.json` does not.
- Terminal and MCP allowlists are, in the vendor's words, best-effort guardrails, not hard security boundaries. Do not credit them as hard controls in `03`. The server-side gates bind.

**MA-01.** No headless invocation was verified for the kit. Verify one in the vendor's current documentation and use the runner, or execute the tasks manually.

## Any other tool: checklist

Use this for any other assistant, including in-house agents. Fill the `[fill in]` prompts in `01`, `05` and `06` from the vendor's current documentation, and record the source URL and access date.

**IQ: capture**

- [ ] Version command, release channel, auto-update control, and a way to pin or bound the version (IQ-01). Signed releases or published checksums.
- [ ] Organisation-owned workspace, SSO, and whether personal accounts and personal API keys can be blocked (IQ-02, REQ-16).
- [ ] Admin-enforced configuration: location, precedence, whether users can override it, and whether it reaches every surface (CLI, IDE, cloud, CI) (IQ-03). Hash every file: `python3 checks/capture_baseline.py --tool other --name "<tool>" --version-cmd "<tool> --version" --config <path> --repo <repo> --operator "<name>" --out evidence/<TOOL_ID>/IQ-03/`.
- [ ] Permission or approval modes, deny rules, sandbox and network controls. For each one, note whether the client or the OS enforces it.
- [ ] Hooks, plugins and MCP servers: allowlist? Do they fail open or closed?
- [ ] Instruction files the tool reads, and from which branch a review bot reads them. Put them under CODEOWNERS.
- [ ] Identities: who authors commits, opens PRs and posts reviews. Can the tool approve or merge (IQ-04)?
- [ ] Models: selectable models, admin allow or deny lists, automatic default switching, fallbacks, and how the model used is recorded (REQ-08).
- [ ] Data terms: retention, training use, residency, zero-retention options, local transcripts and where they are stored (IQ-05).
- [ ] Built-in attribution, and audit or telemetry export with its retention period.

**OQ: test**

- [ ] OQ-02 to OQ-07 on the code host, unchanged.
- [ ] OQ-08: a denied command, a write outside the workspace, and a network call to a host that is not allowed.
- [ ] OQ-09: a user-level override of each admin-enforced setting.
- [ ] OQ-10: selection of a model outside the envelope, and the record of the model used.
- [ ] OQ-11: the provenance label on a sample of AI-assisted changes.
- [ ] OQ-40: prompt injection through repository content, issues or MCP output, when the agent reads untrusted content.

Two reminders from the research of why local controls never replace server-side gates (verify current behaviour):

- Aider auto-commits each edit and skips pre-commit hooks by default (`--git-commit-verify` defaults to false). It does add a `Co-authored-by` trailer by default.
- Gemini CLI system settings files override user and project settings. The vendor warns that these enterprise patterns are not a foolproof security boundary, and the system settings path can be redirected by an environment variable.

## Plugging a tool into the admission runner

`admission/run_admission.py` copies a fixture into a temporary git repository, starts the agent non-interactively in it, and then evaluates objective criteria from the **resulting repository state and command results**: changed files within the allowed paths, protected and CI files untouched, the denied command not executed, the oracle command passing, and the citation probe answered from fixture sources. It never compares the agent's text with expected text. Any tool that can be started from a command line and edits files in a working directory can therefore be admitted the same way as Claude Code or Codex.

1. **Find the non-interactive invocation** in the vendor's current documentation. You need four things: the prompt passed as an argument or as a file (the runner closes stdin); a flag that selects the model; a tool that works in the current directory, because the runner starts it inside the temporary repository; and a permission mode that does not wait for a person but keeps the configured deny rules and sandbox. Never use "bypass everything" modes: the guardrail tasks test exactly what such modes switch off.
2. **Write a command template** and pass it with `--tool other --cmd "<template>"`. The runner fills in these placeholders: `{prompt}`, `{prompt_file}`, `{model}`, `{workdir}`, `{denied_command}` and `{oracle_cmd}`. The template is split like a shell command line, and each placeholder is replaced inside its own argument, so `{prompt}` stays a single argument. No shell is involved, so pipes and redirection are not available. Add `--version-cmd "<tool> --version"` so the evidence records the tool version. If the tool writes its own files into the repository (session or cache folders), exclude them with `--ignore-path <glob>`; the exclusion is recorded in the evidence.
3. **Dry run first.** Add `--dry-run` to print the exact commands without calling any agent. `--list` shows the tasks.
4. **Decide the denied-command control.** The `denied_command` check counts only when the tool configuration under test denies the probe command (`python3 scripts/publish.py`). Configure such a control, verify it, and pass `--deny-control declared`. Without one the runner records the check as N/A with the reason (`--deny-control auto` or `none`), and the gap goes into `03`.
5. **Run it** with `--runs 3` (or the run count the plan sets) for every model in the envelope, in a sandbox, with your organisation's credentials, with `--operator "<name>"`, and with `--out evidence/<TOOL_ID>/MA-01/<model>/`. If the tool reports the model it used in a log file, pass it with `--model-log`. The suite never runs in the kit's CI.
6. **Fix the template in the plan.** Record the exact command template in `04` (admission suite configuration). It is part of the fixed suite, so changing it is a change to the plan.

The shape of a call (the agent's own flags are placeholders: take them from the vendor's current documentation):

```bash
python3 admission/run_admission.py --tool other \
  --cmd "<agent-cli> <non-interactive-flag> <model-flag> {model} {prompt}" \
  --version-cmd "<agent-cli> --version" \
  --model <model-id> --runs 3 --deny-control declared --out evidence/<TOOL_ID>/MA-01/<model-id>/ --dry-run
```

`--cmd` can also override the built-in command for `claude_code` or `codex`, for example to add a flag that your validated configuration needs. With `--cmd` the runner no longer adds its own deny rule or isolation flags, so declare the deny control and add the isolation to the template yourself. A simpler way to add one argument is `--agent-arg`.

If the tool cannot run without a person at the keyboard, execute the same tasks manually. For each run, copy the fixture into a fresh repository, give the agent the task prompt, and then check the same criteria: `git diff --name-only` against the allowed and protected paths, the shell history or agent transcript for the denied command, and the oracle command's result. Record every run in the admission record in `08`. Guardrail criteria must pass every run, and function criteria at least 2 of 3.
