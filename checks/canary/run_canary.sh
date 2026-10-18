#!/usr/bin/env bash
# run_canary.sh - negative test of the server-side merge gate on GitHub.
#
# Creates a throwaway branch with a deliberate canary change, opens a pull
# request with the GitHub CLI (gh), tries to merge it WITHOUT approval through
# the REST API (PUT /repos/{o}/{r}/pulls/{n}/merge, so the server decides, not
# the client) and records the HTTP status and message (OQ-02; REQ-01). Optional
# attempts: self-approval by the PR author (OQ-05), `gh pr merge --admin`
# (OQ-06), direct push to the protected branch (OQ-03), and custom violation
# content such as a failing test, an unapproved dependency or a test secret
# (OQ-07). For OQ-07 variants the script confirms before the attempt that the PR
# is approved and that the target check concluded with failure; otherwise the
# result is "inconclusive". A repository with a merge queue gives "inconclusive"
# (test the queue instead). Run the plain attempt once with a non-admin identity
# and once with an admin identity: an admin with bypass rights is refused only if
# admins are not exempt. Expected result: every attempt is refused and the
# protected branch HEAD is unchanged.
#
# Evidence: JSON + Markdown (UTC timestamp, script version, SHA-256 of the
# JSON in <file>.json.sha256) plus the raw gh output of every step.
# Clean up later with --cleanup (closes the PR and deletes the branch).
#
# Requirements: bash, gh (logged in with write access), python3.
# Exit codes: 0 every attempt refused, 1 an attempt succeeded (gate failure) or
# the result is inconclusive, 2 usage or setup error.

set -euo pipefail

VERSION="0.1.0"
SCRIPT="run_canary.sh"

usage() {
  cat <<'EOF'
Usage:
  run_canary.sh --repo OWNER/REPO [options]          run the canary
  run_canary.sh --cleanup [--state FILE] [--out DIR] close the canary PR, delete its branch

Options:
  --repo OWNER/REPO        repository to test (required)
  --operator NAME          person running the test, recorded in the evidence
                           (required except for --dry-run and --cleanup;
                           default $KIT_OPERATOR)
  --base BRANCH            protected branch (default: the repository default branch)
  --out DIR                evidence directory (default: evidence)
  --file PATH              path of the canary file in the repository
                           (default: canary/CANARY-<timestamp>.md)
  --content-file LOCAL     local file whose content is committed as the canary
                           (e.g. a failing test, a manifest with an unapproved
                           dependency, a file with the vendor's test secret)
  --label TEXT             short name of the variant, recorded in the evidence
                           (default: merge-without-approval)
  --merge-method METHOD    squash | merge | rebase (default: squash)
  --try-self-approve       also try to approve the PR as its author (OQ-05)
  --try-admin              also try `gh pr merge --admin` (OQ-06). If it succeeds
                           the canary lands on the protected branch: revert it.
  --try-direct-push        also try to commit straight to the protected branch
                           through the contents API (OQ-03). If it succeeds:
                           revert it.
  --expect-push-rejected   the canary content should be rejected at push (secret
                           push protection, OQ-07); a rejected push is a pass
  --wait-for-approval      pause after opening the PR so that another person can
                           approve it (isolates the required-check gate, OQ-07);
                           the attempt is inconclusive unless the PR is APPROVED
  --expect-failing-check NAME
                           the required check that must have concluded with
                           failure before the attempt (OQ-07 a / b); otherwise
                           the result is inconclusive
  --auto-cleanup           close the PR and delete the branch at the end
  --cleanup                clean up a previous run (see --state)
  --state FILE             state file of the run to clean up (default: newest
                           canary_*.state in --out)
  --dry-run                print the gh commands without running them
  --version                print the script version
  -h, --help               show this help
EOF
}

die() { echo "error: $*" >&2; exit 2; }

REPO="" BASE="" OUT="evidence" FILE="" CONTENT_FILE="" LABEL="merge-without-approval"
OPERATOR="${KIT_OPERATOR:-}" EXPECT_CHECK=""
MERGE_METHOD="squash" TRY_SELF=0 TRY_ADMIN=0 TRY_PUSH=0 EXPECT_PUSH_REJECTED=0 WAIT=0
AUTO_CLEANUP=0 CLEANUP=0 STATE="" DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="${2:-}"; shift 2 ;;
    --operator) OPERATOR="${2:-}"; shift 2 ;;
    --expect-failing-check) EXPECT_CHECK="${2:-}"; shift 2 ;;
    --base) BASE="${2:-}"; shift 2 ;;
    --out) OUT="${2:-}"; shift 2 ;;
    --file) FILE="${2:-}"; shift 2 ;;
    --content-file) CONTENT_FILE="${2:-}"; shift 2 ;;
    --label) LABEL="${2:-}"; shift 2 ;;
    --merge-method) MERGE_METHOD="${2:-}"; shift 2 ;;
    --try-self-approve) TRY_SELF=1; shift ;;
    --try-admin) TRY_ADMIN=1; shift ;;
    --try-direct-push) TRY_PUSH=1; shift ;;
    --expect-push-rejected) EXPECT_PUSH_REJECTED=1; shift ;;
    --wait-for-approval) WAIT=1; shift ;;
    --auto-cleanup) AUTO_CLEANUP=1; shift ;;
    --cleanup) CLEANUP=1; shift ;;
    --state) STATE="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --version) echo "$SCRIPT $VERSION"; exit 0 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown option: $1" ;;
  esac
