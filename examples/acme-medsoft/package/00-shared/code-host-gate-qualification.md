> FICTIONAL EXAMPLE, invented for illustration only. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are made up to show what an executed package looks like. Model ids are placeholders. Each person signs in the eQMS, shown here only as "[signed in eQMS]".

# ACME-VAL-GEN-03 Code-host gate qualification

| Field | Value |
|---|---|
| Document ID | ACME-VAL-GEN-03 |
| Title | Code-host gate qualification (OQ-01 to OQ-07, OQ-12 at code-host level) |
| Version | 1.0, approved before execution on 2026-10-19; executed 2026-10-21 and 2026-10-22 |
| Organisation | Acme MedSoft |
| Product context | Class II SaMD (FDA 510(k)); EU MDR Class IIa planned |
| Code host | GitHub |
| Prepared by (role) | Validation Engineer |
| Approved before execution by (role) | Head of QA |
| Rendered | 2026-10-18 (kit 0.2.0) |

> Generated with the AI Coding Tool Validation Kit 0.2.0. Complete every `[fill in]` before review. This record is approved **before** any test in it is executed. Approval is given by the approver personally in the eQMS.

## 1. Purpose and use

The human approval gate, the required checks and the branch protection are properties of the code host, shared by every AI tool. This record proves them **once per code host and set of repositories**, for every AI tool in scope, so each tool's protocol skips the same platform tests. Each tool's test protocol references this record and adds only its tool-specific steps (for example the agent itself trying to merge, push or approve).

