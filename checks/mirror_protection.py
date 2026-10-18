#!/usr/bin/env python3
"""Export the merge-gate configuration of a GitHub repository and, optionally,
apply it to a sandbox repository so that negative gate tests run on a sandbox
"protected exactly like production" (OQ-02 to OQ-07 preconditions; IQ-03 export).

Read from the source repository (REST API, version header 2022-11-28):
  * classic branch protection    GET /repos/{o}/{r}/branches/{b}/protection
  * repository rulesets          GET /repos/{o}/{r}/rulesets, /rulesets/{id}
  * Actions approval setting     GET /repos/{o}/{r}/actions/permissions/workflow
  * check / log retention        GET /repos/{o}/{r}/actions/permissions/artifact-and-log-retention

With --to, the script plans (dry run, default) or applies (--apply):
  * PUT  /repos/{dst}/branches/{b}/protection             (classic protection)
  * POST /repos/{dst}/rulesets or PUT /rulesets/{id}      (repository rulesets, by name)
  * PUT  /repos/{dst}/actions/permissions/workflow        (Actions approval setting)
and then re-reads the target and reports every difference. Organisation rulesets
are not copied: they apply through their own repository conditions, which the
report lists so that you can confirm the sandbox is targeted. Bypass actors and
user / team allowances are copied only with --copy-actors (their ids are
organisation-specific).

Evidence: JSON + Markdown with UTC timestamp, script version, who ran it
(--operator, required) and the SHA-256 of the JSON. Authentication: GITHUB_TOKEN
(or GH_TOKEN), otherwise the GitHub CLI login. Python 3.9+ standard library only.
Exit codes: 0 export done / target matches, 1 target differs after apply, 2 error.
"""

from __future__ import annotations

import argparse
import datetime
import getpass
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SCRIPT_NAME = "mirror_protection.py"
SCRIPT_VERSION = "0.1.0"
EVIDENCE_SCHEMA = "ai-coding-tool-validation-kit/evidence/v1"
API_VERSION = "2022-11-28"
DEFAULT_API_URL = "https://api.github.com"
EXIT_PASS, EXIT_FAIL, EXIT_ERROR = 0, 1, 2
CLASSIC_BOOLEANS = ("required_linear_history", "allow_force_pushes", "allow_deletions",
                    "block_creations", "required_conversation_resolution", "lock_branch",
                    "allow_fork_syncing")
REVIEW_KEYS = ("dismiss_stale_reviews", "require_code_owner_reviews",
               "required_approving_review_count", "require_last_push_approval")


class ApiError(Exception):
    pass


class Transport:
    """GitHub REST with a token (urllib) or through `gh api` (its own login)."""

    def __init__(self, api_url: str = DEFAULT_API_URL, token: Optional[str] = None,
                 gh: Optional[str] = None, runner: Callable[..., Any] = subprocess.run,
                 opener: Callable[..., Any] = urllib.request.urlopen):
        self.api_url = api_url.rstrip("/")
        self.token, self.gh, self.runner, self.opener = token, gh, runner, opener
        self.calls: List[Dict[str, Any]] = []

    def request(self, method: str, path: str, body: Any = None) -> Tuple[int, Any]:
        status, data = (self._urllib if self.token else self._gh)(method, path, body)
        self.calls.append({"method": method, "path": path, "status": status})
        if status == 401:
            raise ApiError("authentication failed (HTTP 401) for %s" % path)
        return status, data

    def _urllib(self, method: str, path: str, body: Any) -> Tuple[int, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.api_url + "/" + path, data=data, method=method, headers={
            "Accept": "application/vnd.github+json", "Authorization": "Bearer " + str(self.token),
            "X-GitHub-Api-Version": API_VERSION, "User-Agent": SCRIPT_NAME + "/" + SCRIPT_VERSION,
            "Content-Type": "application/json"})
        try:
            with self.opener(req, timeout=30) as resp:
                raw = resp.read()
                return resp.status, json.loads(raw.decode("utf-8")) if raw.strip() else None
        except urllib.error.HTTPError as exc:
            raw = exc.read() or b""
            try:
                return exc.code, json.loads(raw.decode("utf-8")) if raw.strip() else None
            except ValueError:
                return exc.code, {"message": raw.decode("utf-8", "replace")[:300]}
        except (urllib.error.URLError, OSError) as exc:
            raise ApiError("network error for %s: %s" % (path, exc))

    def _gh(self, method: str, path: str, body: Any) -> Tuple[int, Any]:
        cmd = [self.gh or "gh", "api", "--include", "--method", method,
               "-H", "Accept: application/vnd.github+json",
               "-H", "X-GitHub-Api-Version: " + API_VERSION, path]
        if body is not None:
            cmd[-1:-1] = ["--input", "-"]
        try:
            proc = self.runner(cmd, input=json.dumps(body).encode("utf-8") if body is not None
                               else None, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=60)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ApiError("gh api failed: %s" % exc)
        text = (proc.stdout or b"").decode("utf-8", "replace").replace("\r\n", "\n")
        if not text.startswith("HTTP/"):
            raise ApiError("gh api returned no HTTP response: %s" %
                           (proc.stderr or b"").decode("utf-8", "replace").strip()[:300])
        head, _, payload = text.partition("\n\n")
        status = int(head.split("\n")[0].split()[1])
        try:
            return status, json.loads(payload) if payload.strip() else None
        except ValueError:
            return status, {"message": payload[:300]}