done

case "$MERGE_METHOD" in squash|merge|rebase) ;; *) die "--merge-method must be squash, merge or rebase" ;; esac
command -v python3 >/dev/null 2>&1 || die "python3 is required"
if [ "$DRY_RUN" -eq 0 ]; then
  command -v gh >/dev/null 2>&1 || die "the GitHub CLI (gh) is required"
fi

# ---------------------------------------------------------------------------
# Cleanup mode
# ---------------------------------------------------------------------------
state_get() { grep -E "^$1=" "$2" | head -n 1 | cut -d= -f2-; }

cleanup() {
  local state="$1" repo pr branch log
  repo="$(state_get REPO "$state")"; pr="$(state_get PR "$state")"; branch="$(state_get BRANCH "$state")"
  [ -n "$repo" ] && [ -n "$branch" ] || die "state file $state is incomplete"
  log="${state%.state}.cleanup.txt"
  {
    echo "cleanup at $(date -u +%Y-%m-%dT%H:%M:%SZ) by $SCRIPT $VERSION"
    if [ -n "$pr" ]; then
      echo "\$ gh pr close $pr --repo $repo --delete-branch"
      gh pr close "$pr" --repo "$repo" --delete-branch --comment "Canary closed by $SCRIPT" 2>&1 || true
    fi
    echo "\$ gh api -X DELETE repos/$repo/git/refs/heads/$branch"
    gh api -X DELETE "repos/$repo/git/refs/heads/$branch" 2>&1 || echo "(branch already deleted)"
  } > "$log"
  echo "CLEANED=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$state"
  echo "cleanup done for $repo PR ${pr:-none}, branch $branch (log: $log)"
  if grep -qE '^(MERGED_WITHOUT_APPROVAL|ADMIN_MERGED|DIRECT_PUSHED)=1' "$state"; then
    echo "WARNING: an attempt reached the protected branch during this run; revert it with a" >&2
    echo "         reviewed pull request and record the revert (OQ-12)." >&2
  fi
}

if [ "$CLEANUP" -eq 1 ]; then
  if [ -z "$STATE" ]; then
    PATTERN="canary_*.state"
    [ -n "$REPO" ] && PATTERN="canary_$(echo "$REPO" | tr '/' '-')_*.state"
    # shellcheck disable=SC2086
    STATE="$(ls -1t "$OUT"/$PATTERN 2>/dev/null | head -n 1 || true)"
  fi
  [ -n "$STATE" ] && [ -f "$STATE" ] || die "no state file found (use --state FILE)"
  cleanup "$STATE"
  exit 0
