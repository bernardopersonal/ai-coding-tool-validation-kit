#!/usr/bin/env python3
"""Find the AI coding tool footprint of a repository (tool discovery; shared
tool-discovery checklist, periodic review reconciliation; REQ-05, REQ-06, REQ-12).

Scans a working copy for

  * agent configuration and instruction files (.claude/, CLAUDE.md, .mcp.json,
    AGENTS.md, .codex/, .agents/, .cursor/, .github/copilot-instructions.md,
    .github/instructions/, .github/hooks/, GEMINI.md, .gemini/, .aider.conf.yml, ...);
  * CI workflows that use AI actions or agent CLIs, with risky options flagged
    (floating action refs, pull_request_target / workflow_run triggers, bypass or
    "dangerously" flags, non-write users or bots allowed to trigger);
  * AI SDK / agent CLI dependencies in package manifests;
  * AI attribution in recent commit messages (trailers such as Co-Authored-By);
  * whether agent instruction files are covered by CODEOWNERS (approximate);

and, with --org, lists the GitHub App installations of the organisation and
flags AI-related apps (GET /orgs/{org}/installations; needs an organisation
owner token). Text scanning is heuristic: review every hit.

Writes JSON + Markdown evidence with UTC timestamp, script version and the
SHA-256 of the JSON. Python 3.9+ standard library only.

Exit codes: 0 no failing finding, 1 failing finding (risky AI workflow option,
or a detected tool missing from --known-tools), 2 usage / API error.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_github_gates import (ApiError, GitHubClient, make_client,  # noqa: E402
                                write_evidence)

SCRIPT_NAME = "find_ai_footprint.py"
SCRIPT_VERSION = "0.1.0"
EVIDENCE_SCHEMA = "ai-coding-tool-validation-kit/evidence/v1"
EXIT_PASS, EXIT_FAIL, EXIT_ERROR = 0, 1, 2
SEVERITY_ORDER = {"fail": 0, "warn": 1, "info": 2}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".tox", "dist", "build",
             "target", "vendor", ".mypy_cache", ".pytest_cache"}
TOOL_KEYS = ("claude_code", "codex", "copilot", "cursor", "gemini", "aider", "shared", "other")

# (glob relative to repo root, tool, description). '**/' matches any depth.
FILE_PATTERNS: List[Tuple[str, str, str]] = [
    (".claude/**", "claude_code", "Claude Code project settings, hooks, skills or agents"),
    ("**/CLAUDE.md", "claude_code", "Claude Code instruction file"),
    ("**/CLAUDE.local.md", "claude_code", "Claude Code local instruction file"),
    (".mcp.json", "claude_code", "project MCP server configuration"),
    ("REVIEW.md", "claude_code", "Claude Code Review instructions"),
    (".codex/**", "codex", "Codex project configuration, hooks or rules"),
    ("**/AGENTS.override.md", "codex", "Codex instruction override file"),
    (".agents/**", "codex", "agents directory (.agents/)"),
    ("**/AGENTS.md", "shared", "agent instruction file (read by several tools)"),
    (".github/copilot-instructions.md", "copilot", "Copilot repository instructions"),
    (".github/instructions/**", "copilot", "Copilot path-specific instructions"),
    (".github/hooks/*.json", "copilot", "Copilot agent hooks"),
    (".github/skills/**", "copilot", "agent skills"),
    (".cursor/**", "cursor", "Cursor rules, Bugbot or hooks configuration"),
    ("**/GEMINI.md", "gemini", "Gemini instruction file"),
    (".gemini/**", "gemini", "Gemini CLI project settings"),
    (".aider.conf.yml", "aider", "Aider configuration"),
]
INSTRUCTION_NAMES = {"CLAUDE.md", "AGENTS.md", "AGENTS.override.md", "GEMINI.md", "REVIEW.md",
                     "copilot-instructions.md"}

ACTION_TOOLS = {
    "anthropics/claude-code-action": "claude_code",
    "anthropics/claude-code-base-action": "claude_code",
    "openai/codex-action": "codex",
}
AI_WORD_RE = re.compile(r"(?i)(claude|anthropic|openai|codex|copilot|cursor|gemini|aider|"
                        r"chatgpt|\bllm\b|\bai[-_])")
APP_AI_RE = re.compile(r"(?i)(claude|anthropic|openai|codex|chatgpt|copilot|cursor|gemini|devin|"
                       r"\bai\b|\bllm\b|\bagent\b)")
USES_RE = re.compile(r"^\s*-?\s*uses:\s*['\"]?([^'\"\s#]+)")
CLI_PATTERNS = [
    (re.compile(r"\bclaude\s+(?:-p|--print|--bare)\b"), "claude_code", "Claude Code headless run"),
    (re.compile(r"@anthropic-ai/claude-code\b"), "claude_code", "Claude Code CLI install"),
    (re.compile(r"\bcodex\s+exec\b"), "codex", "Codex non-interactive run"),
    (re.compile(r"@openai/codex\b"), "codex", "Codex CLI install"),
    (re.compile(r"\baider\b"), "aider", "Aider invocation"),
]
SECRET_NAMES = {"ANTHROPIC_API_KEY": "claude_code", "CLAUDE_CODE_OAUTH_TOKEN": "claude_code",
                "OPENAI_API_KEY": "codex", "CODEX_API_KEY": "codex",
                "CODEX_ACCESS_TOKEN": "codex"}
# (regex, severity, message)
RISK_PATTERNS = [
    (re.compile(r"--dangerously-skip-permissions"), "fail",
     "uses --dangerously-skip-permissions"),
    (re.compile(r"--dangerously-bypass-approvals-and-sandbox|--yolo\b"), "fail",
     "bypasses Codex approvals and sandbox"),
    (re.compile(r"bypassPermissions"), "fail", "uses the bypassPermissions mode"),
    (re.compile(r"\ballowed_non_write_users\s*:"), "fail",
     "lets users without write access trigger the AI action"),
    (re.compile(r"\bsafety-strategy\s*:\s*['\"]?unsafe"), "fail",
     "runs codex-action with safety-strategy unsafe"),
    (re.compile(r"\ballow-bots\s*:\s*['\"]?true"), "warn", "lets bots trigger the AI action"),
    (re.compile(r"\ballowed_bots\s*:"), "warn", "lets listed bots trigger the AI action"),
    (re.compile(r"\bpermissions\s*:\s*write-all\b"), "warn", "grants write-all permissions"),
]
TRIGGER_RE = re.compile(r"^\s*(pull_request_target|workflow_run)\s*:|"
                        r"^\s*on\s*:\s*\[?[^#\n]*\b(pull_request_target|workflow_run)\b", re.M)
SHA_REF_RE = re.compile(r"^[0-9a-f]{40}$")

DEPENDENCY_PATTERNS = [
    (re.compile(r"@anthropic-ai/[A-Za-z0-9._-]+"), "claude_code"),
    (re.compile(r"@openai/codex(?:-sdk)?\b"), "codex"),
    (re.compile(r"(?im)^\s*[\"']?(anthropic|claude-agent-sdk)\s*([=<>~!\[;\"',]|$)"),
     "claude_code"),
    (re.compile(r"(?im)^\s*[\"']?(openai-codex)\s*([=<>~!\[;\"',]|$)"), "codex"),
    (re.compile(r"(?im)^\s*[\"']?(openai)\s*([=<>~!\[;\"',]|$)"), "other"),
    (re.compile(r"\"(openai)\"\s*:"), "other"),
]
MANIFESTS = ("package.json", "requirements.txt", "requirements-dev.txt", "pyproject.toml",
             "Pipfile", "setup.cfg")

COMMIT_PATTERNS = [
    (re.compile(r"(?im)^co-authored-by:.*<noreply@anthropic\.com>"), "claude_code"),
    (re.compile(r"Generated with \[Claude Code\]"), "claude_code"),
    (re.compile(r"(?im)^claude-session:"), "claude_code"),
    (re.compile(r"(?im)^co-authored-by:.*<noreply@openai\.com>"), "codex"),
    (re.compile(r"(?im)^co-authored-by:.*copilot"), "copilot"),
    (re.compile(r"(?m)^aider: "), "aider"),
]
AUTHOR_PATTERNS = [
    (re.compile(r"(?i)\bcopilot\b"), "copilot"),
    (re.compile(r"\(aider\)"), "aider"),
]


def finding(severity: str, check: str, message: str, requirement: str = "",
            tool: str = "") -> Dict[str, str]:
    return {"severity": severity, "check": check, "message": message,
            "requirement": requirement, "tool": tool}


def glob_to_regex(pattern: str) -> "re.Pattern[str]":
    """Glob with '**' (any depth, including none), '*' and '?' (not crossing '/')."""
    i, out = 0, ""
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile("^" + out + "$")


def walk_files(root: Path, limit: int = 20000) -> List[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            files.append((Path(dirpath) / fn).relative_to(root).as_posix())
            if len(files) >= limit:
                return files
    return files


def scan_files(rel_files: List[str]) -> List[Dict[str, str]]:
    hits = []
    compiled = [(glob_to_regex(p), p, tool, desc) for p, tool, desc in FILE_PATTERNS]
    for rel in rel_files:
        for rx, pattern, tool, desc in compiled:
            if rx.match(rel):
                hits.append({"path": rel, "tool": tool, "pattern": pattern, "description": desc})
                break
    return hits


def scan_workflow(rel: str, text: str) -> Dict[str, Any]:
    tools: set = set()
    actions = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        m = USES_RE.match(line)
        if not m:
            continue
        ref = m.group(1)
        name, _, version = ref.partition("@")
        tool = ACTION_TOOLS.get(name.lower())
        if tool is None and AI_WORD_RE.search(name):
            tool = "other"
        if tool:
            tools.add(tool)
            actions.append({"uses": ref, "tool": tool, "line": lineno,
                            "pinned_to_sha": bool(SHA_REF_RE.match(version))})
    cli = []
    for rx, tool, desc in CLI_PATTERNS:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            cli.append({"tool": tool, "description": desc, "line": line})
            tools.add(tool)
    secrets = sorted({name for name in SECRET_NAMES if re.search(r"\b%s\b" % name, text)})
    for name in secrets:
        tools.add(SECRET_NAMES[name])
    risks = []
    if tools:
        for rx, severity, msg in RISK_PATTERNS:
            for m in rx.finditer(text):
                risks.append({"severity": severity, "message": msg,
                              "line": text.count("\n", 0, m.start()) + 1})
        trig = TRIGGER_RE.search(text)
        if trig:
            risks.append({"severity": "warn", "line": text.count("\n", 0, trig.start()) + 1,
                          "message": "AI workflow runs on %s: never check out untrusted PR code "
                                     "at the workspace root in this context"
                                     % (trig.group(1) or trig.group(2))})
        for a in actions:
            if not a["pinned_to_sha"]:
                risks.append({"severity": "warn", "line": a["line"],
                              "message": "action %s uses a moving ref; pin a tag or commit SHA "
                                         "and record it in the configuration baseline" % a["uses"]})
            if a["uses"].lower().startswith("openai/codex-action") and \
                    not re.search(r"\bcodex-version\s*:", text):
                risks.append({"severity": "warn", "line": a["line"],
                              "message": "codex-action without codex-version installs the "
                                         "latest CLI"})
    return {"path": rel, "tools": sorted(tools), "actions": actions, "cli": cli,
            "secrets_referenced": secrets, "risks": risks}


def scan_dependencies(root: Path, rel_files: List[str]) -> List[Dict[str, str]]:
    hits = []
    for rel in rel_files:
        if Path(rel).name not in MANIFESTS:
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        seen = set()
        for rx, tool in DEPENDENCY_PATTERNS:
            for m in rx.finditer(text):
                name = (m.group(1) if m.groups() else m.group(0)).strip()
                if (name, rel) not in seen:
                    seen.add((name, rel))
                    hits.append({"manifest": rel, "package": name, "tool": tool})
    return hits


def scan_commits(root: Path, limit: int,
                 runner: Callable[..., Any] = subprocess.run) -> Optional[Dict[str, Any]]:
    """Count AI attribution in the last `limit` commits (no names or e-mails stored)."""
    if limit <= 0 or not (root / ".git").exists():
        return None
    try:
        proc = runner(["git", "-C", str(root), "log", "-n", str(limit),
                       "--format=%H%x1f%cI%x1f%an%x1f%B%x1e"],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                      timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": str(exc)}
    if proc.returncode != 0:
        return {"error": (proc.stderr or "").strip()[:200]}
    per_tool: Dict[str, Dict[str, Any]] = {}
    total = 0
    for record in proc.stdout.split("\x1e"):
        record = record.strip("\n")
        if not record.strip():
            continue
        parts = record.split("\x1f")
        if len(parts) < 4:
            continue
        sha, date, author, body = parts[0], parts[1], parts[2], parts[3]
        total += 1
        hits = [tool for rx, tool in COMMIT_PATTERNS if rx.search(body)]
        hits += [tool for rx, tool in AUTHOR_PATTERNS if rx.search(author)]
        for tool in sorted(set(hits)):
            t = per_tool.setdefault(tool, {"commits": 0, "first": date, "last": date,
                                           "examples": []})
            t["commits"] += 1
            t["first"] = min(t["first"], date)
            t["last"] = max(t["last"], date)
            if len(t["examples"]) < 5:
                t["examples"].append(sha[:12])
    return {"commits_scanned": total, "by_tool": per_tool}


def codeowners_patterns(root: Path) -> Optional[List["re.Pattern[str]"]]:
    for rel in (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"):
        p = root / rel
        if p.is_file():
            pats = []
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.split("#", 1)[0].strip()
                if not line or len(line.split()) < 2:
                    continue
                pat = line.split()[0]
                anchored = pat.startswith("/")
                pat = pat.lstrip("/")
                if pat.endswith("/"):
                    pat += "**"
                if not anchored and "/" not in pat.rstrip("*"):
                    pat = "**/" + pat
                pats.append(glob_to_regex(pat))
                if not pat.endswith("**"):
                    pats.append(glob_to_regex(pat + "/**"))
            return pats
    return None


def org_installations(client: GitHubClient, org: str) -> Dict[str, Any]:
    resp, items = client.paginate("orgs/%s/installations" % org, item_key="installations")
    if not resp.ok:
        return {"readable": False, "status": resp.status, "message": resp.message()}
    apps = []
    for inst in items:
        slug = str(inst.get("app_slug") or "")
        perms = inst.get("permissions") or {}
        apps.append({
            "app_slug": slug, "app_id": inst.get("app_id"),
            "repository_selection": inst.get("repository_selection"),
            "permissions": perms, "created_at": inst.get("created_at"),
            "suspended": bool(inst.get("suspended_at")),
            "ai_related": bool(APP_AI_RE.search(slug.replace("-", " ").replace("_", " "))),
            "can_write_code_or_prs": perms.get("contents") == "write" or
            perms.get("pull_requests") == "write",
        })
    return {"readable": True, "installations": apps}


def analyse(root: Path, args: argparse.Namespace, runner: Callable[..., Any] = subprocess.run,
            client: Optional[GitHubClient] = None) -> Dict[str, Any]:
    rel_files = walk_files(root)
    files = scan_files(rel_files)
    workflows = []
    for rel in rel_files:
        if re.match(r"^\.github/workflows/[^/]+\.ya?ml$", rel) or rel == ".gitlab-ci.yml":
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
            wf = scan_workflow(rel, text)
            if wf["tools"]:
                workflows.append(wf)
    deps = scan_dependencies(root, rel_files)
    commits = scan_commits(root, args.git_log, runner)
    findings: List[Dict[str, str]] = []
    detected: Dict[str, List[str]] = {}

    def note(tool: str, source: str) -> None:
        detected.setdefault(tool, [])
        if source not in detected[tool]:
            detected[tool].append(source)

    for h in files:
        note(h["tool"], "files")
    for wf in workflows:
        for t in wf["tools"]:
            note(t, "workflows")
        for r in wf["risks"]:
            findings.append(finding(r["severity"], "workflow_risk", "%s:%s %s" % (
                wf["path"], r["line"], r["message"]), "REQ-02", ",".join(wf["tools"])))
    for d in deps:
        note(d["tool"], "dependencies")
    for tool, info in ((commits or {}).get("by_tool") or {}).items():
        note(tool, "commits")
        findings.append(finding("info", "commit_attribution",
                                "%d of the last %d commits carry %s attribution (%s .. %s)" % (
                                    info["commits"], commits["commits_scanned"], tool,
                                    info["first"], info["last"]), "REQ-10", tool))
    # instruction files covered by CODEOWNERS?
    instr = [h["path"] for h in files if Path(h["path"]).name in INSTRUCTION_NAMES
             or h["path"].startswith((".claude/", ".codex/", ".cursor/", ".github/instructions/",
                                      ".github/hooks/", ".github/skills/", ".agents/"))]
    owners = codeowners_patterns(root)
    uncovered = []
    if instr:
        if owners is None:
            findings.append(finding("warn", "codeowners",
                                    "No CODEOWNERS file: agent instruction and configuration "
                                    "files can change without a designated reviewer.", "REQ-06"))
        else:
            uncovered = [p for p in instr if not any(rx.match(p) for rx in owners)]
            if uncovered:
                findings.append(finding("warn", "codeowners",
                                        "%d agent instruction/configuration file(s) not covered "
                                        "by CODEOWNERS (approximate match): %s" % (
                                            len(uncovered), ", ".join(uncovered[:10])), "REQ-06"))
    org = None
    if args.org:
        if client is None:
            client = make_client(args)
        org = org_installations(client, args.org)
        if not org["readable"]:
            findings.append(finding("info", "org_installations",
                                    "GitHub App installations of %s not readable (HTTP %s); an "
                                    "organisation owner token is needed." % (args.org,
                                                                            org["status"]),
                                    "REQ-05"))
        else:
            for app in org["installations"]:
                if app["ai_related"]:
                    note("other" if not app["app_slug"] else _app_tool(app["app_slug"]),
                         "org_apps")
                    findings.append(finding("warn" if app["can_write_code_or_prs"] else "info",
                                            "org_ai_app",
                                            "AI-related GitHub App installed: %s (repositories: "
                                            "%s; write to contents/PRs: %s)" % (
                                                app["app_slug"], app["repository_selection"],
                                                app["can_write_code_or_prs"]), "REQ-05"))
    known = set(args.known_tools or [])
    if args.known_tools is not None:
        for tool in sorted(detected):
            if tool not in known and tool != "shared":
                findings.append(finding("fail", "inventory",
                                        "AI tool footprint '%s' (%s) is not in the validated "
                                        "inventory (--known-tools)." % (
                                            tool, ", ".join(detected[tool])), "REQ-12", tool))
    if not detected:
        findings.append(finding("info", "footprint", "No AI tool footprint found.", ""))
    findings.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 9))
    return {"files": files, "workflows": workflows, "dependencies": deps, "commits": commits,
            "codeowners_found": owners is not None, "instruction_files_without_owner": uncovered,
            "org": org, "detected_tools": {k: detected[k] for k in sorted(detected)},
            "findings": findings}


def _app_tool(slug: str) -> str:
    s = slug.lower()
    for word, tool in (("claude", "claude_code"), ("anthropic", "claude_code"),
                       ("codex", "codex"), ("openai", "codex"), ("chatgpt", "codex"),
                       ("copilot", "copilot"), ("cursor", "cursor"), ("gemini", "gemini")):
        if word in s:
            return tool
    return "other"


def render_markdown(doc: Dict[str, Any], digest: str, json_name: str) -> str:
    r = doc["report"]
    lines = [
        "# AI tool footprint: %s" % doc["parameters"]["path_name"],
        "",
        "| Field | Value |",
        "|---|---|",
        "| Result | **%s** |" % doc["result"].upper(),
        "| Generated (UTC) | %s |" % doc["generated_at_utc"],
        "| Script | %s %s |" % (doc["script"], doc["script_version"]),
        "| Requirements | %s |" % ", ".join(doc["requirements"]),
        "| Detected tools | %s |" % (", ".join("%s (%s)" % (k, ", ".join(v)) for k, v in
                                              r["detected_tools"].items()) or "none"),
        "| Known tools (inventory) | %s |" % (", ".join(doc["parameters"]["known_tools"])
                                             if doc["parameters"]["known_tools"] is not None
                                             else "not given"),
        "| Evidence JSON | `%s` |" % json_name,
        "| SHA-256 of JSON | `%s` |" % digest,
        "",
        "## Findings",
        "",
        "| Severity | Check | Tool | Message |",
        "|---|---|---|---|",
    ]
    for f in r["findings"]:
        lines.append("| %s | %s | %s | %s |" % (f["severity"], f["check"], f["tool"],
                                               f["message"].replace("|", "\\|")))
    lines += ["", "## Agent configuration and instruction files", ""]
    if r["files"]:
        lines += ["| Path | Tool | Description |", "|---|---|---|"]
        lines += ["| `%s` | %s | %s |" % (h["path"], h["tool"], h["description"])
                  for h in r["files"]]
    else:
        lines.append("- none found")
    lines += ["", "## AI-related workflows", ""]
    if r["workflows"]:
        lines += ["| Workflow | Tools | Actions | Secrets | Risks |", "|---|---|---|---|---|"]
    else:
        lines.append("- none found")
    for wf in r["workflows"]:
        lines.append("| `%s` | %s | %s | %s | %d |" % (
            wf["path"], ", ".join(wf["tools"]), ", ".join(a["uses"] for a in wf["actions"]),
            ", ".join(wf["secrets_referenced"]), len(wf["risks"])))
    lines += ["", "## Dependencies", ""]
    lines += ["- `%s` in `%s` (%s)" % (d["package"], d["manifest"], d["tool"])
              for d in r["dependencies"]] or ["- none found"]
    c = r["commits"]
    lines += ["", "## Commit attribution", ""]
    if not c:
        lines.append("- not scanned (no .git directory or --git-log 0)")
    elif c.get("error"):
        lines.append("- git log failed: %s" % c["error"])
    else:
        lines.append("- %d commits scanned" % c["commits_scanned"])
        lines += ["- %s: %d commits (%s .. %s), e.g. %s" % (t, i["commits"], i["first"], i["last"],
                                                         ", ".join(i["examples"]))
                  for t, i in c["by_tool"].items()]
    if r["org"] is not None:
        lines += ["", "## GitHub App installations (%s)" % doc["parameters"]["org"], ""]
        if not r["org"]["readable"]:
            lines.append("- not readable (HTTP %s)" % r["org"]["status"])
        else:
            lines += ["| App | AI-related | Repositories | Writes code/PRs |", "|---|---|---|---|"]
            lines += ["| %s | %s | %s | %s |" % (a["app_slug"], a["ai_related"],
                                                a["repository_selection"],
                                                a["can_write_code_or_prs"])
                      for a in r["org"]["installations"]]
            lines += ["", "Note: GitHub does not list the apps installed by the 'Allow Claude / "
                          "Codex coding agent' policies among installations; their actions "
                          "appear in the audit log."]
    lines += ["", "Heuristic text scan: review every hit. Record the reconciliation against the "
                  "tool inventory in the tool-discovery checklist.", ""]
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="List AI agent configuration files, AI-related CI workflows, AI SDK "
                    "dependencies and AI commit attribution in a repository; optionally the "
                    "GitHub App installations of an organisation. Writes JSON + Markdown "
                    "evidence.",
        epilog="Exit codes: 0 no failing finding, 1 failing finding, 2 usage/API error.")
    ap.add_argument("--path", default=".", help="repository working copy (default: .)")
    ap.add_argument("--org", help="GitHub organisation: also list its App installations "
                    "(GITHUB_TOKEN / GH_TOKEN or gh login of an org owner)")
    ap.add_argument("--known-tools", type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
                    help="comma-separated tool keys of the validated inventory (%s); any other "
                         "detected tool fails" % ", ".join(TOOL_KEYS))
    ap.add_argument("--git-log", type=int, default=200, metavar="N",
                    help="scan the last N commit messages for AI attribution (0 = skip)")
    ap.add_argument("--out", default="evidence", help="evidence directory (default: evidence)")
    ap.add_argument("--api-url", help="GitHub API base URL (default: $GITHUB_API_URL or "
                    "https://api.github.com)")
    ap.add_argument("--transport", choices=("auto", "token", "gh"), default="auto",
                    help=argparse.SUPPRESS)
    ap.add_argument("--fail-on-warn", action="store_true", help="exit 1 when warnings exist")
    ap.add_argument("--version", action="version", version="%(prog)s " + SCRIPT_VERSION)
    args = ap.parse_args(argv)
    if not Path(args.path).is_dir():
        ap.error("--path %s is not a directory" % args.path)
    for t in args.known_tools or []:
        if t not in TOOL_KEYS:
            ap.error("unknown tool key %r in --known-tools (use: %s)" % (t, ", ".join(TOOL_KEYS)))
    return args


def main(argv: Optional[List[str]] = None, runner: Callable[..., Any] = subprocess.run,
         client: Optional[GitHubClient] = None) -> int:
    args = parse_args(argv)
    root = Path(args.path).resolve()
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    try:
        report = analyse(root, args, runner, client)
    except ApiError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_ERROR
    counts = {s: sum(1 for f in report["findings"] if f["severity"] == s) for s in SEVERITY_ORDER}
    doc = {
        "schema": EVIDENCE_SCHEMA,
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requirements": ["REQ-05", "REQ-06", "REQ-12"],
        "parameters": {"path_name": root.name, "org": args.org,
                       "known_tools": args.known_tools, "git_log": args.git_log},
        "result": "fail" if counts["fail"] else "pass",
        "severity_counts": counts,
        "report": report,
    }
    base = "ai-footprint_%s_%s" % (re.sub(r"[^A-Za-z0-9._-]+", "-", root.name) or "repo",
                                   now.strftime("%Y%m%dT%H%M%SZ"))
    paths = write_evidence(args.out, base, doc, render_markdown)
    print("%s: %s - tools: %s (fail %d, warn %d)" % (
        root.name, doc["result"].upper(), ", ".join(report["detected_tools"]) or "none",
        counts["fail"], counts["warn"]))
    print("evidence: %s\n          %s\nsha256:   %s" % (paths["json"], paths["markdown"],
                                                       paths["json_sha256"]))
    if counts["fail"] or (args.fail_on_warn and counts["warn"]):
        return EXIT_FAIL
    return EXIT_PASS


if __name__ == "__main__":
    sys.exit(main())