- A tool protocol may credit this record when the repositories it covers and the protection export are the same as here, and the record is not older than the last code-host rule change and not older than 12 months.
- A code-host rule or setting change (T12 in each tool's change document) re-runs the affected tests here.
- Acceptance criteria are the same as in the tool protocols and are fixed before execution. A result is Pass, Fail, or N/A with a written justification. Any difference from the expected result is entered in the deviation log (section 7) and assessed before any release decision that relies on this record.
- Evidence goes to `evidence/GEN/<TEST-ID>/`. Every kit script records who ran it on which machine; pass `--operator "<name>"` or set `KIT_OPERATOR`.
- AI tools are already in use: OQ-01 also covers the historical sample defined in each tool's validation plan (section 12).

Tool protocols that reference this record:

| Tool | Test protocol | Surfaces | AI, bot and app identities on the code host (from IQ-04) |
|---|---|---|---|
| Claude Code (Anthropic) | ACME-VAL-CLAUDE-05 | `local_cli_ide` `pr_review_bot` `ci_headless`  | `acme-claude-reviewer[bot]` (custom GitHub App, Contents read, Issues and Pull requests read/write); GitHub Actions workflow token (`contents: read`); developer accounts for local use |
| OpenAI Codex (OpenAI) | ACME-VAL-CODEX-05 | `local_cli_ide` `cloud_agent`  | the vendor's GitHub connector app (cloud tasks and `@codex review`); developer accounts for local use |

## 2. Test environment and identities

Filled in before execution (2026-10-19).

| Item | Value |
|---|---|
| Production repositories in scope (at least 2 when available, one product repository) | `acme-medsoft/lumen-core`, `acme-medsoft/lumen-app` (product), `acme-medsoft/qa-tooling` (tooling), `acme-medsoft/qms-docs` (controlled documents) |
| Sandbox / canary repository (same protection as production) | `acme-medsoft/val-sandbox`; the organisation ruleset "protect-main" applies to every repository; canary runs also on `acme-medsoft/lumen-core` |
| How the sandbox protection was copied and compared | `python3 checks/mirror_protection.py --from acme-medsoft/lumen-core --to acme-medsoft/val-sandbox --operator "Alex Example" --out evidence/GEN/OQ-02/` (dry run, then `--apply`, on 2026-10-14); comparison matched; export SHA-256: `90d3c9f298200118441a7eb9e14e8b742762016437959d3a107cc19604a1f859` |
| User A: PR author (write access, no admin rights) | Dev One (Claude Code tests), Dev Two (Codex tests) |
| User B: qualified reviewer (on the trained-reviewer list) | Rev One |
| User C: second reviewer / pusher | Rev Two |
| Admin: repository or organisation admin | Casey Admin (organisation owner) |
| Protection export (branch protection, rulesets, approval settings) and SHA-256 | `evidence/GEN/OQ-03/20261021-protection-export-4-repositories.json`, SHA-256 `6e3520ed45e6efe11ef0b9e0e9f95bebceb6372311cada97d070c4731ebeca98` |

## 3. Tests at code-host level (GitHub)

### OQ-01 Human gate, positive: real AI-assisted PRs

| Field | Content |
|---|---|
| Verifies | REQ-01, REQ-05 |
| Type | historical / unscripted |
| Objective | Show from real records that AI-assisted changes reached the protected branch only after approval by a qualified human other than the author and the agent launcher, on the final commit, with the required checks passed. |
| Acceptance criterion | For 100% of sampled PRs (at least 3 AI-assisted PRs per repository for each tool): at least one approval by a human (not a bot or app), who is not the author or agent launcher, is on the qualified-reviewer list, approved before merge and on the final commit; required checks passed, or their evidence expired and is handled as defined in the tool's validation plan. |
| Evidence | Script JSON / Markdown output with SHA-256, sample list, reviewer training references. |

Steps:

1. For each repository run `python3 checks/check_github_gates.py --repo OWNER/REPO --branch main --prs 20 --operator "<name>" --out evidence/GEN/OQ-01/`. Add `--non-human LOGIN` for every machine user used by an agent, and `--launcher PR=LOGIN` where the agent launcher is recorded outside GitHub (for example a cloud task record).
2. From the merged PRs in the output, select at least 3 AI-assisted PRs per repository for each tool (by provenance label). Include at least one PR that changes product or safety-relevant code when product code is in scope.
3. For each sampled PR confirm from the output: approving review by a `User` identity; reviewer differs from the PR author and from the agent launcher; review before merge and on the final commit; required checks concluded successfully (`checks` section of the output; "evidence expired" is reported separately from "failed").
4. Check each approver against the qualified-reviewer list and the date of their training.
5. Record, per PR, the time from ready-for-review to approval and the number of review comments (input to PQ-01 and PQ-02).

### OQ-02 Merge without approval is blocked (canary PR)

| Field | Content |
|---|---|
| Verifies | REQ-01 |
| Type | scripted, negative |
| Objective | Prove at server level that an unapproved change cannot be merged into the protected branch. |
| Acceptance criterion | Every merge attempt without approval is refused by the server in every repository tested, for a non-admin identity; the protected branch HEAD SHA is unchanged. |
| Evidence | Canary script output (HTTP status and message of the merge attempt), PR JSON before and after, protected branch SHA before and after. |

Steps:

1. As User A run `checks/canary/run_canary.sh --repo OWNER/REPO --operator "<name>" --out evidence/GEN/OQ-02/` on each repository tested. The script attempts the merge through the REST API (`PUT repos/{owner}/{repo}/pulls/<n>/merge`), so the server itself decides; it records the HTTP status and message and the protected branch SHA before and after. If the repository uses a merge queue, the result is "inconclusive": test the queue instead (an unapproved canary must not be merged by the queue).
2. Save `gh pr view <n> --json number,author,reviews,reviewDecision,mergedAt,statusCheckRollup` for the canary PR.
3. Close the canary PR and delete the branch (`--auto-cleanup` or `--cleanup`).

### OQ-03 Direct push to protected branch is blocked

| Field | Content |
|---|---|
| Verifies | REQ-04 |
| Type | scripted, negative |
| Objective | Prove that no human or token can push directly to the protected branch. |
| Acceptance criterion | Every direct push is rejected; force push and deletion are not allowed; protected branch HEAD SHA unchanged. |
| Evidence | Push output, protection export, SHA before and after. |

Steps:

1. Record the protected branch HEAD SHA.
2. Make a trivial commit and run `git push origin HEAD:main` as User A; run the canary with `--try-direct-push` (contents API).
3. Save `gh api repos/{owner}/{repo}/branches/main/protection` and `gh api repos/{owner}/{repo}/rules/branches/main`. Confirm force pushes and deletion are not allowed (classic `allow_force_pushes` / `allow_deletions`, or ruleset rules `non_fast_forward` / `deletion`).
4. Confirm the HEAD SHA is unchanged.

### OQ-04 AI / bot / Actions approval is not counted

| Field | Content |
|---|---|
| Verifies | REQ-02, REQ-15 |
| Type | scripted, negative |
| Objective | Prove that approvals by bots, apps or CI tokens do not satisfy the required approval, and that the code host's own AI approval features are off. |
| Acceptance criterion | No bot, app or CI approval changes the review decision to approved; no AI or bot identity is a bypass actor; the platform settings match the baseline. The observed result settles undocumented behaviour. |
| Evidence | Settings JSON, reviews JSON (`user.type`, `state`), PR JSON, workflow output, dated screenshots where no API exists. |

Steps:

1. Save `gh api repos/{owner}/{repo}/actions/permissions/workflow` and `gh api orgs/{org}/actions/permissions/workflow`. Expected: `can_approve_pull_request_reviews` is `false` at both levels.
2. In the sandbox repository, run a workflow step that executes `gh pr review <n> --approve` with the workflow token on a canary PR. Expected: the call fails and no approving review by the Actions bot exists.
3. For every app with pull-request write permission (AI reviewer or other, for every tool in section 1), submit an approving review on the canary PR with its token, if available. GitHub does not document whether app approvals count, so record the review decision before and after. If an app approval changes it to approved, the test fails: require code-owner or required-reviewer approval from human teams and remove pull-request write from the app.
4. Save the reviews: `gh api repos/{owner}/{repo}/pulls/<n>/reviews --jq '.[] | {login: .user.login, type: .user.type, state, commit_id, submitted_at}'`.
5. Check that no ruleset lists an AI or bot integration as a bypass actor: `gh api repos/{owner}/{repo}/rulesets/<id> --jq '.bypass_actors'`.
6. GitHub AI approval settings, even if Copilot is not a tool under validation: capture dated screenshots (no API was found) of the enterprise policy "Allow Copilot to approve pull requests", the organisation setting "Count Copilot approvals toward merge requirements" and the repository toggles "Allow Copilot to approve pull requests" and "Allow Copilot approvals to count toward merge requirements", plus the ruleset `copilot_code_review` rule. Expected: "Disabled everywhere" / off. Set the enterprise "Default policy for new features" explicitly: unless it is configured, unconfigured generally available features are enabled automatically from 2026-10-22.

### OQ-05 Author, last pusher and agent launcher cannot satisfy the approval

| Field | Content |
|---|---|
| Verifies | REQ-01, REQ-02 |
| Type | scripted, negative |
| Objective | Prove that the PR author and the last pusher cannot provide the required approval, that approvals become stale when new commits arrive, and that PRs authored by an agent identity need the compensating control. |
| Acceptance criterion | Author self-approval is refused or not counted; an approval by someone who pushed the latest commits is not counted; an approval given before a new push is dismissed or not counted; merge stays blocked in each case; PRs authored by a bot or agent identity require 2 approvals or code-owner approval by a human team. |
| Evidence | API responses, reviews JSON with `commit_id` compared with the PR head, approval-state snapshots, protection export. |

Steps:

1. Confirm in the protection export (OQ-03) that `require_last_push_approval` and stale-review dismissal are enabled (classic `dismiss_stale_reviews`, or ruleset `dismiss_stale_reviews_on_push`).
2. User A opens a PR and runs `gh pr review <n> --approve` (canary option `--try-self-approve`). Expected: refused; review decision unchanged. GitHub enforces this for every author, so this step proves the platform rule; the agent-launcher rule has its own step.
3. User B pushes a commit to User A's branch, then approves. Expected: B's approval is not counted (B made the most recent push).
4. User C approves; User B then pushes a new commit. Expected: C's approval is dismissed or no longer counts; merge blocked until re-approval.
5. Save the reviews JSON and `gh pr view <n> --json reviews,latestReviews,reviewDecision,headRefOid` after each step.
6. Compensating control for agent-authored PRs: confirm that a ruleset or CODEOWNERS rule requires 2 approvals, or code-owner approval by a human team, for PRs whose author is a bot or a machine user used by an agent. When the agent has its own identity, GitHub counts the approval of the person who launched it; the rule "the launcher does not approve" is then procedural (ACME-VAL-GEN-01) and is checked per PR by `checks/check_github_gates.py` (`--launcher`, trigger comments). The tool-specific attempt (an agent-authored PR approved by its launcher) is executed in each tool's protocol.

### OQ-06 Admin bypass prevented, or logged and reviewed

| Field | Content |
|---|---|
| Verifies | REQ-04 |
| Type | scripted |
| Objective | Show that administrators cannot bypass the gate silently: either bypass is impossible, or every bypass leaves an audit record that is reviewed. |
| Acceptance criterion | Either an admin merge without approval is refused, or the authorised bypass appears in the platform's bypass / audit records and in the review routine within the defined period; no bypass mode that skips audit entries is configured. |
| Evidence | Protection / ruleset JSON (bypass actors and modes), merge attempt output, bypass and audit-log exports. |

Steps:

1. Save `gh api repos/{owner}/{repo}/branches/main/protection/enforce_admins` and every ruleset with its `bypass_actors` (actor type, id, `bypass_mode`). Expected: `enforce_admins` enabled or no bypass actors; no `bypass_mode` "exempt" (exempt actors are not evaluated and no bypass audit entry is created: treat it as a nonconformity).
2. As Admin, run the canary (it attempts the merge through the REST API, where an admin bypass would succeed) and, with `--try-admin`, `gh pr merge <n> --admin`. Expected: refused when admins are not exempt.
3. If bypass is allowed by design: perform one authorised bypass in the sandbox repository, then export it with `gh api --paginate "repos/{owner}/{repo}/rulesets/rule-suites?time_period=month&rule_suite_result=bypass"` and from the organisation audit log (export or streaming; the REST audit-log API needs Enterprise Cloud). The audit log shows 180 days and Git events only 7 days, so the review routine must export bypass records before they expire.
4. Record any push-protection exemptions or bypass lists for agent and bot identities, with their justification.

### OQ-07 Required checks block canary violations

| Field | Content |
|---|---|
| Verifies | REQ-03, REQ-09 |
| Type | scripted, negative |
| Objective | Prove that required checks block a failing test, an unapproved dependency and a committed secret, even when a human has approved, and that a required check cannot be faked. |
| Acceptance criterion | All three violation types are blocked in every repository tested; a spoofed status does not unblock the merge; secret push protection rejects the push. An attempt whose preconditions (approval present, target check concluded failure) are not met is inconclusive and repeated. |
| Evidence | Canary PR JSON with check results, push output, API responses, protection / ruleset export showing the check source pinned to an app. |

Steps:

1. Create three canary PRs (variants in `checks/canary/README.md`), each approved by User B to isolate the check gate (`--wait-for-approval`, with `--expect-failing-check <check name>` for a and b): a. a change that makes a unit test fail; b. a new dependency that is not on the approved list, including a plausible but non-existent package name (reference gate: `checks/soup_gate.py`, workflow `examples/github-workflow-soup-gate.yml`); c. a file containing the vendor's test secret pattern (`--expect-push-rejected`).
2. Before each merge attempt the canary confirms that the review decision is APPROVED and that the target check concluded with failure; otherwise the result is inconclusive.
3. Try to merge each PR. Expected: blocked by the required check (a, b) or rejected at push (c).
4. Save `gh api repos/{owner}/{repo} --jq '.security_and_analysis'` (expected `secret_scanning_push_protection.status` "enabled") and the check runs: `gh api --paginate repos/{owner}/{repo}/commits/<sha>/check-runs`.
5. Spoofing: with a token that has write access, post a success status for the required context on canary PR (a) (`POST /repos/{owner}/{repo}/statuses/<sha>`). Expected: merge stays blocked because the required check is pinned to its app (classic `checks[].app_id`, ruleset `integration_id`).
6. Record the retention of checks and logs (`gh api repos/{owner}/{repo}/actions/permissions/artifact-and-log-retention`) and export the check evidence before it expires.

### OQ-12 Reversibility of an AI-assisted change

| Field | Content |
|---|---|
| Verifies | REQ-11 |
| Type | scripted |
| Objective | Show that an AI-assisted change can be reverted through the normal gate, with full traceability, and that history cannot be rewritten. |
| Acceptance criterion | The revert is merged through the gate; original change and revert are both traceable to named humans and linked; force push and branch deletion are refused. |
| Evidence | PR JSON of original and revert, `git log` excerpt, refused force-push output. |

Steps:

1. Merge an AI-assisted change in the sandbox repository through the normal gate.
2. Revert it with `git revert <sha>` on a branch and open a PR that references the original; merge it through the gate.
3. Confirm the history shows both commits, their authors and approvers, and the link between them.
4. Try `git push --force` to the protected branch. Expected: refused.
5. Controlled records: restore the previous version of an AI-assisted edit in the document / record system and confirm the audit trail shows edit, restoration, person and time.

Per-step record (required when any tool's determination is high; one table per test, or the same columns in an evidence file named in the execution record):

| Test | Step | Expected | Actual | Pass / Fail | Evidence file |
|---|---|---|---|---|---|
| OQ-01 | 1 | Gate script PASS on each repository | PASS on lumen-core, lumen-app, qa-tooling, qms-docs (20 merged PRs each) | Pass | evidence/GEN/OQ-01/github-gates_* (4 files) |
| OQ-01 | 2 | At least 3 AI-assisted PRs per repository and tool, one changing safety-relevant code | Claude Code: 13 PRs (lumen-core 4 incl. #412 alarm-threshold logic; lumen-app 3; qa-tooling 3; qms-docs 3). OpenAI Codex: 7 PRs (lumen-core 3, qa-tooling 4) | Pass | `evidence/GEN/OQ-01/20261021-oq01-sample-per-tool.md` |
| OQ-01 | 3 | Approval by a `User`, not author or launcher, before merge, on the head commit; required checks passed | 20 of 20; required checks concluded success on the merge head of 80 of 80 PRs; 0 expired, 0 failed | Pass | github-gates_* (`checks` section) |
| OQ-01 | 4 | Every approver qualified and trained before the approval | 8 approvers on the ACME-QP-12 qualified-reviewer list, code-review training dated before their first approval; ACME-VAL-GEN-01 training on 2026-10-19, after the sampled approvals (covered by NC-2026-031) | Pass | `evidence/GEN/OQ-01/20261021-oq01-sample-per-tool.md` |
| OQ-01 | 5 | Review time and comments recorded | Median ready-for-review to approval 47 minutes (Claude Code sample), 39 minutes (Codex sample) | Pass | same |
| OQ-02 | 1 | Server refuses the merge without approval; HEAD unchanged | val-sandbox #7 and lumen-core #431: `PUT .../pulls/<n>/merge` refused by the server for Dev One (HTTP status and message recorded); review decision REVIEW_REQUIRED; HEAD SHA unchanged; no merge queue | Pass | evidence/GEN/OQ-02/canary_* (2 files) |
| OQ-02 | 1a | Same attempt by the admin identity is refused | Repeated on val-sandbox as Casey Admin (`actor_is_admin` true): refused; the ruleset has no bypass actors | Pass | `evidence/GEN/OQ-02/canary_acme-medsoft-val-sandbox_20261021T091530Z.json` |
| OQ-02 | 2-3 | PR JSON saved; canary closed | PR JSON before and after in the canary evidence; PRs closed and branches deleted (`--auto-cleanup`) | Pass | canary_* (raw step output) |
| OQ-03 | 1-4 | Direct push and contents-API commit rejected; force push and deletion blocked | `git push origin HEAD:main` rejected for Dev One in val-sandbox and lumen-core; `--try-direct-push` refused; ruleset rules `non_fast_forward` and `deletion` active (classic endpoint: not protected, rulesets only); HEAD SHA unchanged | Pass | evidence/GEN/OQ-03/* |
| OQ-04 | 1 | `can_approve_pull_request_reviews` false for repository and organisation | false / false | Pass | `evidence/GEN/OQ-04/20261021-actions-workflow-permissions-repo-and-org.json` |
| OQ-04 | 2 | Workflow-token approval fails | `gh pr review --approve` in a workflow step failed; no review created | Pass | `evidence/GEN/OQ-04/20261021-canary-reviews-before-after.json` |
| OQ-04 | 3-4 | App approval does not change the review decision | Approval with the token of `acme-claude-reviewer[bot]` recorded, review decision stayed REVIEW_REQUIRED (code-owner approval by the human team `@acme-medsoft/qualified-reviewers` required); the gate script flagged it. The Codex connector app has no approve permission in use (`@codex review` posts COMMENTED, ACME-VAL-CODEX-05 OQ-04) | Pass | same |
| OQ-04 | 5 | No AI or bot bypass actor | Ruleset "protect-main": no bypass actors | Pass | `evidence/GEN/OQ-06/20261021-rulesets-bypass-actors-and-rule-suites.json` |
| OQ-04 | 6 | Copilot approval settings off everywhere; default policy for new features set | Copilot not licensed; enterprise policy "Allow Copilot to approve pull requests" disabled, organisation setting "Count Copilot approvals toward merge requirements" off, repository toggles off, no `copilot_code_review` rule; enterprise "Default policy for new features" set explicitly to disabled on 2026-10-20 (dated screenshots) | Pass | `evidence/GEN/OQ-04/20261021-copilot-approval-settings-screenshots.pdf` |
| OQ-05 | 1 | `require_last_push_approval` and stale-review dismissal enabled | both true in the ruleset | Pass | `evidence/GEN/OQ-03/20261021-protection-export-4-repositories.json` |
| OQ-05 | 2 | Author self-approval refused | refused (`--try-self-approve`); review decision unchanged | Pass | `evidence/GEN/OQ-05/canary_acme-medsoft-val-sandbox_20261021T110520Z.json` |
| OQ-05 | 3-5 | Last-pusher approval not counted; earlier approval dismissed on push | Rev One pushed to Dev One's branch and approved: not counted; Rev Two approved, Rev One pushed again: approval dismissed, merge blocked until Rev Two re-approved on the new head | Pass | `evidence/GEN/OQ-05/20261021-oq05-review-states.json` |
| OQ-05 | 6 | Compensating control for agent-authored PRs | Repository ruleset `agent-prs` on qa-tooling and val-sandbox, the only repositories where an agent identity may open PRs (OpenAI Codex cloud restriction), requires 2 approving reviews; in the other repositories no AI tool opens PRs under its own identity (IQ-04 of both tools). Per-PR check with `check_github_gates.py --launcher`; the tool attempt is in ACME-VAL-CODEX-05 OQ-05 | Pass | `evidence/GEN/OQ-05/20261021-agent-prs-ruleset-export.json` |
| OQ-06 | 1 | No bypass actors and no `exempt` mode | no bypass actors in any ruleset | Pass | `evidence/GEN/OQ-06/20261021-rulesets-bypass-actors-and-rule-suites.json` |
| OQ-06 | 2 | Admin merge through the API and `gh pr merge --admin` refused | both refused for Casey Admin | Pass | `evidence/GEN/OQ-06/canary_acme-medsoft-val-sandbox_20261021T120015Z.json` |
| OQ-06 | 3 | Bypass records exported and reviewed | Rule-suite export of the last month: 0 bypass events; organisation audit log exported weekly into the evidence store | Pass | same |
| OQ-06 | 4 | No push-protection exemptions for agents or bots | none | Pass | same |
| OQ-07 | 1-3 | Failing test (a) and unapproved dependency (b) blocked after approval; secret (c) rejected at push | val-sandbox and lumen-core, each approved by Rev One: (a) blocked by `ci / unit-tests`; (b) `acme-fastjson-utils` (non-existent and absent from the SOUP register) blocked by `soup-gate`; (c) push rejected by secret scanning push protection. Preconditions confirmed by the canary before each attempt (APPROVED, target check failed) | Pass | evidence/GEN/OQ-07/canary_* (6 files) |
| OQ-07 | 4 | Push protection enabled | `secret_scanning_push_protection` enabled on all 5 repositories | Pass | `evidence/GEN/OQ-07/20261021-status-spoof-attempt-and-security-settings.json` |
| OQ-07 | 5 | Spoofed status does not unblock | success status for `ci / unit-tests` posted with a write token: merge stayed blocked (checks pinned to the GitHub Actions app) | Pass | same |
| OQ-07 | 6 | Retention recorded; check evidence exported | Retention raised from 90 to 400 days on all 5 repositories on 2026-10-20; evidence-export workflow active | Pass | `evidence/GEN/OQ-07/20261021-artifact-and-log-retention.json` |
| OQ-12 | 1-3 | Revert through the gate, both changes traceable and linked | Claude Code-assisted PR val-sandbox #15 reverted by #16, Codex-assisted PR #33 reverted by #34, each approved by Rev Two; history shows commits, authors, approvers and links | Pass | `evidence/GEN/OQ-12/20261022-oq12-revert-prs-and-force-push.json` |
| OQ-12 | 4 | Force push refused | `git push --force` to main refused | Pass | same |
| OQ-12 | 5 | Record restoration visible in the audit trail | qms-docs: previous version of an AI-assisted draft (DOC-TEST-01) restored; history and eQMS audit trail show edit, restoration, person and time | Pass | same |

## 4. Execution records

| ID | Verifies | Result (Pass / Fail / Inconclusive / N/A) | Executed by / date and time (UTC) | Repositories | Deviation ref |
|---|---|---|---|---|---|
| OQ-01 | REQ-01, REQ-05 | Pass | Alex Example / 2026-10-21 07:10 to 08:40 | lumen-core, lumen-app, qa-tooling, qms-docs | none |
| OQ-02 | REQ-01 | Pass | Alex Example (User A: Dev One; admin run: Casey Admin) / 2026-10-21 09:00 to 09:40 | val-sandbox, lumen-core | none |
| OQ-03 | REQ-04 | Pass | Alex Example (User A: Dev One) / 2026-10-21 10:00 to 10:15 | val-sandbox, lumen-core | none |
| OQ-04 | REQ-02, REQ-15 | Pass | Alex Example / 2026-10-21 10:25 to 11:00 | val-sandbox (organisation settings) | none |
| OQ-05 | REQ-01, REQ-02 | Pass | Alex Example (Users A/B/C: Dev One, Rev One, Rev Two) / 2026-10-21 11:05 to 11:45 | val-sandbox | none |
| OQ-06 | REQ-04 | Pass | Alex Example (Admin: Casey Admin) / 2026-10-21 12:00 to 12:15 | val-sandbox (organisation ruleset) | none |
| OQ-07 | REQ-03, REQ-09 | Pass | Alex Example (approvals by Rev One) / 2026-10-21 13:00 to 14:55 | val-sandbox, lumen-core | none |
| OQ-12 | REQ-11 | Pass | Alex Example (approvals by Rev Two) / 2026-10-22 10:30 to 10:55 | val-sandbox, qms-docs | none |

An "Inconclusive" result is repeated before it can be credited; it is never counted as Pass.

## 5. Evidence index

| Test ID | Evidence file (`evidence/GEN/<TEST-ID>/...`) | SHA-256 | Captured (UTC) | Captured by |
|---|---|---|---|---|
| OQ-01 | `evidence/GEN/OQ-01/github-gates_acme-medsoft-lumen-core_main_20261021T071502Z.json` (+ `.md`, `.json.sha256`) | `5188c7de9c4571d4ae4f599d25497fb43dd703737a26cce1b4b181f3a33d3a1b` | 2026-10-21 07:15 | Alex Example |
| OQ-01 | `evidence/GEN/OQ-01/github-gates_acme-medsoft-lumen-app_main_20261021T072210Z.json` (+ `.md`, `.json.sha256`) | `54fde5edc82fc8df2c6951ceb152159b05e4c7dd29c3895ecc10bad852ce5772` | 2026-10-21 07:22 | Alex Example |
| OQ-01 | `evidence/GEN/OQ-01/github-gates_acme-medsoft-qa-tooling_main_20261021T072845Z.json` (+ `.md`, `.json.sha256`) | `7feb877ba3d76def4796c907c638d8d4867a3f28fdedf6b6816ac8c0ded1f5e8` | 2026-10-21 07:28 | Alex Example |
| OQ-01 | `evidence/GEN/OQ-01/github-gates_acme-medsoft-qms-docs_main_20261021T073320Z.json` (+ `.md`, `.json.sha256`) | `7bd07e50475b00e8cc3d14b0bfffc865a25f84f45055b4a98a90016bf08dd1cd` | 2026-10-21 07:33 | Alex Example |
| OQ-01 | `evidence/GEN/OQ-01/20261021-oq01-sample-per-tool.md` | `c5d6530a830f88e1abb584c5bbf5c1364e65ec8740d8cb576be1bcff1a88867a` | 2026-10-21 08:40 | Alex Example |
| OQ-02 | `evidence/GEN/OQ-02/mirror-protection_acme-medsoft-lumen-core_to_val-sandbox_20261014T141030Z.json` (+ `.md`, `.json.sha256`) | `90d3c9f298200118441a7eb9e14e8b742762016437959d3a107cc19604a1f859` | 2026-10-14 14:10 | Alex Example |
| OQ-02 | `evidence/GEN/OQ-02/canary_acme-medsoft-val-sandbox_20261021T090102Z.json` (+ `.md`, `.json.sha256`) | `c74c236c6944aaebbcbff3d82ca556be024d4338320ec43e11de2e3e9bb79de9` | 2026-10-21 09:01 | Alex Example |
| OQ-02 | `evidence/GEN/OQ-02/canary_acme-medsoft-val-sandbox_20261021T091530Z.json` (+ `.md`, `.json.sha256`) | `12475a6cd864f440d5fd1cdfc244af040b39d2e2e91d23edf35993adb1c86d1a` | 2026-10-21 09:15 | Alex Example |
| OQ-02 | `evidence/GEN/OQ-02/canary_acme-medsoft-lumen-core_20261021T093045Z.json` (+ `.md`, `.json.sha256`) | `d52e7de35ab5034b395b60649c09026837c032bbb68138ac433ee4c8115643eb` | 2026-10-21 09:30 | Alex Example |
| OQ-03 | `evidence/GEN/OQ-03/20261021-direct-push-refused.txt` | `90af5a168111f7a4063e13c1a9a79b1a1a8d6e03a5e0840767187e11f36e40c9` | 2026-10-21 10:05 | Alex Example |
| OQ-03 | `evidence/GEN/OQ-03/20261021-protection-export-4-repositories.json` | `6e3520ed45e6efe11ef0b9e0e9f95bebceb6372311cada97d070c4731ebeca98` | 2026-10-21 10:12 | Alex Example |
| OQ-04 | `evidence/GEN/OQ-04/20261021-actions-workflow-permissions-repo-and-org.json` | `e6df3c90e92e2942813860febc0ae9b446260ddbee0ae4c8c9484d2c78972216` | 2026-10-21 10:30 | Alex Example |
| OQ-04 | `evidence/GEN/OQ-04/20261021-canary-reviews-before-after.json` | `f78aa906a2eac9b8e34884e2dcb6851d33ebc95b2986e953c3839c7def14b620` | 2026-10-21 10:48 | Alex Example |
| OQ-04 | `evidence/GEN/OQ-04/20261021-copilot-approval-settings-screenshots.pdf` | `5e1c27df1cf13c10a65d77cebe58cc2336c3611b9f6e67547b940bf316ceecdc` | 2026-10-21 10:58 | Alex Example |
| OQ-05 | `evidence/GEN/OQ-05/canary_acme-medsoft-val-sandbox_20261021T110520Z.json` (+ `.md`, `.json.sha256`) | `61a46c502d2da0ebc3f1a4b8db7f7866d0ba791cdf36c62cb506f4378f889655` | 2026-10-21 11:05 | Alex Example |
| OQ-05 | `evidence/GEN/OQ-05/20261021-oq05-review-states.json` | `b0976f33b11f4f84693c50da671a23b450f8c86e407d301507679065b235326e` | 2026-10-21 11:40 | Alex Example |
| OQ-05 | `evidence/GEN/OQ-05/20261021-agent-prs-ruleset-export.json` | `fef39ebd05fdbaf9daaa19979c06d79e54dbd45dd949bd0a2f13684457772538` | 2026-10-21 11:45 | Alex Example |
| OQ-06 | `evidence/GEN/OQ-06/canary_acme-medsoft-val-sandbox_20261021T120015Z.json` (+ `.md`, `.json.sha256`) | `a9b4c5f2e94e2a7fe6ad0dcd938165d814426a2e6bf5b19505bf188e3b5f91aa` | 2026-10-21 12:00 | Alex Example |
| OQ-06 | `evidence/GEN/OQ-06/20261021-rulesets-bypass-actors-and-rule-suites.json` | `97c91672d0688c39c15648fcbcae7ccb8c79a6d0ed182c3172882cfc3198f7e0` | 2026-10-21 12:10 | Alex Example |
| OQ-07 | `evidence/GEN/OQ-07/canary_acme-medsoft-val-sandbox_20261021T130510Z.json` (+ `.md`, `.json.sha256`) | `7fa037fcb113062c961756260d0a8d653bcd54f2902e10a98375c365cd73c5b5` | 2026-10-21 13:05 | Alex Example |
| OQ-07 | `evidence/GEN/OQ-07/canary_acme-medsoft-val-sandbox_20261021T132030Z.json` (+ `.md`, `.json.sha256`) | `7256a3bc30e55172ca2641c77aec0f8529596ed96ff2f63ad9afdf55d308fdec` | 2026-10-21 13:20 | Alex Example |
| OQ-07 | `evidence/GEN/OQ-07/canary_acme-medsoft-val-sandbox_20261021T133555Z.json` (+ `.md`, `.json.sha256`) | `97d19329bed871ca4884bcec745fee4b98efc788e6490abe3e95e8c537f76227` | 2026-10-21 13:35 | Alex Example |
| OQ-07 | `evidence/GEN/OQ-07/canary_acme-medsoft-lumen-core_20261021T140100Z.json` (+ `.md`, `.json.sha256`) | `f295e9fc21e65497577167ef16bfbd6af7578acf7e72ca6063c92858bcca153b` | 2026-10-21 14:01 | Alex Example |
| OQ-07 | `evidence/GEN/OQ-07/canary_acme-medsoft-lumen-core_20261021T141540Z.json` (+ `.md`, `.json.sha256`) | `9d0c2011f675ca8714d6d418064a006e009bdb7a1b60d75621ec1a843a679b1a` | 2026-10-21 14:15 | Alex Example |
| OQ-07 | `evidence/GEN/OQ-07/canary_acme-medsoft-lumen-core_20261021T143010Z.json` (+ `.md`, `.json.sha256`) | `ba9ca3937ece320df78cc5e9051f901d9bc7782aa10d9c5896fdb7f64e3a63eb` | 2026-10-21 14:30 | Alex Example |
| OQ-07 | `evidence/GEN/OQ-07/20261021-status-spoof-attempt-and-security-settings.json` | `0500a60534100e389462eada4bfa0fdaf62af45dd8a6fb72636479f04ea1f198` | 2026-10-21 14:50 | Alex Example |
| OQ-07 | `evidence/GEN/OQ-07/20261021-artifact-and-log-retention.json` | `78e6c4cb070e05ae92edbb4d1c2e79b7755cdfe66f35d3b93a528f4a9e9fa7de` | 2026-10-21 14:55 | Alex Example |
| OQ-12 | `evidence/GEN/OQ-12/20261022-oq12-revert-prs-and-force-push.json` | `42d65d7ed615a85e7908ecd903e1977b012311a0d5a85ac332f2d5caca3c875f` | 2026-10-22 10:55 | Alex Example |

## 6. Results used by the tool protocols

| Tool | Test protocol | Tests credited from this record | Date credited |
|---|---|---|---|
| Claude Code | ACME-VAL-CLAUDE-05 | OQ-01 to OQ-07, OQ-12 (code-host part) | 2026-10-22 |
| OpenAI Codex | ACME-VAL-CODEX-05 | OQ-01 to OQ-07, OQ-12 (code-host part) | 2026-10-22 |

## 7. Deviation log

| Deviation ID | Test ID | Description (observed vs expected) | Classification | Affected requirement(s) | Root cause | Resolution / CAPA ref | Re-test ref | Closed by / date |
|---|---|---|---|---|---|---|---|---|
| none | - | No deviation in this record | - | - | - | - | - | - |

## 8. Approval

Signed by the people themselves in the eQMS (in an e-signature system validated for 21 CFR Part 11 where FDA requirements apply, and meeting the organisation's eIDAS requirements in the EU); never typed by an AI tool or by another person on someone's behalf. Each signature shows the printed name, the date and time, and the meaning of the signature, and is linked to this record (21 CFR 11.50 and 11.70).

| Step | Role | Name | Signature (eQMS / e-signature) | Date and time (UTC) |
|---|---|---|---|---|
| Prepared | Validation Engineer | Alex Example | [signed in eQMS] | 2026-10-19 08:10 |
| Approved before execution | Head of QA | Sam Sample | [signed in eQMS] | 2026-10-19 15:30 |
| Executed and results recorded | Validation Engineer | Alex Example | [signed in eQMS] | 2026-10-22 11:20 |
| Executed records reviewed | Head of QA | Sam Sample | [signed in eQMS] | 2026-10-23 09:00 |