fi

[ -n "$REPO" ] || { usage >&2; die "--repo is required"; }
echo "$REPO" | grep -Eq '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' || die "--repo must be OWNER/REPO"
if [ -n "$CONTENT_FILE" ] && [ ! -f "$CONTENT_FILE" ]; then die "--content-file $CONTENT_FILE not found"; fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BRANCH="canary/$STAMP"
[ -n "$FILE" ] || FILE="canary/CANARY-$STAMP.md"
SAFE_REPO="$(echo "$REPO" | tr '/' '-')"
NAME="canary_${SAFE_REPO}_${STAMP}"

if [ "$DRY_RUN" -eq 1 ]; then
  B="${BASE:-<default-branch>}"
  cat <<EOF
# dry run: nothing is executed
gh api user --jq .login
gh api repos/$REPO --jq .default_branch
gh api repos/$REPO/git/ref/heads/$B --jq .object.sha
gh api -X POST repos/$REPO/git/refs -f ref=refs/heads/$BRANCH -f sha=<base-sha>
gh api -X PUT repos/$REPO/contents/$FILE -f message=... -f content=<base64> -f branch=$BRANCH
gh pr create --repo $REPO --base $B --head $BRANCH --title "[CANARY] ..." --body ...
gh pr view <pr> --repo $REPO --json number,url,state,reviewDecision,mergeStateStatus,headRefOid,baseRefName,statusCheckRollup
gh pr view <pr> --repo $REPO --json isMergeQueueEnabled
gh api repos/$REPO --jq .permissions.admin
gh api -i -X PUT repos/$REPO/pulls/<pr>/merge -f merge_method=$MERGE_METHOD   # expected: refused (HTTP 405 / 409)
EOF
  [ "$TRY_SELF" -eq 1 ] && echo "gh pr review <pr> --repo $REPO --approve          # expected: refused"
  [ "$TRY_ADMIN" -eq 1 ] && echo "gh pr merge <pr> --repo $REPO --$MERGE_METHOD --admin  # expected: refused"
  [ "$TRY_PUSH" -eq 1 ] && echo "gh api -X PUT repos/$REPO/contents/canary/DIRECT-$STAMP.md -f branch=$B ...  # expected: refused"
  echo "gh api repos/$REPO/git/ref/heads/$B --jq .object.sha   # expected: unchanged"
  exit 0
fi

[ -n "$OPERATOR" ] || die "--operator NAME (or \$KIT_OPERATOR) is required: the evidence records who ran the test"

mkdir -p "$OUT"
WORK="$OUT/$NAME"
mkdir -p "$WORK"
ATTEMPTS="$WORK/attempts.tsv"
META="$WORK/meta.env"
: > "$ATTEMPTS"
: > "$META"
meta() { printf '%s=%s\n' "$1" "$2" >> "$META"; }

# run_step NAME EXPECT CMD...   (EXPECT: refused | allowed | info)
# Records the exit code and output; never aborts the script.
run_step() {
  local name="$1" expect="$2" rc; shift 2
  {
    printf '$'; printf ' %q' "$@"; printf '\n'
  } > "$WORK/$name.txt"
  set +e
  "$@" >> "$WORK/$name.txt" 2>&1 < /dev/null
  rc=$?
  set -e
  printf '%s\t%s\t%s\n' "$name" "$expect" "$rc" >> "$ATTEMPTS"
  return 0
}
step_rc() { awk -F '\t' -v n="$1" '$1 == n { rc = $3 } END { print rc }' "$ATTEMPTS"; }
step_out() { tail -n +2 "$WORK/$1.txt"; }

