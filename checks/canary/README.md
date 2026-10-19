# Merge gate canary (OQ-02, optional OQ-03, OQ-05, OQ-06, OQ-07)

`run_canary.sh` proves with a **negative test** that an unapproved change can't
reach the protected branch. It works through the GitHub API with the GitHub CLI
(`gh`) and leaves local clones untouched.

1. Reads the HEAD SHA of the protected branch, the authenticated login and
   whether that login is a repository admin.
2. Creates a throwaway branch `canary/<UTC timestamp>` and commits a canary file
   to it (default `canary/CANARY-<timestamp>.md`, or your own content).
3. Opens a pull request titled `[CANARY] ... - do not merge` and records whether
   the repository uses a merge queue.
4. Tries to merge **without approval** through the REST API
   (`PUT /repos/{o}/{r}/pulls/{n}/merge`), so the server itself makes the call.
   Expected: refused. The HTTP status and message are recorded, and the PR state
   is read again afterwards.
5. Optional attempts, each expected to be refused: self-approval by the PR
   author, `gh pr merge --admin`, and a direct commit to the protected branch.
6. Reads the protected branch HEAD again. Expected: unchanged.
7. Writes JSON + Markdown evidence (UTC timestamp, script version, who ran it,
   SHA-256 of the JSON in `<file>.json.sha256`) and the raw output of every `gh`
   call.

The PR stays open for inspection until you clean up.

## Prerequisites

- `gh` logged in (`gh auth login`) as a user with write access, python3, bash.
- Run it against each repository in scope (at least 2 when available), with the
  branch protection or rulesets exactly as in production. If you may not open
  test PRs in production, copy the protection to a sandbox repository with
  `../mirror_protection.py` and attach its comparison to the record.
- Run the plain attempt once with a non-admin identity and once with an admin
  identity. An admin who's exempt from the rules can merge, so a refusal for a
  non-admin says nothing about admins (OQ-06).
- Repositories with a merge queue: the queue can accept the merge request
  without merging it, and the result is `inconclusive`. Test the queue's own
  rules for those.
- Agree the run with the repository owners: the canary PR is visible, may notify
  reviewers and may start CI.

## Usage

```
checks/canary/run_canary.sh --repo OWNER/REPO --operator "<name>" --out evidence/GEN/OQ-02/
checks/canary/run_canary.sh --repo OWNER/REPO --operator "<name>" --try-self-approve --out evidence/GEN/OQ-05/
checks/canary/run_canary.sh --repo OWNER/REPO --operator "<name>" --try-admin --out evidence/GEN/OQ-06/     # admin account
checks/canary/run_canary.sh --repo OWNER/REPO --operator "<name>" --try-direct-push --out evidence/GEN/OQ-03/
checks/canary/run_canary.sh --repo OWNER/REPO --dry-run                                                    # print the gh calls only
checks/canary/run_canary.sh --cleanup --out evidence/GEN/OQ-02/                                            # newest run in --out
checks/canary/run_canary.sh --cleanup --state evidence/GEN/OQ-02/canary_<repo>_<stamp>.state
```

The code-host gates are qualified once for all tools in the shared code-host
gate qualification record, so the evidence goes to `evidence/GEN/<TEST-ID>/`.
`--operator` (or `$KIT_OPERATOR`) is required except for `--dry-run` and
`--cleanup`.

Options: `--base BRANCH` (default: the repository default branch),
`--merge-method squash|merge|rebase` (default squash; use a method your rules
allow, otherwise the refusal has a different cause), `--label TEXT` (variant name
recorded in the evidence), `--auto-cleanup` (close the PR and delete the branch at
the end).

Exit codes: `0` every attempt refused and the protected branch unchanged
(result `pass`); `1` an attempt succeeded (result `fail`: raise a deviation) or
the result is `inconclusive` (repeat the attempt after fixing the precondition);
`2` usage or setup error.

**If an attempt succeeds** (`--try-admin`, `--try-direct-push`, or the plain
merge on an unprotected branch), the canary content is on the protected branch.
Revert it through a reviewed pull request and record the revert (it doubles as
evidence for OQ-12). The cleanup step prints a warning in that case.

## Variants for OQ-07 (required checks block violations)

OQ-07 isolates the required-check gate: a second person approves the canary PR,
and the merge must still be refused because a required check fails.

Use `--wait-for-approval` (the script pauses after opening the PR), your own
content with `--file` / `--content-file`, and `--expect-failing-check NAME` for
the check that must block. Before the attempt the script confirms that the PR is
`APPROVED` and that the named check concluded with failure. If either is
missing, the result is `inconclusive`, because the refusal would have another
cause:

| Variant | How | Expected |
|---|---|---|
| a. failing unit test | `--label failing-test --file tests/test_canary.py --content-file my_failing_test.py --expect-failing-check <test check>` (a test in your framework that always fails) | merge refused by the required test check |
| b. unapproved dependency | `--label unapproved-dependency --file <manifest> --content-file <copy of the manifest with one package that is not on the approved SOUP list> --expect-failing-check <SOUP gate check>`; include a plausible but non-existent package name to cover invented dependencies. The gate is `../soup_gate.py` run as a required check (`../../examples/github-workflow-soup-gate.yml`) | merge refused by the dependency / SOUP check |
| c. committed secret | `--label secret --expect-push-rejected --file canary/secret.txt --content-file <file with the vendor-provided test secret pattern>` | commit rejected by secret scanning push protection (a rejected push is a pass); if it's accepted, the merge must still be refused |

`--file` replaces the file on the canary branch if it already exists. Wait for
the checks to finish before pressing Enter: a merge refused only because checks
are still pending proves nothing for OQ-07. `mergeStateStatus` and
`statusCheckRollup` in the PR JSON show why it was blocked, and the script
records them in the `pr_precheck` step.

Spoofing a required check (OQ-07 step 4) and the agent-driven merge attempt
(OQ-02 step 3) are executed manually, as the test protocol describes.

## Evidence

In `--out`: `canary_<owner-repo>_<stamp>.json`, `.md`, `.json.sha256`, the state
file `.state` used by `--cleanup`, `.cleanup.txt` after cleanup, and a folder with
the raw output of every step (`create_branch.txt`, `push_canary.txt`,
`create_pr.txt`, `pr_before.txt`, `merge_queue.txt`, `merge_without_approval.txt`,
...).

The JSON records the result (`pass`, `fail`, `inconclusive` with reasons), who
ran it (operator, operating-system user, host, gh login and whether it's an
admin) and whether a merge queue is enabled. For every step it records the
expected outcome (`refused`, `allowed`, `info`), the exit code, whether it was as
expected and the SHA-256 of its output.

For the merge attempt it also records the HTTP status and whether the PR was
merged afterwards. Plus the protected branch SHA before and after, and the PR
JSON (`number`, `url`, `state`, `reviewDecision`, `mergeStateStatus`,
`headRefOid`, `baseRefName`, `statusCheckRollup`) before and after the attempts.