def make_transport(api_url: str) -> Transport:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return Transport(api_url, token=token)
    gh = shutil.which("gh")
    if gh:
        return Transport(api_url, gh=gh)
    raise ApiError("no credentials: set GITHUB_TOKEN (or GH_TOKEN), or log in to the GitHub CLI")


def _enabled(value: Any) -> Optional[bool]:
    if isinstance(value, dict):
        return bool(value.get("enabled"))
    return value if isinstance(value, bool) else None


def classic_put_body(prot: Dict[str, Any], copy_actors: bool = False) -> Dict[str, Any]:
    """Turn GET .../branches/{b}/protection into the PUT body (four required keys)."""
    rsc = prot.get("required_status_checks")
    status_checks = None
    if isinstance(rsc, dict):
        checks = []
        for c in rsc.get("checks") or []:
            if c.get("context"):
                item = {"context": c["context"]}
                if c.get("app_id") is not None:  # omitted = the app that last set the check
                    item["app_id"] = c["app_id"]
                checks.append(item)
        status_checks = {"strict": bool(rsc.get("strict")), "contexts": [], "checks": checks}
        if not checks:  # contexts is closing down but still required in the body
            status_checks["contexts"] = list(rsc.get("contexts") or [])
    rpr = prot.get("required_pull_request_reviews")
    reviews = None
    if isinstance(rpr, dict):
        reviews = {k: rpr.get(k) for k in REVIEW_KEYS if k in rpr}
        reviews["required_approving_review_count"] = int(
            rpr.get("required_approving_review_count") or 0)
        if copy_actors:
            for key in ("dismissal_restrictions", "bypass_pull_request_allowances"):
                if isinstance(rpr.get(key), dict):
                    reviews[key] = {
                        "users": [u.get("login") for u in rpr[key].get("users") or []],
                        "teams": [t.get("slug") for t in rpr[key].get("teams") or []],
                        "apps": [a.get("slug") for a in rpr[key].get("apps") or []]}
    restrictions = None
    if copy_actors and isinstance(prot.get("restrictions"), dict):
        r = prot["restrictions"]
        restrictions = {"users": [u.get("login") for u in r.get("users") or []],
                        "teams": [t.get("slug") for t in r.get("teams") or []],
                        "apps": [a.get("slug") for a in r.get("apps") or []]}
    body: Dict[str, Any] = {"required_status_checks": status_checks,
                            "enforce_admins": bool(_enabled(prot.get("enforce_admins"))),
                            "required_pull_request_reviews": reviews,
                            "restrictions": restrictions}
    for key in CLASSIC_BOOLEANS:
        value = _enabled(prot.get(key))
        if value is not None:
            body[key] = value
    return body


def ruleset_body(rs: Dict[str, Any], copy_actors: bool = False) -> Dict[str, Any]:
    body = {k: rs.get(k) for k in ("name", "target", "enforcement", "conditions", "rules")}
    body["bypass_actors"] = (rs.get("bypass_actors") or []) if copy_actors else []
    return body


def export(t: Transport, repo: str, branch: Optional[str]) -> Dict[str, Any]:
    status, info = t.request("GET", "repos/%s" % repo)
    if status != 200 or not isinstance(info, dict):
        raise ApiError("cannot read repository %s (HTTP %s)" % (repo, status))
    branch = branch or info.get("default_branch") or "main"
    out: Dict[str, Any] = {"repo": repo, "branch": branch, "private": info.get("private")}
    status, prot = t.request("GET", "repos/%s/branches/%s/protection" % (repo, branch))
    out["classic_protection"] = prot if status == 200 else None
    out["classic_status"] = "ok" if status == 200 else "not_protected" if status == 404 \
        else "not_accessible (HTTP %s)" % status
    status, listed = t.request("GET", "repos/%s/rulesets?includes_parents=true" % repo)
    rulesets, org_rulesets = [], []
    for item in listed if status == 200 and isinstance(listed, list) else []:
        if item.get("source_type") == "Organization":
            org_rulesets.append({k: item.get(k) for k in ("id", "name", "source",
                                                          "enforcement", "target")})
            continue
        s, detail = t.request("GET", "repos/%s/rulesets/%s" % (repo, item.get("id")))
        if s == 200 and isinstance(detail, dict):
            rulesets.append(detail)
    out["rulesets"], out["organization_rulesets"] = rulesets, org_rulesets
    status, wf = t.request("GET", "repos/%s/actions/permissions/workflow" % repo)
    out["workflow_permissions"] = wf if status == 200 else None
    status, ret = t.request("GET", "repos/%s/actions/permissions/artifact-and-log-retention"
                            % repo)
    out["check_and_log_retention"] = ret if status == 200 else None
    return out