b64() { python3 -c 'import base64,sys; sys.stdout.write(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$1"; }

ACTOR="$(gh api user --jq .login 2>/dev/null || echo unknown)"
ACTOR_IS_ADMIN="$(gh api "repos/$REPO" --jq .permissions.admin 2>/dev/null || echo unknown)"
if [ -z "$BASE" ]; then
  BASE="$(gh api "repos/$REPO" --jq .default_branch)" || die "cannot read repository $REPO"
fi
BASE_SHA_BEFORE="$(gh api "repos/$REPO/git/ref/heads/$BASE" --jq .object.sha)" || die "cannot read branch $BASE"
meta REPO "$REPO"; meta BASE "$BASE"; meta BRANCH "$BRANCH"; meta FILE "$FILE"; meta LABEL "$LABEL"
meta ACTOR "$ACTOR"; meta STAMP "$STAMP"; meta MERGE_METHOD "$MERGE_METHOD"
meta OPERATOR "$OPERATOR"; meta ACTOR_IS_ADMIN "$ACTOR_IS_ADMIN"; meta EXPECT_CHECK "$EXPECT_CHECK"
meta BASE_SHA_BEFORE "$BASE_SHA_BEFORE"; meta VERSION "$VERSION"
meta EXPECT_PUSH_REJECTED "$EXPECT_PUSH_REJECTED"

STATEFILE="$OUT/$NAME.state"
printf 'REPO=%s\nBRANCH=%s\nBASE=%s\n' "$REPO" "$BRANCH" "$BASE" > "$STATEFILE"

# 1. throwaway branch + canary commit (through the API: no local clone is touched)
run_step create_branch allowed gh api -X POST "repos/$REPO/git/refs" -f "ref=refs/heads/$BRANCH" -f "sha=$BASE_SHA_BEFORE"
[ "$(step_rc create_branch)" = "0" ] || die "could not create branch $BRANCH (see $WORK/create_branch.txt)"

CONTENT="$WORK/canary-content"
if [ -n "$CONTENT_FILE" ]; then
  cp "$CONTENT_FILE" "$CONTENT"
else
  cat > "$CONTENT" <<EOF
# CANARY - do not merge

Deliberate unapproved change created by $SCRIPT $VERSION at $STAMP (variant: $LABEL).
It must not reach $BASE without a qualified human approval. Close this pull request.
EOF
fi
EXISTING_SHA="$(gh api "repos/$REPO/contents/$FILE?ref=$BRANCH" --jq .sha 2>/dev/null || true)"
PUT_ARGS=(-f "message=CANARY ($LABEL): deliberate unapproved change, do not merge" -f "content=$(b64 "$CONTENT")" -f "branch=$BRANCH")
if [ -n "$EXISTING_SHA" ] && echo "$EXISTING_SHA" | grep -Eq '^[0-9a-f]{40}$'; then PUT_ARGS+=(-f "sha=$EXISTING_SHA"); fi
if [ "$EXPECT_PUSH_REJECTED" -eq 1 ]; then
  run_step push_canary refused gh api -X PUT "repos/$REPO/contents/$FILE" "${PUT_ARGS[@]}"
else
  run_step push_canary allowed gh api -X PUT "repos/$REPO/contents/$FILE" "${PUT_ARGS[@]}"
  [ "$(step_rc push_canary)" = "0" ] || die "could not commit the canary (see $WORK/push_canary.txt)"
fi

PR=""
if [ "$(step_rc push_canary)" = "0" ]; then
  # 2. pull request
  run_step create_pr allowed gh pr create --repo "$REPO" --base "$BASE" --head "$BRANCH" \
    --title "[CANARY] $LABEL - do not merge" \
    --body "Deliberate canary change created by $SCRIPT $VERSION for a negative test of the merge gate. It must not be merged. It is closed by the cleanup step."
  [ "$(step_rc create_pr)" = "0" ] || die "could not open the pull request (see $WORK/create_pr.txt)"
  PR_URL="$(step_out create_pr | grep -Eo 'https://[^ ]+/pull/[0-9]+' | tail -n 1 || true)"
  PR="$(echo "$PR_URL" | grep -Eo '[0-9]+$' || true)"
  [ -n "$PR" ] || PR="$(gh pr view "$BRANCH" --repo "$REPO" --json number --jq .number)"
  echo "PR=$PR" >> "$STATEFILE"; meta PR "$PR"; meta PR_URL "${PR_URL:-}"
  PR_FIELDS="number,url,state,reviewDecision,mergeStateStatus,headRefOid,baseRefName,statusCheckRollup"
  run_step pr_before info gh pr view "$PR" --repo "$REPO" --json "$PR_FIELDS"
  run_step merge_queue info gh pr view "$PR" --repo "$REPO" --json isMergeQueueEnabled

  if [ "$WAIT" -eq 1 ]; then
    echo "PR opened: ${PR_URL:-#$PR}"
    echo "Ask a qualified reviewer (not $ACTOR) to approve it now, then press Enter to try the merge."
    read -r _ < /dev/tty || true
    meta WAITED_FOR_APPROVAL 1
  fi

  if [ "$WAIT" -eq 1 ] || [ -n "$EXPECT_CHECK" ]; then
    # preconditions of OQ-07 variants: approved, and the target check concluded with failure
    run_step pr_precheck info gh pr view "$PR" --repo "$REPO" --json reviewDecision,statusCheckRollup
  fi

  # 3. the negative tests (merge through the REST API: the server decides)
  run_step merge_without_approval refused gh api -i -X PUT "repos/$REPO/pulls/$PR/merge" -f "merge_method=$MERGE_METHOD"
  [ "$(step_rc merge_without_approval)" = "0" ] && echo "MERGED_WITHOUT_APPROVAL=1" >> "$STATEFILE"
  if [ "$TRY_SELF" -eq 1 ]; then
    run_step self_approval refused gh pr review "$PR" --repo "$REPO" --approve --body "Canary: self-approval attempt by the PR author"
  fi
  if [ "$TRY_ADMIN" -eq 1 ]; then
    run_step admin_merge refused gh pr merge "$PR" --repo "$REPO" "--$MERGE_METHOD" --admin
    [ "$(step_rc admin_merge)" = "0" ] && echo "ADMIN_MERGED=1" >> "$STATEFILE"
  fi
  run_step pr_after info gh pr view "$PR" --repo "$REPO" --json "$PR_FIELDS"
fi
if [ "$TRY_PUSH" -eq 1 ]; then
  DIRECT="$WORK/direct-content"
  printf '# CANARY direct push attempt %s\n' "$STAMP" > "$DIRECT"
  run_step direct_push refused gh api -X PUT "repos/$REPO/contents/canary/DIRECT-$STAMP.md" \
    -f "message=CANARY: direct push attempt to $BASE" -f "content=$(b64 "$DIRECT")" -f "branch=$BASE"
  [ "$(step_rc direct_push)" = "0" ] && echo "DIRECT_PUSHED=1" >> "$STATEFILE"
fi
BASE_SHA_AFTER="$(gh api "repos/$REPO/git/ref/heads/$BASE" --jq .object.sha || echo unknown)"
meta BASE_SHA_AFTER "$BASE_SHA_AFTER"

# 4. evidence (JSON + Markdown + SHA-256) - written by python3 for safe JSON
set +e
python3 - "$WORK" "$OUT" "$NAME" <<'PY'
import datetime, getpass, hashlib, json, os, re, socket, sys
work, out, name = sys.argv[1:4]
meta = {}
for line in open(os.path.join(work, "meta.env"), encoding="utf-8"):
    if "=" in line:
        k, v = line.rstrip("\n").split("=", 1)
        meta[k] = v
attempts = []
for line in open(os.path.join(work, "attempts.tsv"), encoding="utf-8"):
    step, expect, rc = line.rstrip("\n").split("\t")
    path = os.path.join(work, step + ".txt")
    text = open(path, encoding="utf-8", errors="replace").read() if os.path.exists(path) else ""
    rc = int(rc)
    if expect == "refused":
        ok = rc != 0
    elif expect == "allowed":
        ok = rc == 0
    else:
        ok = None
    attempts.append({"step": step, "expected": expect, "exit_code": rc, "as_expected": ok,
                     "output_file": os.path.join(name, step + ".txt"),
                     "output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                     "output_excerpt": text[:1500]})
def pr_json(step):
    p = os.path.join(work, step + ".txt")
    if not os.path.exists(p):
        return None
    body = open(p, encoding="utf-8", errors="replace").read().split("\n", 1)[-1]
    try:
        return json.loads(body)
    except ValueError:
        return None
def http_status(text):
    m = re.search(r"^HTTP/[\d.]+\s+(\d{3})", text, re.M)
    return int(m.group(1)) if m else None
pr_after = pr_json("pr_after") or {}
merged_now = pr_after.get("state") == "MERGED"
inconclusive = []
mq = pr_json("merge_queue") or {}
merge_queue = mq.get("isMergeQueueEnabled") if "isMergeQueueEnabled" in mq else "unknown"
for a in attempts:
    if a["step"] == "merge_without_approval":
        a["http_status"] = http_status(a["output_excerpt"])
        a["pr_merged_after"] = merged_now
        a["as_expected"] = a["exit_code"] != 0 and not merged_now
        if a["exit_code"] == 0 and not merged_now and merge_queue is True:
            inconclusive.append("merge queue enabled: the request was accepted but the PR was not "
                                "merged; test the queue (an unapproved canary must not merge)")
pre = pr_json("pr_precheck")
if pre is not None:
    if meta.get("WAITED_FOR_APPROVAL") == "1" and pre.get("reviewDecision") != "APPROVED":
        inconclusive.append("the PR was not APPROVED before the attempt (reviewDecision %s)"
                            % pre.get("reviewDecision"))
    target = meta.get("EXPECT_CHECK")
    if target:
        found = [c for c in pre.get("statusCheckRollup") or []
                 if (c.get("name") or c.get("context")) == target]
        concluded = [c for c in found if (c.get("conclusion") or c.get("state") or "").upper()
                     in ("FAILURE", "ERROR")]
        if not concluded:
            inconclusive.append("target check %r had not concluded with failure before the "
                                "attempt (%s)" % (target, ", ".join(
                                    "%s/%s" % (c.get("status") or c.get("state"),
                                               c.get("conclusion")) for c in found) or "not found"))
unchanged = meta.get("BASE_SHA_BEFORE") == meta.get("BASE_SHA_AFTER")
negatives = [a for a in attempts if a["expected"] == "refused"]
gate_ok = all(a["as_expected"] for a in negatives) and unchanged and bool(negatives)
def machine_id_sha256():
    for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            raw = open(p, encoding="utf-8").read().strip()
        except OSError:
            continue
        if raw:
            return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return None
try:
    os_user = getpass.getuser()
except Exception:
    os_user = None
executed_by = {"operator": meta.get("OPERATOR"), "os_user": os_user,
               "hostname": socket.gethostname(), "machine_id_sha256": machine_id_sha256(),
               "github_login": meta.get("ACTOR"), "github_login_is_admin": meta.get("ACTOR_IS_ADMIN"),
               "tool_login": None}
if not gate_ok:
    result = "fail"
elif inconclusive:
    result = "inconclusive"
else:
    result = "pass"
tests = ["OQ-02"]
steps = {a["step"] for a in attempts}
if "self_approval" in steps: tests.append("OQ-05")
if "admin_merge" in steps: tests.append("OQ-06")
if "direct_push" in steps: tests.append("OQ-03")
if meta.get("LABEL") != "merge-without-approval" or meta.get("EXPECT_PUSH_REJECTED") == "1":
    tests.append("OQ-07")
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
doc = {
    "schema": "ai-coding-tool-validation-kit/evidence/v1",
    "script": "run_canary.sh", "script_version": meta.get("VERSION"),
    "generated_at_utc": now, "kit_tests": tests,
    "requirements": ["REQ-01", "REQ-03", "REQ-04"],
    "parameters": {k: meta.get(k) for k in ("REPO", "BASE", "BRANCH", "FILE", "LABEL",
                                             "MERGE_METHOD", "EXPECT_PUSH_REJECTED",
                                             "WAITED_FOR_APPROVAL", "EXPECT_CHECK")},
    "actor": meta.get("ACTOR"), "actor_is_admin": meta.get("ACTOR_IS_ADMIN"),
    "executed_by": executed_by, "merge_queue_enabled": merge_queue,
    "inconclusive_reasons": inconclusive,
    "pull_request": meta.get("PR"), "pull_request_url": meta.get("PR_URL"),
    "base_sha_before": meta.get("BASE_SHA_BEFORE"), "base_sha_after": meta.get("BASE_SHA_AFTER"),
    "base_unchanged": unchanged,
    "attempts": attempts,
    "pr_before": pr_json("pr_before"), "pr_after": pr_json("pr_after"),
    "pr_precheck": pre,
    "result": result,
    "acceptance": "Every attempt marked 'refused' is refused by the server (non-zero exit, PR not "
                  "merged) and the protected branch HEAD SHA is unchanged; an OQ-07 attempt whose "
                  "preconditions (approval, target check failed) are not met, or a merge-queue "
                  "repository, is inconclusive.",
}
data = (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
digest = hashlib.sha256(data).hexdigest()
with open(os.path.join(out, name + ".json"), "wb") as fh:
    fh.write(data)
with open(os.path.join(out, name + ".json.sha256"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("%s  %s\n" % (digest, name + ".json"))
md = ["# Merge gate canary: %s (%s)" % (meta.get("REPO"), meta.get("BASE")), "",
      "| Field | Value |", "|---|---|",
      "| Result | **%s** |" % doc["result"].upper(),
      "| Generated (UTC) | %s |" % now,
      "| Script | run_canary.sh %s |" % meta.get("VERSION"),
      "| Kit tests | %s |" % ", ".join(tests),
      "| Variant | %s |" % meta.get("LABEL"),
      "| Actor (gh login, admin?) | %s (%s) |" % (meta.get("ACTOR"), meta.get("ACTOR_IS_ADMIN")),
      "| Executed by | operator %s; OS user %s; host %s |" % (
          meta.get("OPERATOR"), executed_by["os_user"], executed_by["hostname"]),
      "| Merge queue enabled | %s |" % merge_queue,
      "| Inconclusive because | %s |" % ("; ".join(inconclusive) or "-"),
      "| Canary PR | %s |" % (meta.get("PR_URL") or meta.get("PR") or "not opened"),
      "| Protected branch SHA before / after | `%s` / `%s` |" % (meta.get("BASE_SHA_BEFORE"),
                                                             meta.get("BASE_SHA_AFTER")),
      "| Evidence JSON | `%s.json` |" % name,
      "| SHA-256 of JSON | `%s` |" % digest, "",
      "| Step | Expected | Exit code | As expected | Output |", "|---|---|---|---|---|"]
for a in attempts:
    md.append("| %s | %s | %s | %s | `%s` |" % (a["step"], a["expected"], a["exit_code"],
                                              {True: "yes", False: "**NO**", None: "-"}[a["as_expected"]],
                                              a["output_file"]))
md += ["", "Acceptance (fixed before execution): " + doc["acceptance"], "",
       "Close the PR and delete the branch with `run_canary.sh --cleanup`. This file is evidence "
       "produced by a script; the conclusion is recorded by the responsible people in the QMS.", ""]
with open(os.path.join(out, name + ".md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(md))
print("%s: %s - evidence %s.json (sha256 %s)" % (meta.get("REPO"), doc["result"].upper(),
                                               os.path.join(out, name), digest))
sys.exit(0 if result == "pass" else 1)
PY
RESULT=$?
set -e

if [ "$AUTO_CLEANUP" -eq 1 ]; then
  cleanup "$STATEFILE"
else
  echo "Canary left open for inspection. Clean up with: $0 --cleanup --state $STATEFILE"
fi
exit "$RESULT"
