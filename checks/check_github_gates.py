#!/usr/bin/env python3
"""Check the server-side review gates of a GitHub repository and the review
record of its merged pull requests.

Evidence for OQ-01 (human gate, positive, historical), OQ-04 (AI / bot / Actions
approval not counted), OQ-05 (agent launcher does not approve), OQ-06 (bypass
prevented or logged), PQ-01 (in-use monitoring) and RV-01 (retrospective review).
Requirements: REQ-01, REQ-02, REQ-03, REQ-04, REQ-05.

For one branch the script reads:

  * classic branch protection    GET /repos/{o}/{r}/branches/{b}/protection
  * effective ruleset rules      GET /repos/{o}/{r}/rules/branches/{b}
  * ruleset details (bypass)     GET /repos/{o}/{r}/rulesets/{id} (or /orgs/{org}/rulesets/{id})
  * ruleset bypass insights      GET /repos/{o}/{r}/rulesets/rule-suites
  * Actions approval setting     GET /repos/{o}/{r}/actions/permissions/workflow
                                 GET /orgs/{org}/actions/permissions/workflow (if accessible)
  * check / log retention         GET /repos/{o}/{r}/actions/permissions/artifact-and-log-retention
  * the last N merged PRs        GET /repos/{o}/{r}/pulls, /pulls/{n}, /pulls/{n}/reviews
  * their required checks        GET /repos/{o}/{r}/commits/{sha}/check-runs, .../status
  * trigger comments (launcher)  GET /repos/{o}/{r}/issues/{n}/comments

and verifies that every merged PR had at least one APPROVED review by a human
(user.type == "User"), other than the PR author and the agent launcher, submitted
before the merge, and on the head commit when last-push approval is required, and
that its required checks concluded successfully ("evidence expired" is reported
separately from "failed": since 2026-10-01 check runs and statuses are deleted
after the Actions retention period). Approvals by bots / apps are flagged. The
agent launcher is the author of a trigger comment (for example "@claude" or
"@codex") on the PR, or is given with --launcher PR=LOGIN (for example from a cloud
task record). Evidence: JSON + Markdown with UTC timestamp, script version, who ran
it on which machine (--operator) and the SHA-256 of the JSON (also written to
<file>.json.sha256).

Authentication: GITHUB_TOKEN (or GH_TOKEN) via urllib; otherwise `gh api`
(GitHub CLI, using its own login). Python 3.9+ standard library only.

Exit codes: 0 pass, 1 fail or inconclusive (or warnings with --fail-on-warn),
2 usage / authentication / network error.
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
import statistics
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SCRIPT_NAME = "check_github_gates.py"
SCRIPT_VERSION = "0.1.0"
EVIDENCE_SCHEMA = "ai-coding-tool-validation-kit/evidence/v1"
API_VERSION = "2022-11-28"  # pinned REST API version, recorded in the evidence
DEFAULT_API_URL = "https://api.github.com"
EXIT_PASS, EXIT_FAIL, EXIT_ERROR = 0, 1, 2

SEVERITY_ORDER = {"fail": 0, "inconclusive": 1, "warn": 2, "info": 3}


class ApiError(Exception):
    """A GitHub API call could not be completed (network, auth, rate limit)."""


# ---------------------------------------------------------------------------
# Transport: urllib with a token, or the GitHub CLI
# ---------------------------------------------------------------------------

class Response:
    def __init__(self, status: int, data: Any, headers: Optional[Dict[str, str]] = None):
        self.status = status
        self.data = data
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def message(self) -> str:
        if isinstance(self.data, dict):
            return str(self.data.get("message", ""))
        return ""


def _decode_json(raw: bytes) -> Any:
    if not raw or not raw.strip():
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return {"message": raw.decode("utf-8", "replace")[:500]}


class UrllibTransport:
    """GitHub REST over urllib with a bearer token."""

    name = "urllib"

    def __init__(self, token: str, api_url: str = DEFAULT_API_URL, timeout: int = 30,
                 opener: Optional[Callable[..., Any]] = None):
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self._open = opener or urllib.request.urlopen

    def request(self, url: str) -> Response:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + self.token,
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "ai-coding-tool-validation-kit/" + SCRIPT_VERSION,
        })
        try:
            with self._open(req, timeout=self.timeout) as resp:
                return Response(resp.status, _decode_json(resp.read()), dict(resp.headers))
        except urllib.error.HTTPError as exc:
            return Response(exc.code, _decode_json(exc.read() or b""), dict(exc.headers or {}))
        except (urllib.error.URLError, OSError) as exc:
            raise ApiError("network error for %s: %s" % (url, exc))


class GhTransport:
    """GitHub REST through `gh api --include` (uses the CLI's own login)."""

    name = "gh"

    def __init__(self, gh: str = "gh", api_url: str = DEFAULT_API_URL, timeout: int = 60,
                 runner: Optional[Callable[..., Any]] = None):
        self.gh = gh
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self._run = runner or subprocess.run
        host = urllib.parse.urlparse(self.api_url).hostname or "api.github.com"
        self.hostname = None if host == "api.github.com" else host

    def _path(self, url: str) -> str:
        if url.startswith(self.api_url):
            return url[len(self.api_url):].lstrip("/")
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        if path.startswith("/api/v3/"):
            path = path[len("/api/v3"):]
        return path.lstrip("/") + ("?" + parsed.query if parsed.query else "")

    def request(self, url: str) -> Response:
        cmd = [self.gh, "api", "--include", "--method", "GET",
               "-H", "Accept: application/vnd.github+json",
               "-H", "X-GitHub-Api-Version: " + API_VERSION]
        if self.hostname:
            cmd += ["--hostname", self.hostname]
        cmd.append(self._path(url))
        try:
            proc = self._run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=self.timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ApiError("gh api failed: %s" % exc)
        return self.parse_include(proc.stdout or b"", proc.stderr or b"", proc.returncode)

    @staticmethod
    def parse_include(out: bytes, err: bytes, returncode: int) -> Response:
        text = out.decode("utf-8", "replace")
        if not text.startswith("HTTP/"):
            raise ApiError("gh api returned no HTTP response (exit %s): %s" % (
                returncode, err.decode("utf-8", "replace").strip()[:300]))
        head, _, body = text.replace("\r\n", "\n").partition("\n\n")
        lines = head.split("\n")
        try:
            status = int(lines[0].split()[1])
        except (IndexError, ValueError):
            raise ApiError("cannot parse gh api status line: %r" % lines[0])
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                key, _, value = line.partition(":")
                headers[key.strip()] = value.strip()
        return Response(status, _decode_json(body.encode("utf-8")), headers)


_LINK_NEXT_RE = re.compile(r'<([^>]+)>\s*;\s*rel="next"')


class GitHubClient:
    def __init__(self, transport: Any, api_url: str = DEFAULT_API_URL):
        self.transport = transport
        self.api_url = api_url.rstrip("/")
        self.calls: List[Dict[str, Any]] = []

    def url(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        url = self.api_url + "/" + path.lstrip("/")
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        return url

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Response:
        return self.get_url(self.url(path, params))

    def get_url(self, url: str) -> Response:
        resp = self.transport.request(url)
        self.calls.append({"url": url[len(self.api_url):] if url.startswith(self.api_url) else url,
                           "status": resp.status})
        if resp.status in (401,):
            raise ApiError("authentication failed (HTTP 401) for %s" % url)
        if resp.status in (403, 429) and "rate limit" in resp.message().lower():
            raise ApiError("GitHub API rate limit reached: %s" % resp.message())
        return resp

    def paginate(self, path: str, params: Optional[Dict[str, Any]] = None, max_pages: int = 10,
                 item_key: Optional[str] = None,
                 stop: Optional[Callable[[List[Any]], bool]] = None) -> Tuple[Response, List[Any]]:
        """Follow Link rel="next" (or page numbers when the header is missing)."""
        params = dict(params or {})
        params.setdefault("per_page", 100)
        items: List[Any] = []
        url = self.url(path, params)
        page = 1
        resp = Response(0, None)
        while url and page <= max_pages:
            resp = self.get_url(url)
            if not resp.ok:
                return resp, items
            chunk = resp.data.get(item_key, []) if (item_key and isinstance(resp.data, dict)) \
                else (resp.data or [])
            if not isinstance(chunk, list):
                break
            items.extend(chunk)
            if stop and stop(items):
                break
            match = _LINK_NEXT_RE.search(resp.headers.get("link", ""))
            if match:
                url = match.group(1)
            elif "link" not in resp.headers and len(chunk) >= int(params["per_page"]):
                params["page"] = page + 1
                url = self.url(path, params)
            else:
                url = None
            page += 1
        return resp, items


def make_client(args: argparse.Namespace) -> GitHubClient:
    api_url = (args.api_url or os.environ.get("GITHUB_API_URL") or DEFAULT_API_URL).rstrip("/")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    mode = args.transport
    if mode == "token" or (mode == "auto" and token):
        if not token:
            raise ApiError("--transport token needs GITHUB_TOKEN or GH_TOKEN")
        return GitHubClient(UrllibTransport(token, api_url), api_url)
    gh = shutil.which("gh")
    if gh:
        return GitHubClient(GhTransport(gh, api_url), api_url)
    raise ApiError("no credentials: set GITHUB_TOKEN (or GH_TOKEN), or install and log in to "
                   "the GitHub CLI (gh)")


# ---------------------------------------------------------------------------
# Evidence helpers
# ---------------------------------------------------------------------------

def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def iso(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(value: Optional[str]) -> Optional[datetime.datetime]:
    if not value:
        return None
    try:
        return datetime.datetime.strptime(value.replace("Z", "+0000")[:24],
                                          "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        try:
            return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-") or "x"


def write_evidence(out_dir: str, base: str, doc: Dict[str, Any],
                   render_md: Callable[[Dict[str, Any], str, str], str]) -> Dict[str, str]:
    """Write <base>.json, <base>.json.sha256 and <base>.md; return the paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    json_path = out / (base + ".json")
    json_path.write_bytes(data)
    sha_path = out / (base + ".json.sha256")
    with open(sha_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("%s  %s\n" % (digest, json_path.name))
    md_path = out / (base + ".md")
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_md(doc, digest, json_path.name))
    return {"json": str(json_path), "sha256": str(sha_path), "markdown": str(md_path),
            "json_sha256": digest}


def machine_id_sha256(runner: Callable[..., Any] = subprocess.run) -> Optional[str]:
    """SHA-256 of the machine identifier (/etc/machine-id, macOS IOPlatformUUID or the
    Windows MachineGuid); the raw identifier is not written to the evidence."""
    raw = None
    for candidate in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            raw = Path(candidate).read_text(encoding="utf-8").strip() or None
        except OSError:
            continue
        if raw:
            break
    if not raw and sys.platform == "darwin":
        try:
            out = runner(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         universal_newlines=True, timeout=10).stdout
            m = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', out or "")
            raw = m.group(1) if m else None
        except (OSError, subprocess.SubprocessError):
            raw = None
    if not raw and os.name == "nt":  # pragma: no cover - Windows only
        try:
            import winreg  # type: ignore
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Cryptography") as key:
                raw = str(winreg.QueryValueEx(key, "MachineGuid")[0])
        except OSError:
            raw = None
    return hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw else None


def executed_by(operator: Optional[str], github_login: Optional[str]) -> Dict[str, Any]:
    """Who ran the script on which machine, and under which GitHub identity."""
    try:
        os_user = getpass.getuser()
    except Exception:  # noqa: BLE001 - getuser raises various errors without a login name
        os_user = None
    try:
        hostname = socket.gethostname()
    except OSError:
        hostname = None
    return {"operator": operator, "os_user": os_user, "hostname": hostname,
            "machine_id_sha256": machine_id_sha256(), "github_login": github_login,
            "tool_login": None}


def md_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


# ---------------------------------------------------------------------------
# Normalisation of the gate configuration
# ---------------------------------------------------------------------------

def _enabled(obj: Any) -> Optional[bool]:
    if isinstance(obj, dict):
        return bool(obj.get("enabled"))
    if isinstance(obj, bool):
        return obj
    return None


def _logins(items: Any, key: str = "login") -> List[str]:
    return [str(i.get(key) or i.get("slug") or i.get("name") or i.get("id"))
            for i in (items or []) if isinstance(i, dict)]


def normalize_classic(prot: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Reduce GET .../branches/{b}/protection to the fields the checks use."""
    if not isinstance(prot, dict):
        return None
    rpr = prot.get("required_pull_request_reviews")
    rsc = prot.get("required_status_checks")
    checks: List[Dict[str, Any]] = []
    if isinstance(rsc, dict):
        for c in rsc.get("checks") or []:
            checks.append({"context": c.get("context"), "app_id": c.get("app_id")})
        known = {c["context"] for c in checks}
        for ctx in rsc.get("contexts") or []:
            if ctx not in known:
                checks.append({"context": ctx, "app_id": None})
    bypass = (rpr or {}).get("bypass_pull_request_allowances") or {}
    return {
        "pull_request_required": isinstance(rpr, dict),
        "required_approving_review_count": int((rpr or {}).get("required_approving_review_count")
                                               or 0),
        "dismiss_stale_reviews": bool((rpr or {}).get("dismiss_stale_reviews")),
        "require_code_owner_reviews": bool((rpr or {}).get("require_code_owner_reviews")),
        "require_last_push_approval": bool((rpr or {}).get("require_last_push_approval")),
        "bypass_pull_request_allowances": {
            "users": _logins(bypass.get("users")),
            "teams": _logins(bypass.get("teams"), "slug"),
            "apps": _logins(bypass.get("apps"), "slug"),
        },
        "enforce_admins": _enabled(prot.get("enforce_admins")),
        "required_status_checks": checks,
        "strict_status_checks": bool((rsc or {}).get("strict")) if isinstance(rsc, dict) else None,
        "allow_force_pushes": _enabled(prot.get("allow_force_pushes")),
        "allow_deletions": _enabled(prot.get("allow_deletions")),
        "required_linear_history": _enabled(prot.get("required_linear_history")),
        "required_signatures": _enabled(prot.get("required_signatures")),
        "lock_branch": _enabled(prot.get("lock_branch")),
    }


def normalize_rules(rules: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Reduce GET .../rules/branches/{b} (effective rules) to what the checks use."""
    out: Dict[str, Any] = {"pull_request": [], "required_status_checks": [], "workflows": [],
                           "non_fast_forward": False, "deletion": False,
                           "copilot_code_review": False, "rule_types": [], "rulesets": []}
    seen = set()
    for rule in rules or []:
        if not isinstance(rule, dict):
            continue
        rtype = rule.get("type")
        params = rule.get("parameters") or {}
        out["rule_types"].append(rtype)
        key = (rule.get("ruleset_id"), rule.get("ruleset_source_type"), rule.get("ruleset_source"))
        if rule.get("ruleset_id") is not None and key not in seen:
            seen.add(key)
            out["rulesets"].append({"id": rule.get("ruleset_id"),
                                    "source_type": rule.get("ruleset_source_type"),
                                    "source": rule.get("ruleset_source")})
        if rtype == "pull_request":
            out["pull_request"].append({
                "ruleset_id": rule.get("ruleset_id"),
                "required_approving_review_count": int(params.get("required_approving_review_count")
                                                       or 0),
                "dismiss_stale_reviews_on_push": bool(params.get("dismiss_stale_reviews_on_push")),
                "require_last_push_approval": bool(params.get("require_last_push_approval")),
                "require_code_owner_review": bool(params.get("require_code_owner_review")),
            })
        elif rtype == "required_status_checks":
            for c in params.get("required_status_checks") or []:
                out["required_status_checks"].append({"context": c.get("context"),
                                                      "integration_id": c.get("integration_id"),
                                                      "ruleset_id": rule.get("ruleset_id")})
        elif rtype == "workflows":
            for w in params.get("workflows") or []:
                out["workflows"].append({"path": w.get("path"), "ref": w.get("ref"),
                                         "sha": w.get("sha"),
                                         "repository_id": w.get("repository_id")})
        elif rtype == "non_fast_forward":
            out["non_fast_forward"] = True
        elif rtype == "deletion":
            out["deletion"] = True
        elif rtype == "copilot_code_review":
            out["copilot_code_review"] = True
    out["rule_types"] = sorted(set(t for t in out["rule_types"] if t))
    return out


def effective_gate(classic: Optional[Dict[str, Any]], rules: Dict[str, Any]) -> Dict[str, Any]:
    counts = [r["required_approving_review_count"] for r in rules["pull_request"]]
    if classic and classic["pull_request_required"]:
        counts.append(classic["required_approving_review_count"])
    return {
        "pull_request_required": bool(rules["pull_request"]) or bool(
            classic and classic["pull_request_required"]),
        "required_approving_review_count": max(counts) if counts else 0,
        "require_last_push_approval": any(r["require_last_push_approval"]
                                          for r in rules["pull_request"]) or bool(
            classic and classic["require_last_push_approval"]),
        "dismiss_stale_reviews": any(r["dismiss_stale_reviews_on_push"]
                                     for r in rules["pull_request"]) or bool(
            classic and classic["dismiss_stale_reviews"]),
        "required_status_checks": len(rules["required_status_checks"]) + len(
            (classic or {}).get("required_status_checks") or []),
        "required_workflows": len(rules["workflows"]),
    }


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

def finding(severity: str, check: str, message: str, requirement: str = "",
            test: str = "") -> Dict[str, str]:
    return {"severity": severity, "check": check, "message": message,
            "requirement": requirement, "test": test}


def evaluate_gate_config(state: Dict[str, Any]) -> List[Dict[str, str]]:
    """Findings on the configuration (protection, rulesets, Actions settings)."""
    f: List[Dict[str, str]] = []
    classic = state.get("classic")
    classic_status = state.get("classic_status")  # ok | not_protected | not_accessible
    rules = state["rules"]
    gate = state["effective"]

    if classic_status == "not_accessible":
        f.append(finding("info", "classic_protection_readable",
                         "Classic branch protection could not be read with this token (it may "
                         "need repository admin rights); only rulesets were evaluated.",
                         "REQ-01"))
    if not state.get("rules_readable", True):
        f.append(finding("inconclusive", "rules_readable",
                         "Effective ruleset rules for the branch could not be read.", "REQ-01"))

    # REQ-01: an approving review is required
    if gate["pull_request_required"] and gate["required_approving_review_count"] >= 1:
        f.append(finding("info", "review_required",
                         "A pull request with at least %d approving review(s) is required."
                         % gate["required_approving_review_count"], "REQ-01", "OQ-01"))
    elif classic_status == "not_accessible" or not state.get("rules_readable", True):
        f.append(finding("inconclusive", "review_required",
                         "No readable rule requires an approving review; classic protection was "
                         "not readable, so the gate could not be confirmed.", "REQ-01", "OQ-02"))
    else:
        f.append(finding("fail", "review_required",
                         "No branch protection rule or ruleset requires at least one approving "
                         "review before merge.", "REQ-01", "OQ-02"))

    # REQ-01: approval on the final commit
    if gate["pull_request_required"]:
        if not gate["require_last_push_approval"] and not gate["dismiss_stale_reviews"]:
            f.append(finding("warn", "final_commit_approval",
                             "Neither 'require last push approval' nor 'dismiss stale reviews' is "
                             "enabled: an approval given on an earlier commit still counts after "
                             "new pushes.", "REQ-01", "OQ-01"))
        elif not gate["require_last_push_approval"]:
            f.append(finding("info", "final_commit_approval",
                             "Stale reviews are dismissed on push; 'require last push approval' "
                             "is off.", "REQ-01"))

    # REQ-04: admin bypass and bypass lists (classic)
    if classic:
        if classic["enforce_admins"] is False:
            f.append(finding("warn", "admin_bypass_classic",
                             "Classic protection does not include administrators ('Do not allow "
                             "bypassing the above settings' is off): admin bypass must be "
                             "prevented, or logged and reviewed.", "REQ-04", "OQ-06"))
        allow = classic["bypass_pull_request_allowances"]
        for kind in ("users", "teams", "apps"):
            if allow.get(kind):
                f.append(finding("warn", "bypass_pull_request_allowances",
                                 "Classic protection lets these %s bypass pull request "
                                 "requirements: %s" % (kind, ", ".join(allow[kind])),
                                 "REQ-04", "OQ-06"))
        if classic["allow_force_pushes"]:
            f.append(finding("warn", "force_push",
                             "Classic protection allows force pushes.", "REQ-04", "OQ-03"))
        if classic["allow_deletions"]:
            f.append(finding("warn", "branch_deletion",
                             "Classic protection allows deleting the branch.", "REQ-04", "OQ-03"))
    if not classic and not rules["non_fast_forward"]:
        f.append(finding("warn", "force_push",
                         "No readable rule blocks force pushes (ruleset 'non_fast_forward').",
                         "REQ-04", "OQ-03"))

    # REQ-04: ruleset bypass actors
    for rs in state.get("rulesets", []):
        name = "%s (id %s)" % (rs.get("name") or "ruleset", rs.get("id"))
        if rs.get("enforcement") not in (None, "active"):
            unknown = rs.get("applies_to_branch") == "unknown"
            f.append(finding("info" if unknown else "warn", "ruleset_enforcement",
                             "Ruleset %s is in '%s' mode and does not enforce its rules%s."
                             % (name, rs.get("enforcement"),
                                " (check whether it targets this branch)" if unknown else ""),
                             "REQ-04"))
        actors = rs.get("bypass_actors")
        if actors is None:
            f.append(finding("info", "ruleset_bypass_visible",
                             "Bypass list of ruleset %s is not visible with this token." % name,
                             "REQ-04", "OQ-06"))
            continue
        for actor in actors:
            desc = "%s %s (mode %s)" % (actor.get("actor_type"), actor.get("actor_id"),
                                        actor.get("bypass_mode", "always"))
            if actor.get("bypass_mode") == "exempt":
                f.append(finding("fail", "ruleset_bypass_exempt",
                                 "Ruleset %s exempts %s: rules are not run for that actor and no "
                                 "bypass audit entry is created." % (name, desc),
                                 "REQ-04", "OQ-06"))
            elif actor.get("actor_type") == "Integration":
                f.append(finding("warn", "ruleset_bypass_integration",
                                 "Ruleset %s lets an app / integration bypass: %s. An AI agent "
                                 "app must not be a bypass actor on QMS branches."
                                 % (name, desc), "REQ-02", "OQ-06"))
            else:
                f.append(finding("warn", "ruleset_bypass_actor",
                                 "Ruleset %s has bypass actor %s: bypasses must be logged and "
                                 "reviewed." % (name, desc), "REQ-04", "OQ-06"))

    bypasses = state.get("bypass_events")
    if bypasses is None:
        f.append(finding("info", "ruleset_bypass_events",
                         "Rule insights (rule-suites with result 'bypass') not accessible; review "
                         "bypasses in the audit log instead.", "REQ-04", "OQ-06"))
    elif bypasses:
        f.append(finding("warn", "ruleset_bypass_events",
                         "%d ruleset bypass(es) on this branch in the last month: each must be "
                         "reviewed and justified." % len(bypasses), "REQ-04", "OQ-06"))

    # REQ-03: required checks
    if gate["required_status_checks"] == 0 and gate["required_workflows"] == 0:
        if classic_status == "not_accessible":
            f.append(finding("inconclusive", "required_checks",
                             "No required status check found in rulesets; classic protection "
                             "was not readable.", "REQ-03", "OQ-07"))
        else:
            f.append(finding("fail", "required_checks",
                             "No required status checks or required workflows are configured.",
                             "REQ-03", "OQ-07"))
    for c in (classic or {}).get("required_status_checks") or []:
        if c.get("app_id") in (None, -1):
            f.append(finding("warn", "status_check_source",
                             "Required check '%s' (classic) is not pinned to an app: any writer "
                             "can set its status." % c.get("context"), "REQ-03", "OQ-07"))
    for c in rules["required_status_checks"]:
        if c.get("integration_id") is None:
            f.append(finding("warn", "status_check_source",
                             "Required check '%s' (ruleset %s) is not pinned to an integration: "
                             "any writer can set its status." % (c.get("context"),
                                                                c.get("ruleset_id")),
                             "REQ-03", "OQ-07"))

    # REQ-02: GitHub Actions approving pull requests
    wf = state.get("workflow_permissions")
    if wf is None:
        f.append(finding("inconclusive", "actions_can_approve",
                         "Repository Actions workflow permissions not readable with this token "
                         "(it may need repository admin rights).", "REQ-02", "OQ-04"))
    else:
        if wf.get("can_approve_pull_request_reviews"):
            f.append(finding("fail", "actions_can_approve",
                             "GitHub Actions can approve pull requests in this repository "
                             "(can_approve_pull_request_reviews = true).", "REQ-02", "OQ-04"))
        else:
            f.append(finding("info", "actions_can_approve",
                             "GitHub Actions cannot approve pull requests in this repository.",
                             "REQ-02", "OQ-04"))
        if wf.get("default_workflow_permissions") == "write":
            f.append(finding("warn", "default_workflow_permissions",
                             "Default GITHUB_TOKEN permission is 'write'; prefer 'read'.",
                             "REQ-02"))
    owf = state.get("org_workflow_permissions")
    if owf is not None and owf.get("can_approve_pull_request_reviews"):
        f.append(finding("warn", "org_actions_can_approve",
                         "The organisation allows GitHub Actions to approve pull requests.",
                         "REQ-02", "OQ-04"))

    # REQ-03 / record retention: checks and statuses are deleted after the retention period
    days = state.get("check_retention_days")
    if days is None:
        f.append(finding("info", "check_retention",
                         "Actions retention of checks, statuses and logs not readable with this "
                         "token; record it from the repository settings.", "REQ-03", "OQ-07"))
    elif state.get("repo_private") and int(days) < 400:
        f.append(finding("warn", "check_retention",
                         "Checks, commit statuses and logs are kept %s days (since 2026-10-01 "
                         "this also deletes required-check evidence on PRs): export check "
                         "evidence on merge, or raise retention (private repositories: up to "
                         "400 days)." % days, "REQ-03", "OQ-07"))
    else:
        f.append(finding("info", "check_retention",
                         "Checks, commit statuses and logs are kept %s days; export check "
                         "evidence on merge." % days, "REQ-03", "OQ-07"))

    # REQ-03 / REQ-09: secret scanning push protection
    pp = state.get("push_protection")
    if pp is None:
        f.append(finding("info", "push_protection",
                         "Secret scanning push protection status not visible with this token.",
                         "REQ-09", "OQ-07"))
    elif pp != "enabled":
        f.append(finding("warn", "push_protection",
                         "Secret scanning push protection is '%s'." % pp, "REQ-09", "OQ-07"))
    return f


# ---------------------------------------------------------------------------
# Pull request review record
# ---------------------------------------------------------------------------

def is_human(user: Optional[Dict[str, Any]], non_human: Optional[set] = None) -> bool:
    if not isinstance(user, dict):
        return False
    login = str(user.get("login") or "")
    if login.lower() in (non_human or set()):
        return False
    return user.get("type") == "User" and not login.endswith("[bot]")


def _hours(a: Optional[datetime.datetime], b: Optional[datetime.datetime]) -> Optional[float]:
    if a is None or b is None:
        return None
    return round((b - a).total_seconds() / 3600.0, 2)


CHECK_OK = {"success", "neutral", "skipped"}
CHECK_FAILED = {"failure", "cancelled", "timed_out", "action_required", "stale", "startup_failure"}


def evaluate_checks(required: List[str], check_runs: Optional[List[Dict[str, Any]]],
                    statuses: Optional[List[Dict[str, Any]]], merged_at: Optional[str],
                    retention_days: Optional[int], now: Optional[datetime.datetime] = None
                    ) -> Dict[str, Any]:
    """Result per required context: success | failed | pending | missing | evidence_expired |
    not_readable.

    A required check passes when it is successful, skipped or neutral. When no record of a
    context exists and the PR was merged longer ago than the retention period, the result
    is evidence_expired (not failed)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    merged = parse_ts(merged_at)
    expired_window = bool(merged and retention_days and
                          (now - merged).days >= int(retention_days))
    results: Dict[str, str] = {}
    for ctx in required:
        runs = [c for c in (check_runs or []) if c.get("name") == ctx]
        sts = [s for s in (statuses or []) if s.get("context") == ctx]
        if runs:
            latest = sorted(runs, key=lambda c: c.get("completed_at") or c.get("started_at")
                            or "")[-1]
            if latest.get("status") != "completed":
                results[ctx] = "pending"
            elif latest.get("conclusion") in CHECK_OK:
                results[ctx] = "success"
            else:
                results[ctx] = "failed"
        elif sts:
            state = sorted(sts, key=lambda s: s.get("updated_at") or s.get("created_at")
                           or "")[-1].get("state")
            results[ctx] = {"success": "success", "pending": "pending"}.get(state, "failed")
        else:
            if check_runs is None and statuses is None:
                results[ctx] = "not_readable"
            else:
                results[ctx] = "evidence_expired" if expired_window else "missing"
    values = set(results.values())
    if not required:
        overall = "no_required_checks"
    elif "failed" in values:
        overall = "failed"
    elif values == {"success"}:
        overall = "passed"
    elif values <= {"success", "evidence_expired"}:
        overall = "evidence_expired"
    else:
        overall = "incomplete"
    return {"required": list(required), "results": results, "overall": overall}


def evaluate_pr(pr: Dict[str, Any], reviews: List[Dict[str, Any]], required_approvals: int,
                require_head: bool, non_human: Optional[set] = None,
                launchers: Optional[set] = None, agent_min_approvals: int = 2,
                checks: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Classify the approvals of one merged PR.

    The latest state-changing review (APPROVED / CHANGES_REQUESTED / DISMISSED)
    of each reviewer submitted before the merge decides; COMMENTED reviews do not
    change it. A qualifying approval is APPROVED, by a human (type User, not a
    [bot] login, not in --non-human), not the PR author, not an agent launcher, before
    merge, and on the head commit when require_head is true.
    """
    non_human = {x.lower() for x in (non_human or set())}
    launchers = {x.lower() for x in (launchers or set())}
    author = (pr.get("user") or {}).get("login")
    author_l = (author or "").lower()
    merged_at = parse_ts(pr.get("merged_at"))
    created_at = parse_ts(pr.get("created_at"))
    head_sha = (pr.get("head") or {}).get("sha")
    latest: Dict[str, Dict[str, Any]] = {}
    non_qualifying: List[Dict[str, Any]] = []
    flags: List[str] = []
    counts = {"APPROVED": 0, "CHANGES_REQUESTED": 0, "COMMENTED": 0, "DISMISSED": 0}

    def rv_info(rv: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
        user = rv.get("user") or {}
        info = {"login": user.get("login"), "type": user.get("type"),
                "state": rv.get("state"), "submitted_at": rv.get("submitted_at"),
                "commit_id": rv.get("commit_id"), "on_head_commit": rv.get("commit_id") == head_sha,
                "author_association": rv.get("author_association")}
        if reason:
            info["reason"] = reason
        return info

    for rv in sorted(reviews, key=lambda r: r.get("submitted_at") or ""):
        state = rv.get("state")
        ts = parse_ts(rv.get("submitted_at"))
        if state == "PENDING" or ts is None:
            continue
        if state in counts:
            counts[state] += 1
        user = rv.get("user") or {}
        login = str(user.get("login") or "")
        if state == "APPROVED" and not is_human(user, non_human):
            flags.append("approval by non-human identity %s (type %s)" % (login, user.get("type")))
        if merged_at is not None and ts > merged_at:
            if state == "APPROVED":
                non_qualifying.append(rv_info(rv, "submitted_after_merge"))
            continue
        if state in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            prev = latest.get(login.lower())
            if prev is not None and prev.get("state") == "APPROVED" and state != "APPROVED":
                non_qualifying.append(rv_info(prev, "superseded_by_" + state.lower()))
            latest[login.lower()] = rv

    qualifying: List[Dict[str, Any]] = []
    for login_l, rv in latest.items():
        if rv.get("state") != "APPROVED":
            continue
        user = rv.get("user") or {}
        if not is_human(user, non_human):
            non_qualifying.append(rv_info(rv, "non_human_identity"))
        elif login_l == author_l:
            non_qualifying.append(rv_info(rv, "pr_author"))
        elif login_l in launchers:
            non_qualifying.append(rv_info(rv, "agent_launcher"))
        elif require_head and rv.get("commit_id") != head_sha:
            non_qualifying.append(rv_info(rv, "not_on_head_commit"))
        else:
            qualifying.append(rv_info(rv))

    status = "pass" if len(qualifying) >= max(1, required_approvals) else "fail"
    if status == "pass" and not require_head and not any(q["on_head_commit"] for q in qualifying):
        flags.append("no qualifying approval on the final (head) commit")
    author_user = pr.get("user") or {}
    agent_authored = bool(author_user) and not is_human(author_user, non_human)
    if agent_authored:
        if not launchers:
            flags.append("PR authored by non-human identity %s: launcher not identified "
                         "(record it with --launcher) - confirm the approver is not the "
                         "person who launched the agent" % author)
        if len(qualifying) < agent_min_approvals:
            flags.append("agent-authored PR with %d qualifying approval(s): the compensating "
                         "control (%d approvals or code-owner approval) is not shown by the "
                         "review record" % (len(qualifying), agent_min_approvals))
    if checks is not None:
        if checks["overall"] == "failed":
            status = "fail"
            non_qualifying.append({"reason": "required_check_failed", "login": None,
                                   "detail": {k: v for k, v in checks["results"].items()
                                              if v == "failed"}})
        elif checks["overall"] == "incomplete":
            flags.append("required check evidence missing or pending: %s" % ", ".join(
                "%s=%s" % (k, v) for k, v in checks["results"].items()
                if v not in ("success", "evidence_expired")))
    merged_by = pr.get("merged_by") or {}
    if merged_by and not is_human(merged_by, non_human):
        flags.append("merged by non-human identity %s (type %s)" % (merged_by.get("login"),
                                                                  merged_by.get("type")))
    first_ok = min((parse_ts(q["submitted_at"]) for q in qualifying), default=None)
    if status == "pass" and flags:
        status = "warn"
    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "url": pr.get("html_url"),
        "author": author,
        "author_type": author_user.get("type") if author_user else None,
        "created_at": pr.get("created_at"),
        "merged_at": pr.get("merged_at"),
        "merged_by": merged_by.get("login") if merged_by else None,
        "merged_by_type": merged_by.get("type") if merged_by else None,
        "head_sha": head_sha,
        "merge_commit_sha": pr.get("merge_commit_sha"),
        "agent_authored": agent_authored,
        "launchers": sorted(launchers),
        "checks": checks,
        "required_approvals": max(1, required_approvals),
        "head_approval_required": require_head,
        "qualifying_approvals": qualifying,
        "non_qualifying_approvals": non_qualifying,
        "review_counts": counts,
        "flags": flags,
        "hours_to_first_qualifying_approval": _hours(created_at, first_ok),
        "hours_open": _hours(created_at, merged_at),
        "status": status,
    }


def summarize_prs(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    def med(values: List[Optional[float]]) -> Optional[float]:
        vals = [v for v in values if v is not None]
        return round(statistics.median(vals), 2) if vals else None
    total = len(results)
    ok = sum(1 for r in results if r["status"] in ("pass", "warn"))
    return {
        "merged_prs_checked": total,
        "with_qualifying_human_approval": ok,
        "without_qualifying_human_approval": total - ok,
        "with_non_human_approval": sum(1 for r in results if any(
            x.startswith("approval by non-human") for x in r["flags"])),
        "merged_by_non_human": sum(1 for r in results if r["merged_by_type"] not in (None, "User")),
        "coverage_percent": round(100.0 * ok / total, 1) if total else None,
        "agent_authored": sum(1 for r in results if r.get("agent_authored")),
        "approved_by_launcher": sum(1 for r in results if any(
            n.get("reason") == "agent_launcher" for n in r["non_qualifying_approvals"])),
        "with_failed_required_check": sum(1 for r in results
                                          if (r.get("checks") or {}).get("overall") == "failed"),
        "with_check_evidence_expired": sum(1 for r in results if (r.get("checks") or {}).get(
            "overall") == "evidence_expired"),
        "with_incomplete_check_evidence": sum(1 for r in results if (r.get("checks") or {}).get(
            "overall") == "incomplete"),
        "median_hours_to_first_qualifying_approval": med(
            [r["hours_to_first_qualifying_approval"] for r in results]),
        "median_hours_open": med([r["hours_open"] for r in results]),
    }


def pr_findings(results: List[Dict[str, Any]], requested: int) -> List[Dict[str, str]]:
    f: List[Dict[str, str]] = []
    for r in results:
        if r["status"] == "fail":
            reasons = sorted({n.get("reason", "") for n in r["non_qualifying_approvals"]}) or \
                ["no approval"]
            f.append(finding("fail", "pr_qualifying_approval",
                             "PR #%s merged without %d qualifying human approval(s) (%s)."
                             % (r["number"], r["required_approvals"], ", ".join(reasons)),
                             "REQ-01", "OQ-01"))
        for flag in r["flags"]:
            bot = "non-human" in flag
            f.append(finding("warn", "pr_flag", "PR #%s: %s." % (r["number"], flag),
                             requirement="REQ-02" if bot else "REQ-01",
                             test="OQ-04" if bot else "OQ-01"))
    expired = [r["number"] for r in results
               if (r.get("checks") or {}).get("overall") == "evidence_expired"]
    if expired:
        f.append(finding("info", "pr_check_evidence_expired",
                         "Required-check evidence expired (retention) for %d PR(s): %s. Treat "
                         "them as defined in the validation plan (section 12)." % (
                             len(expired), ", ".join("#%s" % n for n in expired[:30])),
                         "REQ-03", "OQ-01"))
    if not results and not requested:
        f.append(finding("info", "pr_sample", "Pull request review record not checked (--prs 0).",
                         "REQ-01", "OQ-01"))
    elif not results:
        f.append(finding("inconclusive", "pr_sample", "No merged pull request found to check.",
                         "REQ-01", "OQ-01"))
    elif len(results) < 3:
        f.append(finding("warn", "pr_sample",
                         "Only %d merged PR(s) checked; OQ-01 needs at least 3 per repository."
                         % len(results), "REQ-01", "OQ-01"))
    elif requested and len(results) < requested:
        f.append(finding("info", "pr_sample", "%d merged PR(s) found (%d requested)."
                         % (len(results), requested), "REQ-01", "PQ-01"))
    return f


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def collect(client: GitHubClient, args: argparse.Namespace) -> Dict[str, Any]:
    owner, repo = args.repo.split("/", 1)
    rp = "repos/%s/%s" % (owner, repo)
    errors: List[str] = []
    repo_resp = client.get(rp)
    if not repo_resp.ok:
        raise ApiError("cannot read repository %s (HTTP %s: %s)" % (
            args.repo, repo_resp.status, repo_resp.message()))
    repo_data = repo_resp.data or {}
    branch = args.branch or repo_data.get("default_branch") or "main"
    owner_type = (repo_data.get("owner") or {}).get("type")
    org = args.org or (owner if owner_type == "Organization" else None)
    repo_private = bool(repo_data.get("private")) or repo_data.get("visibility") in (
        "private", "internal")
    sec = repo_data.get("security_and_analysis") or {}
    push_protection = (sec.get("secret_scanning_push_protection") or {}).get("status") \
        if sec else None
    bq = urllib.parse.quote(branch, safe="")

    # classic protection
    prot = client.get("%s/branches/%s/protection" % (rp, bq))
    if prot.ok:
        classic, classic_status = normalize_classic(prot.data), "ok"
    elif prot.status == 404 and "not protected" in prot.message().lower():
        classic, classic_status = None, "not_protected"
    else:
        classic, classic_status = None, "not_accessible"

    # effective rules + ruleset details
    rules_resp, rules_list = client.paginate("%s/rules/branches/%s" % (rp, bq),
                                             max_pages=args.max_pages)
    rules_readable = rules_resp.ok or rules_resp.status == 0
    if not rules_readable:
        errors.append("rules/branches: HTTP %s %s" % (rules_resp.status, rules_resp.message()))
    rules = normalize_rules(rules_list)
    rulesets = []
    for rs in rules["rulesets"]:
        if rs["source_type"] == "Organization" and rs.get("source"):
            path = "orgs/%s/rulesets/%s" % (rs["source"], rs["id"])
        else:
            path = "%s/rulesets/%s" % (rp, rs["id"])
        resp = client.get(path)
        detail = resp.data if resp.ok and isinstance(resp.data, dict) else {}
        rulesets.append({"id": rs["id"], "source_type": rs["source_type"],
                         "source": rs["source"], "name": detail.get("name"),
                         "enforcement": detail.get("enforcement"),
                         "bypass_actors": detail.get("bypass_actors") if resp.ok else None,
                         "readable": resp.ok})
    # non-active branch rulesets (evaluate / disabled) are not in the effective rules
    ls_resp, ls = client.paginate("%s/rulesets" % rp, {"includes_parents": "true"},
                                  max_pages=args.max_pages)
    known = {r["id"] for r in rulesets}
    for item in ls if ls_resp.ok else []:
        if item.get("target") == "branch" and item.get("enforcement") != "active" \
                and item.get("id") not in known:
            rulesets.append({"id": item.get("id"), "source_type": item.get("source_type"),
                             "source": item.get("source"), "name": item.get("name"),
                             "enforcement": item.get("enforcement"), "bypass_actors": [],
                             "readable": True, "applies_to_branch": "unknown"})

    # ruleset bypass insights (last month)
    bypass_events: Optional[List[Dict[str, Any]]] = None
    if not args.no_rule_suites:
        rs_resp, suites = client.paginate("%s/rulesets/rule-suites" % rp,
                                          {"time_period": "month", "rule_suite_result": "bypass"},
                                          max_pages=args.max_pages)
        if rs_resp.ok:
            ref = "refs/heads/" + branch
            bypass_events = [{"id": s.get("id"), "actor_name": s.get("actor_name"),
                              "ref": s.get("ref"), "pushed_at": s.get("pushed_at"),
                              "result": s.get("result"), "after_sha": s.get("after_sha")}
                             for s in suites if s.get("ref") in (ref, branch)]

    # Actions approval permission
    wf = client.get("%s/actions/permissions/workflow" % rp)
    workflow_permissions = wf.data if wf.ok and isinstance(wf.data, dict) else None
    org_workflow_permissions = None
    if org:
        owf = client.get("orgs/%s/actions/permissions/workflow" % org)
        org_workflow_permissions = owf.data if owf.ok and isinstance(owf.data, dict) else None

    # retention of checks, statuses and logs (deleted after the period since 2026-10-01)
    ret = client.get("%s/actions/permissions/artifact-and-log-retention" % rp)
    retention_days = ret.data.get("days") if ret.ok and isinstance(ret.data, dict) else None

    gate = effective_gate(classic, rules)
    state = {"branch": branch, "classic": classic, "classic_status": classic_status,
             "check_retention_days": retention_days, "repo_private": repo_private,
             "rules": rules, "rules_readable": rules_readable, "rulesets": rulesets,
             "effective": gate, "bypass_events": bypass_events,
             "workflow_permissions": workflow_permissions,
             "org": org, "org_workflow_permissions": org_workflow_permissions,
             "push_protection": push_protection, "errors": errors}

    # merged pull requests
    prs: List[Dict[str, Any]] = []
    if args.pr:
        for number in args.pr:
            resp = client.get("%s/pulls/%d" % (rp, number))
            if resp.ok and isinstance(resp.data, dict):
                prs.append(resp.data)
            else:
                errors.append("pulls/%d: HTTP %s" % (number, resp.status))
    elif args.prs > 0:
        def enough(items: List[Any]) -> bool:
            return sum(1 for p in items if p.get("merged_at")) >= args.prs
        pr_resp, listed = client.paginate("%s/pulls" % rp, {
            "state": "closed", "base": branch, "sort": "updated", "direction": "desc"},
            max_pages=args.max_pages, stop=enough)
        if not pr_resp.ok:
            raise ApiError("cannot list pull requests (HTTP %s: %s)" % (
                pr_resp.status, pr_resp.message()))
        merged = [p for p in listed if p.get("merged_at")]
        merged.sort(key=lambda p: p.get("merged_at") or "", reverse=True)
        for p in merged[:args.prs]:
            detail = client.get("%s/pulls/%s" % (rp, p.get("number")))
            prs.append(detail.data if detail.ok and isinstance(detail.data, dict) else p)

    required = max(1, gate["required_approving_review_count"], args.min_approvals or 0)
    if args.require_head_approval == "auto":
        require_head = gate["require_last_push_approval"]
    else:
        require_head = args.require_head_approval == "always"
    required_contexts: List[str] = []
    for c in ((classic or {}).get("required_status_checks") or []) + \
            rules["required_status_checks"]:
        if c.get("context") and c["context"] not in required_contexts:
            required_contexts.append(c["context"])
    results = []
    for pr in prs:
        if not pr.get("merged_at"):
            errors.append("PR #%s is not merged; skipped" % pr.get("number"))
            continue
        number = pr.get("number")
        rv_resp, reviews = client.paginate("%s/pulls/%s/reviews" % (rp, number),
                                           max_pages=args.max_pages)
        if not rv_resp.ok:
            errors.append("reviews of PR #%s: HTTP %s" % (number, rv_resp.status))
        launchers = set(args.launcher.get(int(number), set())) if number is not None else set()
        if not args.no_launcher_scan:
            cm_resp, comments = client.paginate("%s/issues/%s/comments" % (rp, number),
                                                max_pages=args.max_pages)
            merged_ts = parse_ts(pr.get("merged_at"))
            for c in comments if cm_resp.ok else []:
                body = str(c.get("body") or "").lower()
                user = c.get("user") or {}
                ts = parse_ts(c.get("created_at"))
                if is_human(user, set(args.non_human)) and any(m in body for m in args.trigger) \
                        and (merged_ts is None or ts is None or ts <= merged_ts):
                    launchers.add(str(user.get("login")))
        checks = None
        head_sha = (pr.get("head") or {}).get("sha")
        if not args.no_checks and head_sha:
            cr_resp, runs = client.paginate("%s/commits/%s/check-runs" % (rp, head_sha),
                                            max_pages=args.max_pages, item_key="check_runs")
            st_resp = client.get("%s/commits/%s/status" % (rp, head_sha))
            statuses = (st_resp.data or {}).get("statuses") if st_resp.ok and \
                isinstance(st_resp.data, dict) else None
            checks = evaluate_checks(required_contexts, runs if cr_resp.ok else None,
                                     statuses, pr.get("merged_at"), retention_days)
        results.append(evaluate_pr(pr, reviews, required, require_head, set(args.non_human),
                                   launchers, args.agent_pr_min_approvals, checks))
    state["required_contexts"] = required_contexts
    state["pull_requests"] = results
    state["required_approvals_used"] = required
    state["head_approval_required"] = require_head
    return state


def build_report(state: Dict[str, Any], args: argparse.Namespace, started: datetime.datetime,
                 client: GitHubClient) -> Dict[str, Any]:
    findings = evaluate_gate_config(state) + pr_findings(state["pull_requests"],
                                                         len(args.pr) if args.pr else args.prs)
    findings.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 9))
    sev = {s: sum(1 for x in findings if x["severity"] == s) for s in SEVERITY_ORDER}
    if sev["fail"]:
        result = "fail"
    elif sev["inconclusive"]:
        result = "inconclusive"
    else:
        result = "pass"
    return {
        "schema": EVIDENCE_SCHEMA,
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "generated_at_utc": iso(utc_now()),
        "started_at_utc": iso(started),
        "kit_tests": ["OQ-01", "OQ-04", "OQ-05", "OQ-06", "PQ-01", "RV-01"],
        "requirements": ["REQ-01", "REQ-02", "REQ-03", "REQ-04", "REQ-05"],
        "parameters": {
            "repo": args.repo, "branch": state["branch"], "prs_requested": args.prs,
            "specific_prs": args.pr or [], "min_approvals": args.min_approvals,
            "require_head_approval": args.require_head_approval,
            "non_human_logins": sorted(args.non_human), "api_url": client.api_url,
            "api_version": API_VERSION, "transport": client.transport.name,
            "launchers": {str(k): sorted(v) for k, v in sorted(args.launcher.items())},
            "trigger_mentions": list(args.trigger),
            "agent_pr_min_approvals": args.agent_pr_min_approvals,
            "checks_evaluated": not args.no_checks,
        },
        "executed_by": state.get("executed_by"),
        "result": result,
        "severity_counts": sev,
        "findings": findings,
        "gate": {k: state.get(k) for k in ("classic_status", "classic", "rules", "rulesets",
                                             "effective", "bypass_events", "workflow_permissions",
                                             "org", "org_workflow_permissions", "push_protection",
                                             "required_approvals_used", "head_approval_required",
                                             "required_contexts", "check_retention_days")},
        "pull_requests": state["pull_requests"],
        "pr_summary": summarize_prs(state["pull_requests"]),
        "api_calls": client.calls,
        "errors": state["errors"],
    }


def render_markdown(doc: Dict[str, Any], digest: str, json_name: str) -> str:
    p = doc["parameters"]
    s = doc["pr_summary"]
    lines = [
        "# GitHub review gate check: %s (%s)" % (p["repo"], p["branch"]),
        "",
        "| Field | Value |",
        "|---|---|",
        "| Result | **%s** |" % doc["result"].upper(),
        "| Generated (UTC) | %s |" % doc["generated_at_utc"],
        "| Script | %s %s |" % (doc["script"], doc["script_version"]),
        "| Kit tests | %s |" % ", ".join(doc["kit_tests"]),
        "| Requirements | %s |" % ", ".join(doc["requirements"]),
        "| API | %s (X-GitHub-Api-Version %s, transport %s) |" % (
            p["api_url"], p["api_version"], p["transport"]),
        "| Executed by | operator %s; OS user %s; host %s; machine id SHA-256 %s; GitHub "
        "login %s |" % tuple(md_cell(x) for x in (
            (doc.get("executed_by") or {}).get("operator"),
            (doc.get("executed_by") or {}).get("os_user"),
            (doc.get("executed_by") or {}).get("hostname"),
            ((doc.get("executed_by") or {}).get("machine_id_sha256") or "not readable")[:16],
            (doc.get("executed_by") or {}).get("github_login") or "not readable")),
        "| Evidence JSON | `%s` |" % json_name,
        "| SHA-256 of JSON | `%s` |" % digest,
        "",
        "## Findings",
        "",
        "| Severity | Check | Requirement | Test | Message |",
        "|---|---|---|---|---|",
    ]
    for f in doc["findings"]:
        lines.append("| %s | %s | %s | %s | %s |" % (f["severity"], f["check"], f["requirement"],
                                                   f["test"], md_cell(f["message"])))
    e = doc["gate"]["effective"]
    lines += [
        "",
        "## Effective gate",
        "",
        "| Setting | Value |",
        "|---|---|",
        "| Classic protection | %s |" % doc["gate"]["classic_status"],
        "| Pull request required | %s |" % e["pull_request_required"],
        "| Required approving reviews | %s |" % e["required_approving_review_count"],
        "| Require last push approval | %s |" % e["require_last_push_approval"],
        "| Dismiss stale reviews | %s |" % e["dismiss_stale_reviews"],
        "| Required status checks | %s |" % e["required_status_checks"],
        "| Required workflows | %s |" % e["required_workflows"],
        "| Ruleset rule types | %s |" % ", ".join(doc["gate"]["rules"]["rule_types"]),
        "| Actions can approve PRs (repo) | %s |" % (
            (doc["gate"]["workflow_permissions"] or {}).get("can_approve_pull_request_reviews",
                                                            "not readable")),
        "| Actions can approve PRs (org) | %s |" % (
            (doc["gate"]["org_workflow_permissions"] or {}).get(
                "can_approve_pull_request_reviews", "not readable / not an org")),
        "",
        "## Merged pull requests",
        "",
        "Checked: %s; with qualifying human approval: %s; without: %s; coverage: %s%%; "
        "with non-human approval: %s; merged by non-human: %s; median hours to first "
        "qualifying approval: %s." % (
            s["merged_prs_checked"], s["with_qualifying_human_approval"],
            s["without_qualifying_human_approval"], s["coverage_percent"],
            s["with_non_human_approval"], s["merged_by_non_human"],
            s["median_hours_to_first_qualifying_approval"]),
        "",
        "| PR | Author | Merged (UTC) | Merged by | Qualifying approvers | Not counted | "
        "Required checks | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in doc["pull_requests"]:
        lines.append("| #%s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["number"], md_cell(r["author"]), r["merged_at"], md_cell(r["merged_by"]),
            md_cell(", ".join("%s%s" % (q["login"], "" if q["on_head_commit"] else " (older commit)")
                              for q in r["qualifying_approvals"])),
            md_cell(", ".join("%s: %s" % (n.get("login"), n.get("reason"))
                              for n in r["non_qualifying_approvals"])),
            md_cell((r.get("checks") or {}).get("overall", "not evaluated")),
            r["status"]))
    if doc["errors"]:
        lines += ["", "## Errors and skipped items", ""] + ["- " + md_cell(e) for e in doc["errors"]]
    lines += [
        "",
        "## Notes",
        "",
        "- A qualifying approval is an APPROVED review by a user of type `User` (not a `[bot]` "
        "login or a listed non-human login), not the PR author, submitted before the merge, and "
        "on the head commit when last-push approval is required.",
        "- The agent launcher is taken from trigger comments on the PR (%s) and from "
        "--launcher; launchers recorded only outside GitHub (for example a cloud task) must be "
        "given with --launcher. An approval by a launcher is not counted (OQ-05)." % ", ".join(
            "`%s`" % m for m in p.get("trigger_mentions") or []),
        "- Required checks: a check passes when it concluded successfully, skipped or neutral; "
        "'evidence_expired' means the record was deleted by the retention setting, not that "
        "the check failed.",
        "- Whether app or machine-user approvals count toward required reviews must be shown "
        "empirically (OQ-04); this report only flags them.",
        "- This file is evidence produced by a script. Review, conclusion and approval are "
        "recorded by the responsible people in the QMS.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="Check GitHub branch protection, rulesets, the Actions approval setting and "
                    "the review record of merged PRs; write JSON + Markdown evidence "
                    "(OQ-01, OQ-04, OQ-06, PQ-01).",
        epilog="Auth: GITHUB_TOKEN / GH_TOKEN (urllib) or the gh CLI login. Exit codes: 0 pass, "
               "1 fail or inconclusive, 2 usage/auth/network error.")
    ap.add_argument("--repo", required=True, help="OWNER/REPO")
    ap.add_argument("--branch", help="protected branch (default: the repository default branch)")
    ap.add_argument("--prs", type=int, default=20, help="number of most recent merged PRs to "
                    "check (default 20; 0 = configuration only)")
    ap.add_argument("--pr", type=int, action="append", default=[], metavar="NUMBER",
                    help="check this PR instead of the last N (repeatable)")
    ap.add_argument("--min-approvals", type=int, default=None,
                    help="minimum qualifying approvals per PR (default: the configured required "
                         "count, at least 1)")
    ap.add_argument("--require-head-approval", choices=("auto", "always", "never"),
                    default="auto", help="require the qualifying approval on the head commit: "
                    "auto = when last-push approval is configured (default)")
    ap.add_argument("--non-human", action="append", default=[], metavar="LOGIN",
                    help="treat this login as non-human, e.g. a machine user used by an agent "
                         "(repeatable)")
    ap.add_argument("--launcher", action="append", default=[], metavar="PR=LOGIN",
                    help="person who launched the agent for this PR, e.g. from a cloud task "
                         "record; their approval is not counted (repeatable)")
    ap.add_argument("--trigger", action="append", default=None, metavar="TEXT",
                    help="mention that launches an agent in a PR comment (repeatable; default "
                         "@claude, @codex, @copilot)")
    ap.add_argument("--no-launcher-scan", action="store_true",
                    help="do not read PR comments for trigger mentions")
    ap.add_argument("--agent-pr-min-approvals", type=int, default=2,
                    help="qualifying approvals expected on agent-authored PRs (compensating "
                         "control; default 2; fewer is flagged)")
    ap.add_argument("--no-checks", action="store_true",
                    help="do not read check runs and statuses of merged PRs")
    ap.add_argument("--operator", default=os.environ.get("KIT_OPERATOR"), metavar="NAME",
                    help="name of the person running the check, recorded in the evidence "
                         "(required; default $KIT_OPERATOR)")
    ap.add_argument("--org", help="organisation for the org-level Actions setting (default: the "
                    "repository owner when it is an organisation)")
    ap.add_argument("--out", default="evidence", help="evidence directory (default: evidence)")
    ap.add_argument("--api-url", help="API base URL (default: $GITHUB_API_URL or "
                    "https://api.github.com)")
    ap.add_argument("--transport", choices=("auto", "token", "gh"), default="auto",
                    help="auto: token if GITHUB_TOKEN/GH_TOKEN is set, else gh (default)")
    ap.add_argument("--max-pages", type=int, default=10, help="pagination limit per list call")
    ap.add_argument("--no-rule-suites", action="store_true",
                    help="skip the ruleset bypass insights call")
    ap.add_argument("--fail-on-warn", action="store_true", help="exit 1 when warnings exist")
    ap.add_argument("--version", action="version", version="%(prog)s " + SCRIPT_VERSION)
    args = ap.parse_args(argv)
    if not re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", args.repo):
        ap.error("--repo must be OWNER/REPO")
    if args.prs < 0:
        ap.error("--prs must be >= 0")
    args.non_human = {x.lower() for x in args.non_human}
    launchers: Dict[int, set] = {}
    for item in args.launcher:
        m = re.match(r"^#?(\d+)=([A-Za-z0-9-]+(?:\[bot\])?)$", item.strip())
        if not m:
            ap.error("--launcher must be PR=LOGIN, e.g. 42=alice")
        launchers.setdefault(int(m.group(1)), set()).add(m.group(2).lower())
    args.launcher = launchers
    args.trigger = [x.lower() for x in (args.trigger or ["@claude", "@codex", "@copilot"])]
    if not (args.operator or "").strip():
        ap.error("--operator NAME (or $KIT_OPERATOR) is required: the evidence records who ran "
                 "the check")
    return args


def main(argv: Optional[List[str]] = None, client: Optional[GitHubClient] = None) -> int:
    args = parse_args(argv)
    started = utc_now()
    try:
        client = client or make_client(args)
        state = collect(client, args)
        who = client.get("user")
        state["executed_by"] = executed_by(
            args.operator, (who.data or {}).get("login") if who.ok and
            isinstance(who.data, dict) else None)
    except ApiError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_ERROR
    doc = build_report(state, args, started, client)
    base = "github-gates_%s_%s_%s" % (safe_name(args.repo.replace("/", "-")),
                                      safe_name(state["branch"]),
                                      started.strftime("%Y%m%dT%H%M%SZ"))
    paths = write_evidence(args.out, base, doc, render_markdown)
    counts = doc["severity_counts"]
    print("%s: %s (fail %d, inconclusive %d, warn %d) - %d merged PR(s) checked" % (
        args.repo, doc["result"].upper(), counts["fail"], counts["inconclusive"], counts["warn"],
        doc["pr_summary"]["merged_prs_checked"]))
    print("evidence: %s\n          %s\nsha256:   %s" % (paths["json"], paths["markdown"],
                                                       paths["json_sha256"]))
    if doc["result"] != "pass":
        return EXIT_FAIL
    if args.fail_on_warn and counts["warn"]:
        return EXIT_FAIL
    return EXIT_PASS


if __name__ == "__main__":
    sys.exit(main())