def comparable(exp: Dict[str, Any]) -> Dict[str, Any]:
    """The fields that must match between source and target."""
    prot = exp.get("classic_protection")
    return {
        "classic": classic_put_body(prot) if isinstance(prot, dict) else None,
        "rulesets": sorted((json.dumps(ruleset_body(r), sort_keys=True)
                            for r in exp.get("rulesets") or [])),
        "workflow_permissions": {k: (exp.get("workflow_permissions") or {}).get(k) for k in
                                 ("default_workflow_permissions",
                                  "can_approve_pull_request_reviews")},
    }


def diff(a: Dict[str, Any], b: Dict[str, Any]) -> List[str]:
    out = []
    for key in sorted(set(a) | set(b)):
        if a.get(key) != b.get(key):
            out.append("%s differs" % key)
    return out


def plan(src: Dict[str, Any], dst_repo: str, dst_branch: str, existing: List[Dict[str, Any]],
         copy_actors: bool) -> List[Dict[str, Any]]:
    steps = []
    if isinstance(src.get("classic_protection"), dict):
        steps.append({"method": "PUT", "path": "repos/%s/branches/%s/protection"
                      % (dst_repo, dst_branch),
                      "body": classic_put_body(src["classic_protection"], copy_actors)})
    by_name = {r.get("name"): r for r in existing}
    for rs in src.get("rulesets") or []:
        body = ruleset_body(rs, copy_actors)
        if rs.get("name") in by_name:
            steps.append({"method": "PUT", "path": "repos/%s/rulesets/%s"
                          % (dst_repo, by_name[rs["name"]].get("id")), "body": body})
        else:
            steps.append({"method": "POST", "path": "repos/%s/rulesets" % dst_repo, "body": body})
    wf = src.get("workflow_permissions")
    if isinstance(wf, dict):
        steps.append({"method": "PUT", "path": "repos/%s/actions/permissions/workflow" % dst_repo,
                      "body": {"default_workflow_permissions": wf.get("default_workflow_permissions"),
                               "can_approve_pull_request_reviews":
                                   bool(wf.get("can_approve_pull_request_reviews"))}})
    return steps


def executed_by(operator: Optional[str], t: Transport) -> Dict[str, Any]:
    try:
        os_user = getpass.getuser()
    except Exception:  # noqa: BLE001 - getuser raises various errors without a login name
        os_user = None
    try:
        status, me = t.request("GET", "user")
        login = me.get("login") if status == 200 and isinstance(me, dict) else None
    except ApiError:
        login = None
    return {"operator": operator, "os_user": os_user, "hostname": socket.gethostname(),
            "github_login": login}


def render_markdown(doc: Dict[str, Any], digest: str, json_name: str) -> str:
    lines = ["# Merge-gate configuration export%s" % (" and mirror" if doc.get("target") else ""),
             "", "| Field | Value |", "|---|---|",
             "| Result | **%s** |" % doc["result"].upper(),
             "| Generated (UTC) | %s |" % doc["generated_at_utc"],
             "| Script | %s %s |" % (doc["script"], doc["script_version"]),
             "| Executed by | operator %s; OS user %s; host %s; GitHub login %s |" % (
                 doc["executed_by"].get("operator"), doc["executed_by"].get("os_user"),
                 doc["executed_by"].get("hostname"), doc["executed_by"].get("github_login")),
             "| Source | %s (%s) |" % (doc["source"]["repo"], doc["source"]["branch"]),
             "| Target | %s |" % ("%s (%s), %s" % (doc["target"]["repo"], doc["target"]["branch"],
                                                   "applied" if doc["applied"] else "dry run")
                                    if doc.get("target") else "none (export only)"),
             "| Evidence JSON | `%s` |" % json_name, "| SHA-256 of JSON | `%s` |" % digest, ""]
    if doc["source"].get("organization_rulesets"):
        lines += ["Organisation rulesets (not copied; confirm their conditions include the "
                  "target): " + ", ".join("%s (id %s)" % (r.get("name"), r.get("id"))
                                          for r in doc["source"]["organization_rulesets"]), ""]
    if doc.get("steps"):
        lines += ["| Step | Method | Path | HTTP status |", "|---|---|---|---|"]
        for i, s in enumerate(doc["steps"], start=1):
            lines.append("| %d | %s | `%s` | %s |" % (i, s["method"], s["path"],
                                                     s.get("status", "planned")))
        lines.append("")
    if doc.get("differences") is not None:
        lines += ["Differences after apply: %s" % (", ".join(doc["differences"]) or "none"), ""]
    lines += ["This file is evidence produced by a script; the approval of the sandbox set-up is "
              "recorded by the responsible people in the QMS.", ""]
    return "\n".join(lines)


