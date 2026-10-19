#!/usr/bin/env python3
"""Minimal dependency / SOUP gate for pull requests (REQ-03; OQ-07 b).

Compares the dependency manifests of a change (git BASE..HEAD) and fails when a
new or changed dependency is not on the approved component list, or, with
--check-registry, when the package does not exist in its public registry (this
also catches hallucinated package names, "slopsquatting").

Supported manifests (direct dependencies only):
  * requirements*.txt (PyPI; one requirement per line, comments and options ignored)
  * package.json (npm; dependencies, devDependencies, optionalDependencies,
    peerDependencies)

Approved list (JSON):
  {"components": [{"ecosystem": "pypi", "name": "requests", "versions": ["*"]},
                  {"ecosystem": "npm", "name": "left-pad", "versions": ["1.3.*"]}]}
"versions" are glob patterns matched against the version or specifier text as it
appears in the manifest (for example "2.32.3", "^1.3.0" or ">=2"); "*" accepts any.

It is a reference gate for direct dependencies: lockfiles, transitive
dependencies and other ecosystems need your own tooling. Run it as a required
check pinned to its app (examples/github-workflow-soup-gate.yml).

Evidence: JSON + Markdown with UTC timestamp, script version and the SHA-256 of
the JSON. Python 3.9+ standard library only; git must be on PATH.
Exit codes: 0 pass, 1 an unapproved or unknown dependency, 2 usage or git error.
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import getpass
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SCRIPT_NAME = "soup_gate.py"
SCRIPT_VERSION = "0.2.0"
EVIDENCE_SCHEMA = "ai-coding-tool-validation-kit/evidence/v1"
EXIT_PASS, EXIT_FAIL, EXIT_ERROR = 0, 1, 2
NPM_SECTIONS = ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")
REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*(.*)$")
REGISTRY_URLS = {"pypi": "https://pypi.org/pypi/%s/json",
                 "npm": "https://registry.npmjs.org/%s"}


class GateError(Exception):
    """Usage, git or input error."""


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def normalize(ecosystem: str, name: str) -> str:
    if ecosystem == "pypi":
        return re.sub(r"[-_.]+", "-", name).lower()
    return name.lower()


def ecosystem_of(path: str) -> Optional[str]:
    base = path.rsplit("/", 1)[-1]
    if base == "package.json":
        return "npm"
    if fnmatch.fnmatch(base, "requirements*.txt"):
        return "pypi"
    return None


def parse_requirements(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.split(" #", 1)[0].strip()
        if not line or line.startswith(("#", "-", "git+", "http:", "https:", "file:")):
            continue
        line = line.split(";", 1)[0].strip()  # environment markers
        m = REQ_NAME_RE.match(line)
        if m:
            spec = m.group(3).strip()
            if spec.startswith("=="):
                spec = spec[2:].strip()
            out[normalize("pypi", m.group(1))] = spec or "*"
    return out


def parse_package_json(text: str) -> Dict[str, str]:
    try:
        data = json.loads(text) if text.strip() else {}
    except ValueError as exc:
        raise GateError("package.json is not valid JSON: %s" % exc)
    out: Dict[str, str] = {}
    for section in NPM_SECTIONS:
        for name, spec in (data.get(section) or {}).items():
            out[normalize("npm", str(name))] = str(spec)
    return out


def parse_manifest(ecosystem: str, text: str) -> Dict[str, str]:
    return parse_package_json(text) if ecosystem == "npm" else parse_requirements(text)


def git(args: List[str], repo: Path, runner: Callable[..., Any] = subprocess.run,
        check: bool = True) -> Tuple[int, str]:
    proc = runner(["git"] + args, cwd=str(repo), stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE, universal_newlines=True, timeout=120)
    if check and proc.returncode != 0:
        raise GateError("git %s failed: %s" % (" ".join(args), (proc.stderr or "").strip()))
    return proc.returncode, proc.stdout or ""


def changed_dependencies(repo: Path, base: str, head: str,
                         runner: Callable[..., Any] = subprocess.run) -> List[Dict[str, Any]]:
    _, names = git(["diff", "--name-only", "%s...%s" % (base, head)], repo, runner)
    changes: List[Dict[str, Any]] = []
    for path in sorted(set(n.strip() for n in names.splitlines() if n.strip())):
        eco = ecosystem_of(path)
        if not eco:
            continue
        rc_old, old = git(["show", "%s:%s" % (base, path)], repo, runner, check=False)
        rc_new, new = git(["show", "%s:%s" % (head, path)], repo, runner, check=False)
        before = parse_manifest(eco, old) if rc_old == 0 else {}
        after = parse_manifest(eco, new) if rc_new == 0 else {}
        for name in sorted(after):
            if name not in before:
                changes.append({"manifest": path, "ecosystem": eco, "name": name,
                                "version": after[name], "change": "added"})
            elif before[name] != after[name]:
                changes.append({"manifest": path, "ecosystem": eco, "name": name,
                                "version": after[name], "previous": before[name],
                                "change": "changed"})
    return changes


def load_approved(path: Path) -> Dict[Tuple[str, str], List[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateError("cannot read the approved component list %s: %s" % (path, exc))
    out: Dict[Tuple[str, str], List[str]] = {}
    for item in data.get("components") or []:
        eco = str(item.get("ecosystem", "")).lower()
        if eco not in REGISTRY_URLS or not item.get("name"):
            raise GateError("approved component needs ecosystem pypi|npm and a name: %r" % item)
        versions = [str(v) for v in (item.get("versions") or ["*"])]
        out.setdefault((eco, normalize(eco, str(item["name"]))), []).extend(versions)
    return out


def registry_status(eco: str, name: str, opener: Callable[..., Any] = urllib.request.urlopen,
                    timeout: int = 15) -> str:
    """exists | not_found | unknown (network or server error: the gate fails closed)."""
    url = REGISTRY_URLS[eco] % urllib.parse.quote(name, safe="@")  # scoped npm: @s%2Fname
    req = urllib.request.Request(url, headers={"User-Agent": "%s/%s" % (SCRIPT_NAME,
                                                                         SCRIPT_VERSION)})
    try:
        with opener(req, timeout=timeout) as resp:
            return "exists" if 200 <= getattr(resp, "status", 200) < 300 else "unknown"
    except urllib.error.HTTPError as exc:
        return "not_found" if exc.code == 404 else "unknown"
    except (urllib.error.URLError, OSError):
        return "unknown"


def evaluate(changes: List[Dict[str, Any]], approved: Dict[Tuple[str, str], List[str]],
             check_registry: bool,
             opener: Callable[..., Any] = urllib.request.urlopen) -> List[Dict[str, Any]]:
    results = []
    for ch in changes:
        patterns = approved.get((ch["ecosystem"], ch["name"]))
        ok_name = patterns is not None
        ok_version = ok_name and any(fnmatch.fnmatchcase(ch["version"], p) for p in patterns)
        reg = registry_status(ch["ecosystem"], ch["name"], opener) if check_registry else None
        problems = []
        if not ok_name:
            problems.append("not on the approved component list")
        elif not ok_version:
            problems.append("version %r not approved (approved: %s)" % (ch["version"],
                                                                       ", ".join(patterns)))
        if reg == "not_found":
            problems.append("package does not exist in the %s registry" % ch["ecosystem"])
        elif reg == "unknown":
            problems.append("registry lookup failed: existence not confirmed")
        results.append(dict(ch, registry=reg, problems=problems,
                            result="fail" if problems else "pass"))
    return results


def executed_by(operator: Optional[str]) -> Dict[str, Any]:
    try:
        os_user = getpass.getuser()
    except Exception:  # noqa: BLE001 - getuser raises various errors without a login name
        os_user = None
    return {"operator": operator or os.environ.get("GITHUB_ACTOR"), "os_user": os_user,
            "hostname": socket.gethostname(), "github_login": os.environ.get("GITHUB_ACTOR"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID")}


def render_markdown(doc: Dict[str, Any], digest: str, json_name: str) -> str:
    lines = ["# Dependency / SOUP gate", "", "| Field | Value |", "|---|---|",
             "| Result | **%s** |" % doc["result"].upper(),
             "| Generated (UTC) | %s |" % doc["generated_at_utc"],
             "| Script | %s %s |" % (doc["script"], doc["script_version"]),
             "| Range | `%s...%s` |" % (doc["parameters"]["base"], doc["parameters"]["head"]),
             "| Registry check | %s |" % doc["parameters"]["check_registry"],
             "| Evidence JSON | `%s` |" % json_name, "| SHA-256 of JSON | `%s` |" % digest, "",
             "| Manifest | Package | Version | Change | Registry | Result | Problems |",
             "|---|---|---|---|---|---|---|"]
    for r in doc["dependencies"]:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["manifest"], r["name"], r["version"].replace("|", "\\|"), r["change"],
            r["registry"] or "-", r["result"], "; ".join(r["problems"]) or "-"))
    if not doc["dependencies"]:
        lines.append("| - | no new or changed direct dependency | | | | pass | |")
    lines += ["", "This file is evidence produced by a script; dispositions are recorded in the "
              "QMS (SOUP procedure).", ""]
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
        description="Fail a change whose new or changed direct dependencies are not on the "
                    "approved component (SOUP) list or do not exist in their registry.",
        epilog="Exit codes: 0 pass, 1 unapproved or unknown dependency, 2 usage / git error.")
    ap.add_argument("--approved", required=True, metavar="JSON",
                    help="approved component list (see the module docstring)")
    ap.add_argument("--base", required=True, help="base revision, e.g. origin/main")
    ap.add_argument("--head", default="HEAD", help="head revision (default HEAD)")
    ap.add_argument("--repo", default=".", help="git working copy (default: current directory)")
    ap.add_argument("--check-registry", action="store_true",
                    help="also confirm that each package exists in PyPI / npm (network)")
    ap.add_argument("--operator", default=os.environ.get("KIT_OPERATOR"), metavar="NAME",
                    help="person running the gate (default $KIT_OPERATOR, or $GITHUB_ACTOR in CI)")
    ap.add_argument("--out", default="evidence", help="evidence directory (default: evidence)")
    ap.add_argument("--version", action="version", version="%(prog)s " + SCRIPT_VERSION)
    return ap.parse_args(argv)


def main(argv: Optional[List[str]] = None, runner: Callable[..., Any] = subprocess.run,
         opener: Callable[..., Any] = urllib.request.urlopen) -> int:
    args = parse_args(argv)
    started = utc_now()
    try:
        approved = load_approved(Path(args.approved))
        changes = changed_dependencies(Path(args.repo), args.base, args.head, runner)
    except GateError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_ERROR
    results = evaluate(changes, approved, args.check_registry, opener)
    doc = {"schema": EVIDENCE_SCHEMA, "script": SCRIPT_NAME, "script_version": SCRIPT_VERSION,
           "generated_at_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "kit_tests": ["OQ-07"], "requirements": ["REQ-03"],
           "parameters": {"base": args.base, "head": args.head,
                          "approved_list": Path(args.approved).name,
                          "approved_list_sha256": hashlib.sha256(
                              Path(args.approved).read_bytes()).hexdigest(),
                          "check_registry": args.check_registry},
           "executed_by": executed_by(args.operator),
           "dependencies": results,
           "result": "fail" if any(r["result"] == "fail" for r in results) else "pass"}
    paths = write_evidence(args.out, "soup-gate_%s" % started.strftime("%Y%m%dT%H%M%SZ"), doc)
    for r in results:
        if r["problems"]:
            print("%s %s (%s): %s" % (r["ecosystem"], r["name"], r["version"],
                                      "; ".join(r["problems"])))
    print("soup gate: %s - %d new or changed dependency(ies); evidence %s (sha256 %s)" % (
        doc["result"].upper(), len(results), paths["json"], paths["json_sha256"]))
    return EXIT_PASS if doc["result"] == "pass" else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
