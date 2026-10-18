#!/usr/bin/env python3
"""Automated client regression on a candidate tool version (CS-3a in the change
and revalidation document; supports IQ-01, IQ-03, OQ-08 and OQ-09 on a new
client version).

The script runs a fixed list of probes from a JSON probe file that is approved
with the validation plan before use, and compares each outcome with its
expectation. Example probe files: tools/claude-code/client-regression.example.json
and tools/codex/client-regression.example.json. A probe file is the
organisation's own: confirm every expectation once on the validated version and
remove or fix any probe whose behaviour you cannot confirm before approval.

Probe file:
  {"tool": "claude_code", "version": 1,
   "probes": [{"id": "version", "description": "...", "command": ["claude", "--version"],
               "expect": {"exit_code": 0, "stdout_regex": "^{version}"},
               "timeout": 60, "requires_credentials": false}]}

Expectation keys (all given keys must hold): exit_code, exit_nonzero (true),
stdout_regex, stdout_not_regex, output_regex (stdout + stderr), file_absent,
file_present. Placeholders in commands and expectations: {version} (the
candidate version), {home}, {workdir} (a fresh temporary directory per probe),
{python}, {kit} (the kit root), {out}, {operator}, plus --var NAME=VALUE.

Evidence: JSON + Markdown with UTC timestamp, script version, who ran it
(--operator, required unless --dry-run) and the SHA-256 of the JSON. Every probe
records its command, exit code, the start of its output and the result.
Python 3.9+ standard library only.
Exit codes: 0 every probe met its expectation, 1 a probe failed, 2 usage error.
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
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

SCRIPT_NAME = "client_regression.py"
SCRIPT_VERSION = "0.1.0"
EVIDENCE_SCHEMA = "ai-coding-tool-validation-kit/evidence/v1"
KIT_ROOT = Path(__file__).resolve().parent.parent
EXIT_PASS, EXIT_FAIL, EXIT_ERROR = 0, 1, 2
EXPECT_KEYS = ("exit_code", "exit_nonzero", "stdout_regex", "stdout_not_regex", "output_regex",
               "file_absent", "file_present")
PLACEHOLDER_RE = re.compile(r"\{([a-z_][a-z0-9_]*)\}")


class ProbeError(Exception):
    pass


def load_probes(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProbeError("cannot read probe file %s: %s" % (path, exc))
    probes = data.get("probes")
    if not isinstance(probes, list) or not probes:
        raise ProbeError("%s: 'probes' must be a non-empty list" % path)
    seen = set()
    for p in probes:
        if not isinstance(p, dict) or not isinstance(p.get("id"), str) or not p["id"]:
            raise ProbeError("%s: every probe needs an 'id'" % path)
        if p["id"] in seen:
            raise ProbeError("%s: duplicate probe id %s" % (path, p["id"]))
        seen.add(p["id"])
        if not isinstance(p.get("command"), list) or not all(isinstance(x, str)
                                                             for x in p["command"]):
            raise ProbeError("%s: probe %s needs 'command' as a list of strings" % (path, p["id"]))
        expect = p.get("expect")
        if not isinstance(expect, dict) or not expect or set(expect) - set(EXPECT_KEYS):
            raise ProbeError("%s: probe %s needs 'expect' with keys from %s"
                             % (path, p["id"], ", ".join(EXPECT_KEYS)))
    return data


def substitute(value: Any, values: Dict[str, str]) -> Any:
    if isinstance(value, str):
        def one(m: "re.Match[str]") -> str:
            key = m.group(1)
            if key not in values:
                raise ProbeError("unknown placeholder {%s}" % key)
            return values[key]
        return PLACEHOLDER_RE.sub(one, value)
    if isinstance(value, list):
        return [substitute(v, values) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v, values) for k, v in value.items()}
    return value


def evaluate(expect: Dict[str, Any], rc: Optional[int], out: str, err: str) -> List[str]:
    problems = []
    if "exit_code" in expect and rc != expect["exit_code"]:
        problems.append("exit code %s, expected %s" % (rc, expect["exit_code"]))
    if expect.get("exit_nonzero") and rc == 0:
        problems.append("exit code 0, expected a refusal (non-zero)")
    if "stdout_regex" in expect and not re.search(expect["stdout_regex"], out, re.M):
        problems.append("stdout does not match %r" % expect["stdout_regex"])
    if "stdout_not_regex" in expect and re.search(expect["stdout_not_regex"], out, re.M):
        problems.append("stdout matches %r" % expect["stdout_not_regex"])
    if "output_regex" in expect and not re.search(expect["output_regex"], out + err, re.M):
        problems.append("output does not match %r" % expect["output_regex"])
    if "file_absent" in expect and Path(expect["file_absent"]).expanduser().exists():
        problems.append("file %s exists" % expect["file_absent"])
    if "file_present" in expect and not Path(expect["file_present"]).expanduser().exists():
        problems.append("file %s is missing" % expect["file_present"])
    return problems


def run_probe(probe: Dict[str, Any], values: Dict[str, str],
              runner: Callable[..., Any] = subprocess.run) -> Dict[str, Any]:
    workdir = tempfile.mkdtemp(prefix="cs3a-%s-" % re.sub(r"[^A-Za-z0-9_-]", "-", probe["id"]))
    local = dict(values, workdir=workdir)
    try:
        cmd = substitute(probe["command"], local)
        expect = substitute(probe["expect"], local)
        for key in ("file_absent", "file_present"):
            if key in expect:  # a stale probe file from an earlier run must not decide
                target = Path(expect[key]).expanduser()
                if key == "file_absent" and target.is_file():
                    target.unlink()
        started = datetime.datetime.now(datetime.timezone.utc)
        try:
            proc = runner(cmd, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True, timeout=int(probe.get("timeout", 120)),
                          stdin=subprocess.DEVNULL)
            rc, out, err = proc.returncode, proc.stdout or "", proc.stderr or ""
        except FileNotFoundError:
            rc, out, err = None, "", "command not found: %s" % cmd[0]
        except subprocess.TimeoutExpired:
            rc, out, err = None, "", "timed out"
        problems = evaluate(expect, rc, out, err)
        if rc is None and not problems:
            problems.append(err)
        return {"id": probe["id"], "description": probe.get("description"),
                "requires_credentials": bool(probe.get("requires_credentials")),
                "verify": probe.get("verify"), "command": cmd, "expect": expect,
                "started_at_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "exit_code": rc, "stdout_excerpt": out[:1500], "stderr_excerpt": err[:1500],
                "output_sha256": hashlib.sha256((out + "\0" + err).encode("utf-8")).hexdigest(),
                "problems": problems, "result": "fail" if problems else "pass"}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def executed_by(operator: Optional[str]) -> Dict[str, Any]:
    try:
        os_user = getpass.getuser()
    except Exception:  # noqa: BLE001 - getuser raises various errors without a login name
        os_user = None
    return {"operator": operator, "os_user": os_user, "hostname": socket.gethostname()}


def render_markdown(doc: Dict[str, Any], digest: str, json_name: str) -> str:
    lines = ["# Automated client regression (CS-3a): %s %s" % (doc["tool"],
                                                              doc["candidate_version"]),
             "", "| Field | Value |", "|---|---|",
             "| Result | **%s** |" % doc["result"].upper(),
             "| Generated (UTC) | %s |" % doc["generated_at_utc"],
             "| Script | %s %s |" % (doc["script"], doc["script_version"]),
             "| Probe file | `%s` (SHA-256 `%s`) |" % (doc["probe_file"], doc["probe_file_sha256"]),
             "| Executed by | operator %s; OS user %s; host %s |" % (
                 doc["executed_by"].get("operator"), doc["executed_by"].get("os_user"),
                 doc["executed_by"].get("hostname")),
             "| Evidence JSON | `%s` |" % json_name, "| SHA-256 of JSON | `%s` |" % digest, "",
             "| Probe | Exit code | Result | Problems |", "|---|---|---|---|"]
    for p in doc["probes"]:
        lines.append("| %s | %s | %s | %s |" % (p["id"], p["exit_code"], p["result"],
                                                "; ".join(p["problems"]).replace("|", "\\|")
                                                or "-"))
    lines += ["", "A pass shows that the candidate version behaves as the approved probes "
              "expect. Guardrail-relevant release notes still need the full CS-3. The decision "
              "is recorded in the change record by the responsible people.", ""]
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
        description="Run the approved client-regression probes on a candidate tool version "
                    "and write JSON + Markdown evidence (CS-3a).",
        epilog="Exit codes: 0 all probes pass, 1 a probe failed, 2 usage error.")
    ap.add_argument("--probes", required=True, metavar="JSON", help="approved probe file")
    ap.add_argument("--candidate-version", required=True, metavar="VERSION",
                    help="tool version under test, e.g. 2.1.303")
    ap.add_argument("--var", action="append", default=[], metavar="NAME=VALUE",
                    help="extra placeholder value (repeatable)")
    ap.add_argument("--skip-credentials", action="store_true",
                    help="skip probes that need vendor credentials (recorded as skipped)")
    ap.add_argument("--operator", default=os.environ.get("KIT_OPERATOR"), metavar="NAME",
                    help="person running the probes (required unless --dry-run; default "
                         "$KIT_OPERATOR)")
    ap.add_argument("--out", default="evidence", help="evidence directory (default: evidence)")
    ap.add_argument("--dry-run", action="store_true", help="print the probe commands only")
    ap.add_argument("--version", action="version", version="%(prog)s " + SCRIPT_VERSION)
    args = ap.parse_args(argv)
    extra = {}
    for item in args.var:
        if "=" not in item:
            ap.error("--var must be NAME=VALUE")
        k, v = item.split("=", 1)
        extra[k.strip()] = v
    args.extra = extra
    if not args.dry_run and not (args.operator or "").strip():
        ap.error("--operator NAME (or $KIT_OPERATOR) is required: the evidence records who ran it")
    return args


def main(argv: Optional[List[str]] = None, runner: Callable[..., Any] = subprocess.run) -> int:
    args = parse_args(argv)
    try:
        data = load_probes(Path(args.probes))
    except ProbeError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_ERROR
    values = {"version": args.candidate_version, "home": str(Path.home()),
              "python": sys.executable, "kit": str(KIT_ROOT), "out": str(Path(args.out)),
              "operator": args.operator or "", "workdir": "<workdir>"}
    values.update(args.extra)
    if args.dry_run:
        for p in data["probes"]:
            try:
                print("%-24s %s" % (p["id"], " ".join(substitute(p["command"], values))))
            except ProbeError as exc:
                print("error: probe %s: %s" % (p["id"], exc), file=sys.stderr)
                return EXIT_ERROR
        return EXIT_PASS
    started = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    results = []
    try:
        for p in data["probes"]:
            if args.skip_credentials and p.get("requires_credentials"):
                results.append({"id": p["id"], "result": "skipped", "exit_code": None,
                                "problems": ["skipped (--skip-credentials)"]})
                continue
            results.append(run_probe(p, values, runner))
    except ProbeError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_ERROR
    raw = Path(args.probes).read_bytes()
    doc = {"schema": EVIDENCE_SCHEMA, "script": SCRIPT_NAME, "script_version": SCRIPT_VERSION,
           "generated_at_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "kit_tests": ["IQ-01", "IQ-03", "OQ-08", "OQ-09"], "requirements": ["REQ-06", "REQ-07"],
           "tool": data.get("tool"), "candidate_version": args.candidate_version,
           "probe_file": Path(args.probes).name,
           "probe_file_sha256": hashlib.sha256(raw).hexdigest(),
           "executed_by": executed_by(args.operator), "probes": results,
           "result": "fail" if any(r["result"] == "fail" for r in results) else "pass"}
    paths = write_evidence(args.out, "client-regression_%s_%s_%s" % (
        data.get("tool") or "tool", re.sub(r"[^A-Za-z0-9._-]", "-", args.candidate_version),
        started.strftime("%Y%m%dT%H%M%SZ")), doc)
    for r in results:
        print("%-24s %s" % (r["id"], r["result"].upper()))
    print("client regression %s: %s - evidence %s (sha256 %s)" % (
        args.candidate_version, doc["result"].upper(), paths["json"], paths["json_sha256"]))
    return EXIT_PASS if doc["result"] == "pass" else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