def write_evidence(out_dir: str, base: str, doc: Dict[str, Any]) -> Dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    json_path = out / (base + ".json")
    json_path.write_bytes(data)
    with open(out / (base + ".json.sha256"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("%s  %s\n" % (digest, json_path.name))
    with open(out / (base + ".md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_markdown(doc, digest, json_path.name))
    return {"json": str(json_path), "json_sha256": digest}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="Export branch protection, repository rulesets and the Actions approval "
                    "setting of a GitHub repository; with --to, copy them to a sandbox "
                    "repository (dry run unless --apply) and compare.",
        epilog="Exit codes: 0 done / target matches, 1 target differs after apply, 2 error.")
    ap.add_argument("--from", dest="source", required=True, metavar="OWNER/REPO",
                    help="production repository to export")
    ap.add_argument("--to", dest="target", metavar="OWNER/REPO", help="sandbox repository")
    ap.add_argument("--branch", help="source branch (default: its default branch)")
    ap.add_argument("--target-branch", help="target branch (default: its default branch)")
    ap.add_argument("--apply", action="store_true", help="write to the target (default: plan only)")
    ap.add_argument("--copy-actors", action="store_true",
                    help="also copy bypass actors, dismissal and push allowances")
    ap.add_argument("--operator", default=os.environ.get("KIT_OPERATOR"), metavar="NAME",
                    help="person running the script (required; default $KIT_OPERATOR)")
    ap.add_argument("--out", default="evidence", help="evidence directory (default: evidence)")
    ap.add_argument("--api-url", default=os.environ.get("GITHUB_API_URL") or DEFAULT_API_URL)
    ap.add_argument("--version", action="version", version="%(prog)s " + SCRIPT_VERSION)
    args = ap.parse_args(argv)
    for value in (args.source, args.target):
        if value and not re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", value):
            ap.error("repositories must be OWNER/REPO")
    if not (args.operator or "").strip():
        ap.error("--operator NAME (or $KIT_OPERATOR) is required: the evidence records who ran it")
    return args


def main(argv: Optional[List[str]] = None, transport: Optional[Transport] = None) -> int:
    args = parse_args(argv)
    started = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    try:
        t = transport or make_transport(args.api_url)
        src = export(t, args.source, args.branch)
        doc: Dict[str, Any] = {"schema": EVIDENCE_SCHEMA, "script": SCRIPT_NAME,
                               "script_version": SCRIPT_VERSION,
                               "generated_at_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                               "kit_tests": ["IQ-03", "OQ-02", "OQ-03", "OQ-05", "OQ-06", "OQ-07"],
                               "requirements": ["REQ-01", "REQ-03", "REQ-04"],
                               "executed_by": executed_by(args.operator, t),
                               "source": src, "target": None, "applied": False,
                               "steps": [], "differences": None, "result": "pass"}
        if args.target:
            before = export(t, args.target, args.target_branch)
            doc["target"] = {"repo": args.target, "branch": before["branch"], "before": before}
            steps = plan(src, args.target, before["branch"], before.get("rulesets") or [],
                         args.copy_actors)
            doc["steps"] = steps
            if args.apply:
                for s in steps:
                    s["status"], s["response"] = t.request(s["method"], s["path"], s["body"])
                doc["applied"] = True
                after = export(t, args.target, before["branch"])
                doc["target"]["after"] = after
                doc["differences"] = diff(comparable(src), comparable(after))
                if doc["differences"] or any(not 200 <= int(s["status"]) < 300 for s in steps):
                    doc["result"] = "fail"
            else:
                doc["differences"] = diff(comparable(src), comparable(before))
                doc["result"] = "planned"
    except ApiError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_ERROR
    doc["api_calls"] = t.calls
    paths = write_evidence(args.out, "mirror-protection_%s_%s" % (
        args.source.replace("/", "-"), started.strftime("%Y%m%dT%H%M%SZ")), doc)
    print("%s: %s - evidence %s (sha256 %s)" % (args.source, doc["result"].upper(),
                                               paths["json"], paths["json_sha256"]))
    return EXIT_FAIL if doc["result"] == "fail" else EXIT_PASS


if __name__ == "__main__":
    sys.exit(main())
