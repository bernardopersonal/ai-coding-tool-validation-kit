#!/usr/bin/env python3
"""Capture the configuration baseline of an AI coding tool on this machine and
in a repository (IQ-01 version, IQ-03 configuration baseline; REQ-06, REQ-08).

Per tool (claude_code, codex, other) the script

  * records the CLI version (`<cli> --version`) when the CLI is on PATH;
  * locates and hashes (SHA-256) the configuration files at the documented user,
    project and managed / admin locations;
  * extracts selected keys: permissions, sandbox, hooks, MCP servers, model
    settings, approval / sandbox policy (Codex), login and update controls;
  * hashes the instruction files (CLAUDE.md, AGENTS.md, ...);
  * Claude Code: combines the managed sources in the documented precedence
    (server-managed > MDM > managed file with its managed-settings.d drop-ins >
    HKCU; first source wins unless managedSourcesBehavior is "merge") and names
    the source of each finding;
  * records who ran it on which machine (executed_by; --operator is required);
  * optionally compares with a previous baseline (--compare): managed,
    requirements, project and declared files fail on drift, user-scope and cache
    files warn, and a version change is checked against --approved-version.

Secrets are never printed: values of keys that look like tokens, keys, headers
or passwords, environment values that are not known non-secret toggles, and
token-like strings are replaced by "<redacted>". Hashes are of the raw files.

Sources that this script cannot read (macOS MDM profiles, server-managed or
cloud-managed policy consoles, `/status` output) are listed as manual fields.

Python 3.9+ standard library only (TOML via tomllib on 3.11+, otherwise a small
built-in parser for the subset used in configuration files).

Exit codes: 0 pass (warnings allowed), 1 a check failed (unparseable file,
bypass mode configured, drift against --compare) or warnings with
--fail-on-warn, 2 usage error.
"""

from __future__ import annotations

import argparse
import datetime
import getpass
import glob
import hashlib
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:  # Python 3.11+
    import tomllib  # type: ignore
except ImportError:  # pragma: no cover - depends on the interpreter
    tomllib = None  # type: ignore

SCRIPT_NAME = "capture_baseline.py"
SCRIPT_VERSION = "0.2.0"
EVIDENCE_SCHEMA = "ai-coding-tool-validation-kit/evidence/v1"
EXIT_PASS, EXIT_FAIL, EXIT_ERROR = 0, 1, 2
REDACTED = "<redacted>"
SEVERITY_ORDER = {"fail": 0, "warn": 1, "info": 2}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".tox", "dist", "build",
             "target", ".mypy_cache", ".pytest_cache"}
MAX_TREE_FILES = 500

# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

SECRET_KEY_RE = re.compile(r"(?i)(token|secret|passw|api[_-]?key|apikey|credential|cookie|"
                           r"private[_-]?key|authorization|bearer|header)")
SAFE_KEY_RE = re.compile(r"(?i)(_env_var|^env_vars|credentials_store|^env_key)$")
SECRET_VALUE_RES = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(-----END [A-Z ]*PRIVATE KEY-----|$)"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bglpat-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}"),
]
URL_USERINFO_RE = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^/\s:@]+:[^/\s@]+@")
URL_QUERY_SECRET_RE = re.compile(r"(?i)([?&](?:token|key|api_key|apikey|access_token|sig|"
                                 r"signature|password)=)[^&\s\"']+")

# Environment variables whose values are not secret (verified toggles / exporters).
ENV_SAFE = {
    "CLAUDE_CODE_ENABLE_TELEMETRY", "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA",
    "OTEL_METRICS_EXPORTER", "OTEL_LOGS_EXPORTER", "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_LOG_USER_PROMPTS", "OTEL_LOG_ASSISTANT_RESPONSES",
    "OTEL_LOG_TOOL_DETAILS", "OTEL_LOG_TOOL_CONTENT", "OTEL_LOG_RAW_API_BODIES",
    "OTEL_LOG_MANAGED_SETTINGS", "DISABLE_UPDATES", "DISABLE_AUTOUPDATER", "DISABLE_TELEMETRY",
    "DISABLE_ERROR_REPORTING", "DISABLE_FEEDBACK_COMMAND", "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY", "CLAUDE_CODE_USE_MANTLE",
    "CLAUDE_CODE_USE_ANTHROPIC_AWS", "AWS_REGION", "CLOUD_ML_REGION", "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_MODEL", "ANTHROPIC_BASE_URL", "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB",
    "CLAUDE_CODE_SKIP_PROMPT_HISTORY", "CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE",
}


def redact_string(value: str) -> str:
    out = value
    for rx in SECRET_VALUE_RES:
        out = rx.sub(REDACTED, out)
    out = URL_USERINFO_RE.sub(lambda m: m.group(1) + REDACTED + "@", out)
    out = URL_QUERY_SECRET_RE.sub(lambda m: m.group(1) + REDACTED, out)
    return out


def is_secret_key(key: Any) -> bool:
    k = str(key)
    return bool(SECRET_KEY_RE.search(k)) and not SAFE_KEY_RE.search(k)


def redact(obj: Any, key: Optional[str] = None) -> Any:
    """Return a copy of obj with secret-looking keys and values replaced."""
    if key is not None and is_secret_key(key) and obj not in (None, "", [], {}, False, True):
        if isinstance(obj, dict):
            return {str(k): REDACTED for k in obj}
        if isinstance(obj, list):
            return [REDACTED for _ in obj]
        return REDACTED
    if isinstance(obj, dict):
        return {str(k): redact(v, str(k)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, key) for v in obj]
    if isinstance(obj, str):
        return redact_string(obj)
    return obj


def redact_env(env: Any) -> Any:
    if not isinstance(env, dict):
        return redact(env)
    out = {}
    for name, value in env.items():
        if str(name) in ENV_SAFE and not is_secret_key(name):
            out[str(name)] = redact(value)
        else:
            out[str(name)] = REDACTED
    return out


# ---------------------------------------------------------------------------
# TOML (tomllib, or a subset parser for Python 3.9 / 3.10)
# ---------------------------------------------------------------------------

class TomlSubsetError(ValueError):
    pass


class _TomlSubsetParser:
    """Tables, arrays of tables, dotted / quoted keys, strings (basic, literal,
    multi-line), integers, floats, booleans, arrays and inline tables. Dates are
    kept as strings. Enough for agent configuration files; not a full TOML."""

    BARE = re.compile(r"[A-Za-z0-9_-]+")
    ESC = {"b": "\b", "t": "\t", "n": "\n", "f": "\f", "r": "\r", '"': '"', "\\": "\\"}

    def __init__(self, text: str):
        self.s = text
        self.i = 0
        self.n = len(text)

    def error(self, msg: str) -> TomlSubsetError:
        line = self.s.count("\n", 0, self.i) + 1
        return TomlSubsetError("%s (line %d)" % (msg, line))

    def parse(self) -> Dict[str, Any]:
        root: Dict[str, Any] = {}
        cur = root
        while True:
            self.skip_blank()
            if self.i >= self.n:
                return root
            if self.s.startswith("[[", self.i):
                self.i += 2
                keys = self.key()
                self.expect("]]")
                parent = self.walk(root, keys[:-1])
                arr = parent.setdefault(keys[-1], [])
                if not isinstance(arr, list):
                    raise self.error("key %r is not an array of tables" % keys[-1])
                cur = {}
                arr.append(cur)
            elif self.s[self.i] == "[":
                self.i += 1
                keys = self.key()
                self.expect("]")
                cur = self.walk(root, keys)
            else:
                keys = self.key()
                self.expect("=")
                value = self.value()
                self.walk(cur, keys[:-1])[keys[-1]] = value
            self.end_line()

    def walk(self, d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        for k in keys:
            nxt = d.get(k)
            if nxt is None:
                nxt = d[k] = {}
            elif isinstance(nxt, list) and nxt and isinstance(nxt[-1], dict):
                nxt = nxt[-1]
            elif not isinstance(nxt, dict):
                raise self.error("key %r is not a table" % k)
            d = nxt
        return d

    def skip_ws(self) -> None:
        while self.i < self.n and self.s[self.i] in " \t":
            self.i += 1

    def skip_blank(self) -> None:
        while self.i < self.n:
            c = self.s[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif c == "#":
                while self.i < self.n and self.s[self.i] != "\n":
                    self.i += 1
            else:
                return

    def end_line(self) -> None:
        self.skip_ws()
        if self.i < self.n and self.s[self.i] == "#":
            while self.i < self.n and self.s[self.i] != "\n":
                self.i += 1
        if self.i < self.n and self.s[self.i] not in "\r\n":
            raise self.error("unexpected text %r" % self.s[self.i:self.i + 20])

    def expect(self, token: str) -> None:
        self.skip_ws()
        if not self.s.startswith(token, self.i):
            raise self.error("expected %r" % token)
        self.i += len(token)
        self.skip_ws()

    def key(self) -> List[str]:
        parts = []
        while True:
            self.skip_ws()
            c = self.s[self.i] if self.i < self.n else ""
            if c == '"':
                parts.append(self.basic_string())
            elif c == "'":
                parts.append(self.literal_string())
            else:
                m = self.BARE.match(self.s, self.i)
                if not m:
                    raise self.error("invalid key")
                parts.append(m.group(0))
                self.i = m.end()
            self.skip_ws()
            if self.i < self.n and self.s[self.i] == ".":
                self.i += 1
                continue
            return parts

    def basic_string(self) -> str:
        if self.s.startswith('"""', self.i):
            self.i += 3
            if self.s.startswith("\n", self.i):
                self.i += 1
            elif self.s.startswith("\r\n", self.i):
                self.i += 2
            return self._basic_until('"""', multiline=True)
        self.i += 1
        return self._basic_until('"', multiline=False)

    def _basic_until(self, end: str, multiline: bool) -> str:
        out = []
        while self.i < self.n:
            if self.s.startswith(end, self.i):
                self.i += len(end)
                return "".join(out)
            c = self.s[self.i]
            if c == "\\":
                nxt = self.s[self.i + 1:self.i + 2]
                if nxt in self.ESC:
                    out.append(self.ESC[nxt])
                    self.i += 2
                elif nxt in ("u", "U"):
                    width = 4 if nxt == "u" else 8
                    out.append(chr(int(self.s[self.i + 2:self.i + 2 + width], 16)))
                    self.i += 2 + width
                elif multiline and nxt in "\r\n \t":
                    self.i += 1
                    while self.i < self.n and self.s[self.i] in " \t\r\n":
                        self.i += 1
                else:
                    raise self.error("invalid escape")
            elif c == "\n" and not multiline:
                raise self.error("newline in string")
            else:
                out.append(c)
                self.i += 1
        raise self.error("unterminated string")

    def literal_string(self) -> str:
        if self.s.startswith("'''", self.i):
            self.i += 3
            if self.s.startswith("\n", self.i):
                self.i += 1
            end = self.s.find("'''", self.i)
        else:
            self.i += 1
            end = self.s.find("'", self.i)
            if "\n" in self.s[self.i:end if end >= 0 else self.n]:
                raise self.error("newline in literal string")
        if end < 0:
            raise self.error("unterminated literal string")
        text = self.s[self.i:end]
        self.i = end + (3 if self.s.startswith("'''", end) else 1)
        return text

    def value(self) -> Any:
        self.skip_ws()
        if self.i >= self.n:
            raise self.error("missing value")
        c = self.s[self.i]
        if c == '"':
            return self.basic_string()
        if c == "'":
            return self.literal_string()
        if c == "[":
            return self.array()
        if c == "{":
            return self.inline_table()
        m = re.compile(r"[^\s,\]\}#]+").match(self.s, self.i)
        if not m:
            raise self.error("invalid value")
        tok = m.group(0)
        self.i = m.end()
        if tok == "true":
            return True
        if tok == "false":
            return False
        num = tok.replace("_", "")
        try:
            if re.match(r"^[+-]?(0x[0-9a-fA-F]+|0o[0-7]+|0b[01]+)$", num):
                return int(num, 0)
            if re.match(r"^[+-]?\d+$", num):
                return int(num)
            if re.match(r"^[+-]?(\d+\.?\d*([eE][+-]?\d+)?|inf|nan)$", num):
                return float(num)
        except ValueError:
            pass
        if re.match(r"^\d{4}-\d{2}-\d{2}|^\d{2}:\d{2}", tok):
            # a datetime may contain a space-separated time part
            rest = re.compile(r"[ T]\d{2}:\d{2}[^\s,\]\}#]*").match(self.s, self.i)
            if rest and "T" not in tok:
                tok += rest.group(0)
                self.i = rest.end()
            return tok
        raise self.error("invalid value %r" % tok)

    def array(self) -> List[Any]:
        self.i += 1
        items = []
        while True:
            self.skip_blank()
            if self.i < self.n and self.s[self.i] == "]":
                self.i += 1
                return items
            items.append(self.value())
            self.skip_blank()
            if self.i < self.n and self.s[self.i] == ",":
                self.i += 1
            elif self.i < self.n and self.s[self.i] == "]":
                continue
            else:
                raise self.error("expected ',' or ']' in array")

    def inline_table(self) -> Dict[str, Any]:
        self.i += 1
        table: Dict[str, Any] = {}
        self.skip_ws()
        if self.i < self.n and self.s[self.i] == "}":
            self.i += 1
            return table
        while True:
            keys = self.key()
            self.expect("=")
            self.walk(table, keys[:-1])[keys[-1]] = self.value()
            self.skip_ws()
            if self.i < self.n and self.s[self.i] == ",":
                self.i += 1
                continue
            if self.i < self.n and self.s[self.i] == "}":
                self.i += 1
                return table
            raise self.error("expected ',' or '}' in inline table")


def parse_toml(text: str, force_subset: bool = False) -> Tuple[Dict[str, Any], str]:
    if tomllib is not None and not force_subset:
        return tomllib.loads(text), "tomllib"
    return _TomlSubsetParser(text).parse(), "builtin-subset"


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

def platform_key() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


CLAUDE_MANAGED_DIR = {
    "linux": "/etc/claude-code",
    "macos": "/Library/Application Support/ClaudeCode",
    "windows": r"C:\Program Files\ClaudeCode",
}


class Context:
    def __init__(self, args: argparse.Namespace, platform: Optional[str] = None):
        self.platform = platform or platform_key()
        self.home = Path(args.home).expanduser() if args.home else Path.home()
        self.repo = Path(args.repo).expanduser().resolve() if args.repo else None
        self.root = args.root or ""
        codex_home = args.codex_home or os.environ.get("CODEX_HOME")
        self.codex_home = Path(codex_home).expanduser() if codex_home else self.home / ".codex"
        self.force_toml_subset = bool(getattr(args, "force_toml_subset", False))

    def system(self, path: str) -> Path:
        """System path, optionally below --root (testing, mounted images)."""
        if not self.root:
            return Path(path)
        rel = re.sub(r"^[A-Za-z]:", "", path).replace("\\", "/").lstrip("/")
        return Path(self.root) / rel

    def show(self, path: Path) -> str:
        """Path for the evidence: repository-relative or home as '~' (no user names)."""
        p = str(path)
        if self.repo is not None:
            try:
                return "<repo>/" + Path(path).resolve().relative_to(self.repo).as_posix()
            except ValueError:
                pass
        home = str(self.home)
        if p == home or p.startswith(home.rstrip("/\\") + os.sep) or p.startswith(home + "/"):
            return "~" + p[len(home):].replace("\\", "/")
        if self.root and p.startswith(str(Path(self.root))):
            return "/" + Path(p).relative_to(self.root).as_posix()
        return p


# ---------------------------------------------------------------------------
# File records
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(ctx: Context, scope: str, path: Path, kind: str) -> Dict[str, Any]:
    rec: Dict[str, Any] = {"scope": scope, "kind": kind, "path": ctx.show(path),
                           "exists": path.is_file()}
    if not rec["exists"]:
        return rec
    st = path.stat()
    rec["size"] = st.st_size
    rec["mtime_utc"] = datetime.datetime.fromtimestamp(
        st.st_mtime, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if kind == "presence_only":
        rec["note"] = "content not read (credentials)"
        return rec
    rec["sha256"] = sha256_file(path)
    return rec


def expand(ctx: Context, scope: str, pattern: Path, kind: str) -> List[Dict[str, Any]]:
    pat = str(pattern)
    if any(ch in pat for ch in "*?["):
        matches = sorted(glob.glob(pat))
        return [file_record(ctx, scope, Path(m), kind) for m in matches if Path(m).is_file()]
    return [file_record(ctx, scope, pattern, kind)]


def walk_repo(repo: Path, names: set, max_depth: int = 6) -> List[Path]:
    found = []
    base_depth = len(repo.parts)
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        if len(Path(dirpath).parts) - base_depth >= max_depth:
            dirnames[:] = []
        for fn in sorted(filenames):
            if fn in names:
                found.append(Path(dirpath) / fn)
    return found


def tree_records(ctx: Context, scope: str, root: Path, kind: str, exclude: set) -> List[Dict]:
    out = []
    if not root.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            if str(p) in exclude:
                continue
            out.append(file_record(ctx, scope, p, kind))
            if len(out) >= MAX_TREE_FILES:
                return out
    return out


def load_structured(path: Path, fmt: str, ctx: Context) -> Tuple[Any, str, str]:
    """(data, status, parser) where status is 'ok' or an error message."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, "unreadable: %s" % exc.__class__.__name__, ""
    if fmt == "json":
        try:
            data = json.loads(text) if text.strip() else {}
        except ValueError as exc:
            return None, "invalid JSON: %s" % exc, "json"
        if not isinstance(data, dict):
            return None, "invalid: top level is not a JSON object", "json"
        return data, "ok", "json"
    try:
        data, parser = parse_toml(text, ctx.force_toml_subset)
    except (ValueError, IndexError) as exc:
        return None, "invalid TOML: %s" % exc, ""
    return data, "ok", parser


def dig(data: Any, dotted: str) -> Tuple[bool, Any]:
    cur = data
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False, None
    return True, cur


# ---------------------------------------------------------------------------
# Claude Code
# ---------------------------------------------------------------------------

CLAUDE_KEYS = [
    "permissions.defaultMode", "permissions.allow", "permissions.ask", "permissions.deny",
    "permissions.additionalDirectories", "permissions.disableBypassPermissionsMode",
    "permissions.disableAutoMode", "permissions.blockReadsOutsideWorkingDirectories",
    "disableAutoMode", "allowManagedPermissionRulesOnly", "allowManagedHooksOnly",
    "allowManagedMcpServersOnly", "disableAllHooks", "sandbox",
    "model", "availableModels", "availableModelsMatch", "enforceAvailableModels",
    "deniedModels", "fallbackModel", "switchModelsOnFlag", "modelPicker",
    "requiredMinimumVersion", "requiredMaximumVersion", "minimumVersion", "autoUpdatesChannel",
    "forceLoginMethod", "forceLoginOrgUUID", "allowedProviders",
    "attribution", "includeCoAuthoredBy", "cleanupPeriodDays", "forceRemoteSettingsRefresh",
    "managedSourcesBehavior", "enabledPlugins", "pluginConfigs", "disableSideloadFlags",
    "disableRemoteControl", "skipWebFetchPreflight", "feedbackDrafts",
]


def summarize_claude_hooks(hooks: Any) -> Any:
    if not isinstance(hooks, dict):
        return redact(hooks)
    out: Dict[str, Any] = {}
    for event, groups in hooks.items():
        items = []
        for group in groups if isinstance(groups, list) else []:
            if not isinstance(group, dict):
                continue
            handlers = []
            for h in group.get("hooks") or []:
                if isinstance(h, dict):
                    handlers.append(redact({k: h.get(k) for k in
                                            ("type", "command", "args", "url", "timeout",
                                             "onFailure") if k in h}))
            items.append({"matcher": group.get("matcher"), "handlers": handlers})
        out[str(event)] = items
    return out


def summarize_mcp_servers(servers: Any) -> Any:
    if not isinstance(servers, dict):
        return redact(servers)
    out = {}
    for name, cfg in servers.items():
        if not isinstance(cfg, dict):
            out[str(name)] = redact(cfg)
            continue
        item: Dict[str, Any] = {}
        for k, v in cfg.items():
            if k in ("env", "headers", "http_headers", "env_http_headers"):
                item[k] = sorted(str(x) for x in v) if isinstance(v, dict) else REDACTED
            elif k in ("tools",) and isinstance(v, dict):
                item[k] = {str(t): redact(c) for t, c in v.items()}
            else:
                item[k] = redact(v, k)
        out[str(name)] = item
    return out


def claude_selected(data: Dict[str, Any]) -> Dict[str, Any]:
    sel: Dict[str, Any] = {}
    for key in CLAUDE_KEYS:
        present, value = dig(data, key)
        if present:
            sel[key] = redact(value, key.split(".")[-1])
    if "hooks" in data:
        sel["hooks"] = summarize_claude_hooks(data["hooks"])
    if "env" in data:
        sel["env"] = redact_env(data["env"])
    if "claudeMd" in data and isinstance(data["claudeMd"], str):
        sel["claudeMd"] = {"sha256": hashlib.sha256(data["claudeMd"].encode("utf-8")).hexdigest(),
                           "length": len(data["claudeMd"])}
    if "apiKeyHelper" in data:
        sel["apiKeyHelper"] = "<present>"
    if "mcpServers" in data:
        sel["mcpServers"] = summarize_mcp_servers(data["mcpServers"])
    return sel


def read_windows_registry_claude() -> List[Dict[str, Any]]:  # pragma: no cover - Windows only
    out = []
    try:
        import winreg  # type: ignore
    except ImportError:
        return out
    for hive_name, hive in (("HKLM", winreg.HKEY_LOCAL_MACHINE), ("HKCU", winreg.HKEY_CURRENT_USER)):
        rec: Dict[str, Any] = {"scope": "managed_mdm" if hive_name == "HKLM" else "user_fallback",
                               "kind": "claude_settings", "exists": False,
                               "path": "%s\\SOFTWARE\\Policies\\ClaudeCode (value Settings)"
                                       % hive_name}
        try:
            with winreg.OpenKey(hive, r"SOFTWARE\Policies\ClaudeCode") as key:
                value, _ = winreg.QueryValueEx(key, "Settings")
        except OSError:
            out.append(rec)
            continue
        raw = str(value).encode("utf-8")
        rec.update(exists=True, size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        try:
            data = json.loads(value)
            rec["parse"] = "ok" if isinstance(data, dict) else "invalid: not an object"
            if isinstance(data, dict):
                rec["selected"] = claude_selected(data)
        except ValueError as exc:
            rec["parse"] = "invalid JSON: %s" % exc
        out.append(rec)
    return out


def capture_claude(ctx: Context) -> Dict[str, Any]:
    mdir = CLAUDE_MANAGED_DIR[ctx.platform]
    sep = "\\" if ctx.platform == "windows" else "/"
    managed = lambda name: ctx.system(mdir + sep + name)  # noqa: E731
    specs: List[Tuple[str, Path, str]] = [
        ("managed", managed("managed-settings.json"), "claude_settings"),
        ("managed", managed("managed-settings.d") / "*.json", "claude_settings"),
        ("managed", managed("managed-mcp.json"), "mcp"),
        ("managed", managed("CLAUDE.md"), "instructions"),
        ("server_managed_cache", ctx.home / ".claude" / "remote-settings.json", "claude_settings"),
        ("user", ctx.home / ".claude" / "settings.json", "claude_settings"),
        ("user", ctx.home / ".claude" / "CLAUDE.md", "instructions"),
    ]
    if ctx.repo:
        specs += [
            ("project", ctx.repo / ".claude" / "settings.json", "claude_settings"),
            ("local", ctx.repo / ".claude" / "settings.local.json", "claude_settings"),
            ("project", ctx.repo / ".mcp.json", "mcp"),
        ]
    files: List[Dict[str, Any]] = []
    for scope, path, kind in specs:
        files.extend(expand(ctx, scope, path, kind))
    if ctx.platform == "windows" and not ctx.root:  # pragma: no cover - Windows only
        files.extend(read_windows_registry_claude())
    captured = set()
    for rec, (scope, path, kind) in _with_paths(files, specs, ctx):
        if not rec.get("exists") or kind not in ("claude_settings", "mcp"):
            continue
        data, status, parser = load_structured(path, "json", ctx)
        captured.add(str(path))
        rec["parse"] = status
        if data is None:
            continue
        rec["selected"] = claude_selected(data) if kind == "claude_settings" else {
            "mcpServers": summarize_mcp_servers(data.get("mcpServers", {})),
            "top_level_keys": sorted(data)}
    instructions: List[Dict[str, Any]] = []
    tree: List[Dict[str, Any]] = []
    if ctx.repo:
        for p in walk_repo(ctx.repo, {"CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", "REVIEW.md"}):
            instructions.append(file_record(ctx, "project", p, "instructions"))
        tree = tree_records(ctx, "project", ctx.repo / ".claude", "project_tree", captured)
    return {
        "cli": "claude",
        "files": files,
        "instruction_files": instructions,
        "project_tree": tree,
        "manual_fields": [
            "`/status` output: 'Setting sources' line incl. the 'Enterprise managed settings' "
            "source and any 'Skipped sources' line",
            "`claude doctor` output (invalid entries, Auto-updates, Organization policy, "
            "Managed settings (remote))",
            "MDM payloads not read by this script: macOS domain com.anthropic.claudecode "
            "(the Windows registry value HKLM\\SOFTWARE\\Policies\\ClaudeCode\\Settings is "
            "read on Windows unless --root is given)",
            "Server-managed settings as configured in the claude.ai admin console (export or "
            "dated screenshot)",
            "Who may change each configuration source and the change-control reference",
        ],
    }


def _with_paths(files: List[Dict[str, Any]], specs: List[Tuple[str, Path, str]],
                ctx: Context):
    """Pair each existing file record with its real path and spec (for parsing)."""
    shown = {}
    for scope, path, kind in specs:
        pat = str(path)
        paths = [Path(m) for m in sorted(glob.glob(pat))] if any(c in pat for c in "*?[") \
            else [path]
        for p in paths:
            shown[(scope, ctx.show(p))] = (scope, p, kind)
    for rec in files:
        key = (rec.get("scope"), rec.get("path"))
        if key in shown:
            yield rec, shown[key]


# Managed-source precedence (Claude Code managed settings documentation):
# remote (server-managed) > MDM (macOS plist / Windows HKLM) > managed files
# (managed-settings.json, then managed-settings.d/*.json in alphabetical order) > HKCU.
# Default managedSourcesBehavior "first-wins": only the highest source that delivers a
# policy is used. "merge" combines the admin sources (HKCU never merges): lists union,
# locks take the strictest value, restriction allowlists come whole from the highest source.
CLAUDE_SOURCE_RANK = [("server_managed_cache", "server-managed (remote)"),
                      ("managed_mdm", "MDM"), ("managed", "managed file"),
                      ("user_fallback", "HKCU")]
WHOLE_KEYS = {"fallbackModel", "modelPicker"}
ALLOWLIST_KEYS = {"availableModels", "allowedMcpServers"}
LOCK_TRUE_KEYS = {"allowManagedPermissionRulesOnly", "allowManagedHooksOnly",
                  "allowManagedMcpServersOnly", "disableAllHooks", "enforceAvailableModels",
                  "disableSideloadFlags", "forceRemoteSettingsRefresh",
                  "permissions.blockReadsOutsideWorkingDirectories"}
LOCK_DISABLE_KEYS = {"permissions.disableBypassPermissionsMode", "permissions.disableAutoMode",
                     "disableAutoMode"}


def merge_settings(base: Dict[str, Any], later: Dict[str, Any]) -> Dict[str, Any]:
    """Later file over earlier file: scalars replaced, lists combined, objects merged key
    by key, fallbackModel / modelPicker replaced whole."""
    out = dict(base)
    for key, value in later.items():
        old = out.get(key)
        if key in WHOLE_KEYS:
            out[key] = value
        elif isinstance(old, list) and isinstance(value, list):
            out[key] = old + [v for v in value if v not in old]
        elif isinstance(old, dict) and isinstance(value, dict):
            out[key] = merge_settings(old, value)
        else:
            out[key] = value
    return out


def _strictest(key: str, a: Any, b: Any) -> Any:
    if key in LOCK_TRUE_KEYS:
        return True if (a is True or b is True) else (a if a is not None else b)
    if key in LOCK_DISABLE_KEYS:
        return "disable" if "disable" in (a, b) else (a if a is not None else b)
    return a


def effective_managed(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Effective managed policy and the source of every key, from the captured records."""
    by_scope: Dict[str, List[Dict[str, Any]]] = {}
    for r in files:
        if r.get("exists") and r.get("kind") == "claude_settings" and \
                r.get("scope") in dict(CLAUDE_SOURCE_RANK) and r.get("parse") in (None, "ok"):
            by_scope.setdefault(r["scope"], []).append(r)
    sources = []
    for scope, label in CLAUDE_SOURCE_RANK:
        recs = by_scope.get(scope) or []
        if not recs:
            continue
        if scope == "managed":
            # base file first, then drop-ins in alphabetical order (later wins)
            recs = sorted(recs, key=lambda r: (0 if r["path"].endswith("managed-settings.json")
                                               else 1, r["path"]))
        merged: Dict[str, Any] = {}
        key_source: Dict[str, str] = {}
        for r in recs:
            sel = r.get("selected") or {}
            merged = merge_settings(merged, sel)
            for k in sel:
                key_source[k] = r["path"]
        if merged:
            sources.append({"scope": scope, "label": label, "settings": merged,
                            "key_source": key_source, "paths": [r["path"] for r in recs]})
    behaviour = (sources[0]["settings"].get("managedSourcesBehavior") if sources else None) \
        or "first-wins"
    if not sources:
        return {"behaviour": behaviour, "settings": {}, "key_source": {}, "used": [],
                "skipped": []}
    if behaviour != "merge":
        top = sources[0]
        return {"behaviour": behaviour, "settings": top["settings"],
                "key_source": dict(top["key_source"]), "used": [top["label"]],
                "skipped": [s["label"] for s in sources[1:]]}
    admin = [s for s in sources if s["scope"] != "user_fallback"]
    settings: Dict[str, Any] = {}
    key_source: Dict[str, str] = {}
    for s in reversed(admin):  # lowest first, so higher sources override
        for k, v in s["settings"].items():
            if k in ALLOWLIST_KEYS:
                continue
            if k in LOCK_TRUE_KEYS or k in LOCK_DISABLE_KEYS:
                settings[k] = _strictest(k, settings.get(k), v)
            elif isinstance(settings.get(k), list) and isinstance(v, list):
                settings[k] = settings[k] + [x for x in v if x not in settings[k]]
            else:
                settings[k] = v
            key_source[k] = s["key_source"].get(k, s["label"])
    for s in admin:  # allowlists whole from the highest source that sets them
        for k in ALLOWLIST_KEYS:
            if k in s["settings"] and k not in settings:
                settings[k] = s["settings"][k]
                key_source[k] = s["key_source"].get(k, s["label"])
    return {"behaviour": behaviour, "settings": settings, "key_source": key_source,
            "used": [s["label"] for s in admin],
            "skipped": [s["label"] for s in sources if s["scope"] == "user_fallback"]}


def claude_findings(cap: Dict[str, Any]) -> List[Dict[str, str]]:
    f: List[Dict[str, str]] = []
    files = cap["files"]
    for r in files:
        if r.get("exists") and r.get("parse") not in (None, "ok"):
            f.append(finding("fail", "parse", "%s: %s" % (r["path"], r["parse"]), "REQ-06",
                             "IQ-03"))
        sel = r.get("selected") or {}
        if sel.get("permissions.defaultMode") == "bypassPermissions":
            f.append(finding("fail", "bypass_mode",
                             "%s sets permissions.defaultMode = bypassPermissions." % r["path"],
                             "REQ-07", "OQ-08", source=r["path"]))
    eff = effective_managed(files)
    cap["effective_managed"] = eff
    if not eff["used"]:
        f.append(finding("warn", "managed_settings",
                         "No managed settings found (file, drop-ins or server-managed cache). "
                         "MDM sources are not read: confirm the source with /status.",
                         "REQ-06", "OQ-09"))
        return f
    msel = eff["settings"]
    src = eff["key_source"]
    f.append(finding("info", "managed_sources",
                     "Effective managed policy (%s): %s%s." % (
                         eff["behaviour"], ", ".join(eff["used"]),
                         "; skipped: " + ", ".join(eff["skipped"]) if eff["skipped"] else ""),
                     "REQ-06", "IQ-03"))

    def where(*keys: str) -> str:
        for k in keys:
            if k in src:
                return src[k]
        return ", ".join(eff["used"])
    if msel.get("permissions.disableBypassPermissionsMode") != "disable":
        f.append(finding("warn", "disable_bypass",
                         "Effective managed settings do not set "
                         "permissions.disableBypassPermissionsMode = \"disable\".",
                         "REQ-07", "OQ-08",
                         source=where("permissions.disableBypassPermissionsMode")))
    auto_off = "disable" in (msel.get("disableAutoMode"), msel.get("permissions.disableAutoMode"))
    mode = msel.get("permissions.defaultMode")
    if not auto_off and (mode is None or mode == "auto"):
        f.append(finding("warn", "auto_mode",
                         "Effective managed settings leave auto mode on (no disableAutoMode "
                         "or permissions.disableAutoMode = \"disable\", and no "
                         "permissions.defaultMode other than auto); auto mode, in which a "
                         "classifier approves actions, can be the starting mode.",
                         "REQ-07", "OQ-08",
                         source=where("disableAutoMode", "permissions.disableAutoMode",
                                      "permissions.defaultMode")))
    if "availableModels" not in msel:
        f.append(finding("warn", "available_models",
                         "Effective managed settings do not restrict availableModels (model "
                         "envelope not enforced by the tool).", "REQ-08", "OQ-10"))
    elif msel.get("availableModelsMatch") != "exact":
        f.append(finding("warn", "available_models_match",
                         "availableModels uses prefix matching (availableModelsMatch is not "
                         "\"exact\"): later versions of a listed id are selectable before "
                         "their admission.", "REQ-08", "OQ-10", source=where("availableModels")))
    for key in ("allowManagedPermissionRulesOnly", "allowManagedHooksOnly",
                "allowManagedMcpServersOnly"):
        if msel.get(key) is not True:
            f.append(finding("info", key, "Effective managed settings do not set %s = true."
                             % key, "REQ-06", "OQ-09"))
    plugin_cfg = msel.get("pluginConfigs") if isinstance(msel.get("pluginConfigs"), dict) else {}
    guard = plugin_cfg.get("cc-plugin-sec-default@builtin")
    guard_opts = guard.get("options") if isinstance(guard, dict) else None
    mods_locked = isinstance(guard_opts, dict) and guard_opts.get("allowManagedModsOnly") is True
    if not (msel.get("allowManagedHooksOnly") is True
            or (mods_locked and msel.get("disableSideloadFlags") is True)):
        f.append(finding("info", "mods", "Effective managed settings leave hooks and mods "
                         "open: allowManagedHooksOnly is unset and mods are unrestricted "
                         "(pluginConfigs cc-plugin-sec-default@builtin allowManagedModsOnly "
                         "with disableSideloadFlags).", "REQ-06", "OQ-09",
                         source=where("pluginConfigs", "disableSideloadFlags")))
    sandbox = msel.get("sandbox") if isinstance(msel.get("sandbox"), dict) else {}
    if not sandbox.get("enabled"):
        f.append(finding("info", "sandbox", "Effective managed settings do not enable the "
                         "sandbox.", "REQ-07", "OQ-08", source=where("sandbox")))
    return f


# ---------------------------------------------------------------------------
# Codex
# ---------------------------------------------------------------------------

CODEX_CONFIG_KEYS = [
    "model", "model_provider", "model_reasoning_effort", "approval_policy", "approvals_reviewer",
    "sandbox_mode", "sandbox_workspace_write", "default_permissions", "permissions",
    "shell_environment_policy", "web_search", "features", "history.persistence",
    "analytics.enabled", "feedback.enabled", "check_for_update_on_startup",
    "forced_login_method", "forced_chatgpt_workspace_id", "cli_auth_credentials_store",
    "project_doc_max_bytes", "project_doc_fallback_filenames", "log_dir",
]
CODEX_REQUIREMENT_KEYS = [
    "allowed_approval_policies", "allowed_approvals_reviewers", "allowed_sandbox_modes",
    "allowed_permission_profiles", "default_permissions", "allowed_web_search_modes",
    "allow_managed_hooks_only", "allowed_login_methods", "allowed_chatgpt_workspaces",
    "cli_auth_credentials_store", "enforce_residency", "check_for_update_on_startup", "feedback",
    "features", "models", "permissions",
]


def _exporter_kind(value: Any) -> Any:
    if isinstance(value, dict):
        return sorted(value)
    return value


def codex_selected(data: Dict[str, Any], requirements: bool, ctx: Context) -> Dict[str, Any]:
    sel: Dict[str, Any] = {}
    for key in (CODEX_REQUIREMENT_KEYS if requirements else CODEX_CONFIG_KEYS):
        present, value = dig(data, key)
        if present:
            sel[key] = redact(value, key.split(".")[-1])
    if "mcp_servers" in data:
        sel["mcp_servers"] = summarize_mcp_servers(data["mcp_servers"])
    if "hooks" in data:
        sel["hooks"] = summarize_hook_tables(data["hooks"])
    if "notify" in data:
        sel["notify"] = "<present>"
    if isinstance(data.get("otel"), dict):
        o = data["otel"]
        sel["otel"] = {k: (_exporter_kind(o[k]) if "exporter" in k else redact(o[k], k))
                       for k in o if k != "headers"}
    if isinstance(data.get("model_providers"), dict):
        sel["model_providers"] = {str(n): redact({k: v for k, v in (c or {}).items()
                                                  if k in ("name", "base_url", "wire_api",
                                                           "env_key")})
                                  for n, c in data["model_providers"].items()
                                  if isinstance(c, dict)}
    if isinstance(data.get("projects"), dict):
        sel["projects"] = {ctx.show(Path(p)): (c or {}).get("trust_level")
                           for p, c in data["projects"].items() if isinstance(c, dict)}
    if requirements and isinstance(data.get("rules"), dict):
        rules = data["rules"].get("prefix_rules") or []
        decisions: Dict[str, int] = {}
        for r in rules if isinstance(rules, list) else []:
            d = str((r or {}).get("decision", "allow")) if isinstance(r, dict) else "?"
            decisions[d] = decisions.get(d, 0) + 1
        sel["rules"] = {"prefix_rules": len(rules) if isinstance(rules, list) else None,
                        "decisions": decisions}
    return sel


def summarize_hook_tables(hooks: Any) -> Any:
    if not isinstance(hooks, dict):
        return redact(hooks)
    out: Dict[str, Any] = {}
    for event, entries in hooks.items():
        if isinstance(entries, list):
            out[str(event)] = [redact({k: v for k, v in e.items()
                                       if k in ("matcher", "command", "type", "timeout")})
                               if isinstance(e, dict) else redact(e) for e in entries]
        else:
            out[str(event)] = redact(entries)
    return out


def summarize_rules_file(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"parse": "unreadable"}
    decisions: Dict[str, int] = {}
    for m in re.finditer(r"decision\s*=\s*[\"'](\w+)[\"']", text):
        decisions[m.group(1)] = decisions.get(m.group(1), 0) + 1
    return {"prefix_rule_calls": len(re.findall(r"\bprefix_rule\s*\(", text)),
            "decisions": decisions}


def capture_codex(ctx: Context) -> Dict[str, Any]:
    ch = ctx.codex_home
    if ctx.platform == "windows":
        pd = os.environ.get("ProgramData", r"C:\ProgramData")
        system_cfg = ctx.system(pd + r"\OpenAI\Codex\config.toml")
        system_req = ctx.system(pd + r"\OpenAI\Codex\requirements.toml")
        managed_cfg = ch / "managed_config.toml"
    else:
        system_cfg = ctx.system("/etc/codex/config.toml")
        system_req = ctx.system("/etc/codex/requirements.toml")
        managed_cfg = ctx.system("/etc/codex/managed_config.toml")
    specs: List[Tuple[str, Path, str]] = [
        ("requirements", system_req, "codex_requirements"),
        ("managed_defaults", managed_cfg, "codex_config"),
        ("system", system_cfg, "codex_config"),
        ("user", ch / "config.toml", "codex_config"),
        ("profile", ch / "*.config.toml", "codex_config"),
        ("user", ch / "hooks.json", "codex_hooks"),
        ("user", ch / "rules" / "*.rules", "codex_rules"),
        ("user", ch / "AGENTS.md", "instructions"),
        ("user", ch / "AGENTS.override.md", "instructions"),
        ("credentials", ch / "auth.json", "presence_only"),
    ]
    if ctx.repo:
        specs += [
            ("project", ctx.repo / ".codex" / "config.toml", "codex_config"),
            ("project", ctx.repo / ".codex" / "hooks.json", "codex_hooks"),
            ("project", ctx.repo / ".codex" / "rules" / "*.rules", "codex_rules"),
        ]
    files: List[Dict[str, Any]] = []
    for scope, path, kind in specs:
        files.extend(expand(ctx, scope, path, kind))
    fallback_names: set = set()
    trust = None
    for rec, (scope, path, kind) in _with_paths(files, specs, ctx):
        if not rec.get("exists"):
            continue
        if kind in ("codex_config", "codex_requirements"):
            data, status, parser = load_structured(path, "toml", ctx)
            rec["parse"] = status
            if parser:
                rec["parser"] = parser
            if data is not None:
                rec["selected"] = codex_selected(data, kind == "codex_requirements", ctx)
                names = data.get("project_doc_fallback_filenames")
                if isinstance(names, list):
                    fallback_names.update(str(n) for n in names)
                if scope == "user" and ctx.repo and isinstance(data.get("projects"), dict):
                    for p, c in data["projects"].items():
                        try:
                            if Path(p).expanduser().resolve() == ctx.repo and isinstance(c, dict):
                                trust = c.get("trust_level")
                        except OSError:
                            pass
        elif kind == "codex_hooks":
            data, status, _ = load_structured(path, "json", ctx)
            rec["parse"] = status
            if data is not None:
                rec["selected"] = {"hooks": summarize_hook_tables(data.get("hooks", data))}
        elif kind == "codex_rules":
            rec["selected"] = summarize_rules_file(path)
    instructions: List[Dict[str, Any]] = []
    if ctx.repo:
        names = {"AGENTS.md", "AGENTS.override.md"} | fallback_names
        for p in walk_repo(ctx.repo, names):
            instructions.append(file_record(ctx, "project", p, "instructions"))
    return {
        "cli": "codex",
        "codex_home": ctx.show(ch),
        "repo_trust_level": trust,
        "files": files,
        "instruction_files": instructions,
        "manual_fields": [
            "Cloud-managed requirements (Agent Security in the ChatGPT admin console; export the "
            "raw TOML or a dated screenshot)",
            "macOS MDM payloads not read by this script (domain com.openai.codex: "
            "config_toml_base64, requirements_toml_base64)",
            "`codex --strict-config doctor` and `codex features list` output",
            "TUI `/status` and `/hooks` output (workspace directories, hook sources and trust)",
            "Who may change each configuration source and the change-control reference",
        ],
    }


def codex_findings(cap: Dict[str, Any]) -> List[Dict[str, str]]:
    f: List[Dict[str, str]] = []
    reqs = [r for r in cap["files"] if r["scope"] == "requirements" and r.get("exists")]
    for r in cap["files"]:
        if r.get("exists") and r.get("parse") not in (None, "ok"):
            f.append(finding("fail", "parse", "%s: %s" % (r["path"], r["parse"]), "REQ-06",
                             "IQ-03"))
        sel = r.get("selected") or {}
        if r.get("kind") == "codex_config":
            if sel.get("sandbox_mode") == "danger-full-access":
                f.append(finding("warn", "sandbox_mode",
                                 "%s sets sandbox_mode = danger-full-access." % r["path"],
                                 "REQ-07", "OQ-08"))
            if sel.get("approval_policy") == "never":
                f.append(finding("warn", "approval_policy",
                                 "%s sets approval_policy = never." % r["path"], "REQ-07",
                                 "OQ-08"))
            if sel.get("approval_policy") == "untrusted":
                f.append(finding("warn", "approval_policy",
                                 "%s sets the retired approval_policy = untrusted." % r["path"],
                                 "REQ-06", "IQ-03"))
            sep = sel.get("shell_environment_policy")
            if isinstance(sep, dict) and sep.get("ignore_default_excludes", True) is not False:
                f.append(finding("info", "shell_environment_policy",
                                 "%s: shell_environment_policy.ignore_default_excludes is not "
                                 "false, so KEY/SECRET/TOKEN variables reach spawned commands."
                                 % r["path"], "REQ-09", "OQ-08"))
    if not reqs:
        f.append(finding("warn", "requirements",
                         "No admin-enforced requirements.toml found on this machine. "
                         "Cloud-managed requirements and MDM are not read: confirm them "
                         "separately.", "REQ-06", "OQ-09"))
    for r in reqs:
        sel = r.get("selected") or {}
        if "danger-full-access" in (sel.get("allowed_sandbox_modes") or []):
            f.append(finding("warn", "allowed_sandbox_modes",
                             "Requirements allow sandbox mode danger-full-access.", "REQ-07",
                             "OQ-08"))
        if "never" in (sel.get("allowed_approval_policies") or []):
            f.append(finding("warn", "allowed_approval_policies",
                             "Requirements allow approval policy 'never'.", "REQ-07", "OQ-08"))
        if "auto_review" in (sel.get("allowed_approvals_reviewers") or []):
            f.append(finding("warn", "allowed_approvals_reviewers",
                             "Requirements allow an agent (auto_review) to review "
                             "escalations on a person's behalf.", "REQ-02", "OQ-08"))
    if any(r["scope"] == "credentials" and r.get("exists") for r in cap["files"]):
        f.append(finding("info", "credential_cache",
                         "A file-based credential cache exists in the Codex home (plaintext); "
                         "consider cli_auth_credentials_store = keyring.", "REQ-09", "IQ-02"))
    return f


# ---------------------------------------------------------------------------
# Other tools
# ---------------------------------------------------------------------------

OTHER_INSTRUCTION_GLOBS = [
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md",
    ".github/instructions/**/*.instructions.md", ".github/hooks/*.json",
    ".cursor/rules/**", ".cursor/BUGBOT.md", ".cursor/config/bugbot.yaml", ".cursor/hooks.json",
    ".gemini/settings.json", ".aider.conf.yml",
]


def capture_other(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    files: List[Dict[str, Any]] = []
    for cfg in args.config or []:
        p = Path(cfg).expanduser()
        rec = file_record(ctx, "declared", p, "config")
        if rec.get("exists") and p.suffix.lower() == ".json":
            data, status, _ = load_structured(p, "json", ctx)
            rec["parse"] = status
            if data is not None:
                rec["selected"] = {"top_level_keys": sorted(data)}
        elif rec.get("exists") and p.suffix.lower() == ".toml":
            data, status, parser = load_structured(p, "toml", ctx)
            rec["parse"] = status
            if data is not None:
                rec["selected"] = {"top_level_keys": sorted(data)}
        files.append(rec)
    instructions: List[Dict[str, Any]] = []
    if ctx.repo:
        seen = set()
        for pattern in OTHER_INSTRUCTION_GLOBS:
            for m in sorted(glob.glob(str(ctx.repo / pattern), recursive=True)):
                if Path(m).is_file() and m not in seen:
                    seen.add(m)
                    instructions.append(file_record(ctx, "project", Path(m), "instructions"))
    return {
        "cli": args.name or "other",
        "files": files,
        "instruction_files": instructions,
        "manual_fields": [
            "Vendor admin console / policy settings (export or dated screenshot)",
            "User-level and managed configuration locations of this tool (verify against the "
            "vendor's current documentation and pass them with --config)",
            "Who may change each configuration source and the change-control reference",
        ],
    }


# ---------------------------------------------------------------------------
# Versions, comparison, report
# ---------------------------------------------------------------------------

def finding(severity: str, check: str, message: str, requirement: str = "",
            test: str = "", source: Optional[str] = None) -> Dict[str, str]:
    out = {"severity": severity, "check": check, "message": message,
           "requirement": requirement, "test": test}
    if source:
        out["source"] = source
    return out


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


def executed_by(operator: Optional[str], tool_login: Optional[str] = None,
                runner: Callable[..., Any] = subprocess.run) -> Dict[str, Any]:
    """Who ran the script on which machine (attributable evidence)."""
    try:
        os_user = getpass.getuser()
    except Exception:  # noqa: BLE001 - getuser raises various errors without a login name
        os_user = None
    try:
        hostname = socket.gethostname()
    except OSError:
        hostname = None
    return {"operator": operator, "os_user": os_user, "hostname": hostname,
            "machine_id_sha256": machine_id_sha256(runner), "github_login": None,
            "tool_login": tool_login}


def cli_version(command: List[str], runner: Callable[..., Any] = subprocess.run,
                which: Callable[[str], Optional[str]] = shutil.which) -> Dict[str, Any]:
    rec: Dict[str, Any] = {"command": " ".join(command), "found": False}
    exe = which(command[0])
    if not exe:
        return rec
    rec["found"] = True
    try:
        proc = runner([exe] + command[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      universal_newlines=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        rec["error"] = str(exc)
        return rec
    rec["exit_code"] = proc.returncode
    rec["output"] = redact_string((proc.stdout or proc.stderr or "").strip())[:300]
    return rec


# Drift grading by scope: controlled sources fail, user-level and cache files warn.
FAIL_SCOPES = {"managed", "managed_mdm", "requirements", "managed_defaults", "system",
               "project", "declared"}
VERSION_RE = re.compile(r"\d+\.\d+\.\d+[\w.-]*")


def compare(prev: Dict[str, Any], doc: Dict[str, Any],
            approved_versions: Optional[List[str]] = None) -> List[Dict[str, str]]:
    common = set(prev.get("tools") or {}) & set(doc.get("tools") or {})

    def index(d: Dict[str, Any]) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
        out = {}
        for tool, cap in (d.get("tools") or {}).items():
            if tool not in common:  # compare only the tools captured in both runs
                continue
            for section in ("files", "instruction_files", "project_tree"):
                for r in cap.get(section) or []:
                    if r.get("exists"):
                        out[(tool, r.get("scope", ""), r.get("path", ""))] = r
        return out

    def severity(scope: str) -> str:
        return "fail" if scope in FAIL_SCOPES else "warn"
    f = []
    old, new = index(prev), index(doc)
    for key in sorted(set(old) | set(new)):
        tool, scope, path = key
        if key not in new:
            f.append(finding(severity(scope), "drift", "%s %s file removed since baseline: %s"
                             % (tool, scope, path), "REQ-06", "IQ-03", source=path))
        elif key not in old:
            f.append(finding(severity(scope), "drift", "%s %s file added since baseline: %s"
                             % (tool, scope, path), "REQ-06", "IQ-03", source=path))
        elif old[key].get("sha256") != new[key].get("sha256"):
            if scope == "server_managed_cache":
                # compare the effective managed values (the cache file bytes may differ)
                if old[key].get("selected") != new[key].get("selected"):
                    f.append(finding("fail", "drift", "%s server-managed settings changed since "
                                     "baseline (values in %s)" % (tool, path), "REQ-06", "IQ-03",
                                     source=path))
                else:
                    f.append(finding("info", "drift", "%s server-managed cache rewritten, values "
                                     "unchanged: %s" % (tool, path), "REQ-06", "IQ-03",
                                     source=path))
                continue
            f.append(finding(severity(scope), "drift", "%s %s file changed since baseline: %s"
                             % (tool, scope, path), "REQ-06", "IQ-03", source=path))
    approved = [v.strip() for v in (approved_versions or []) if v.strip()]
    for tool, cap in (doc.get("tools") or {}).items():
        before = ((prev.get("tools") or {}).get(tool) or {}).get("version", {}).get("output")
        after = (cap.get("version") or {}).get("output")
        if tool not in (prev.get("tools") or {}) or before == after:
            continue
        m = VERSION_RE.search(after or "")
        number = m.group(0) if m else after
        if not approved:
            f.append(finding("warn", "drift", "%s version changed since baseline: %r -> %r (no "
                             "--approved-version given)" % (tool, before, after), "REQ-06",
                             "IQ-01"))
        elif number in approved:
            f.append(finding("info", "drift", "%s version changed since baseline to an approved "
                             "version: %r -> %r" % (tool, before, after), "REQ-06", "IQ-01"))
        else:
            f.append(finding("fail", "drift", "%s version %r is not an approved version (%s)"
                             % (tool, number, ", ".join(approved)), "REQ-06", "IQ-01"))
    if not f:
        f.append(finding("info", "drift", "No drift against the reference baseline.", "REQ-06",
                         "IQ-03"))
    return f


def render_markdown(doc: Dict[str, Any], digest: str, json_name: str) -> str:
    p = doc["parameters"]
    lines = [
        "# Configuration baseline: %s" % ", ".join(doc["tools"]),
        "",
        "| Field | Value |",
        "|---|---|",
        "| Result | **%s** |" % doc["result"].upper(),
        "| Generated (UTC) | %s |" % doc["generated_at_utc"],
        "| Script | %s %s |" % (doc["script"], doc["script_version"]),
        "| Kit tests | %s |" % ", ".join(doc["kit_tests"]),
        "| Requirements | %s |" % ", ".join(doc["requirements"]),
        "| Host platform | %s (Python %s) |" % (doc["host"]["platform"], doc["host"]["python"]),
        "| Executed by | operator %s; OS user %s; host %s; machine id SHA-256 %s%s |" % (
            _cell(doc["executed_by"].get("operator")), _cell(doc["executed_by"].get("os_user")),
            _cell(doc["executed_by"].get("hostname")),
            _cell((doc["executed_by"].get("machine_id_sha256") or "not readable")[:16]),
            "; tool login: %s" % _cell(doc["executed_by"]["tool_login"])
            if doc["executed_by"].get("tool_login") else ""),
        "| Repository | %s |" % (p.get("repo") or "not given"),
        "| Reference baseline | %s |" % (p.get("compare") or "none"),
        "| Evidence JSON | `%s` |" % json_name,
        "| SHA-256 of JSON | `%s` |" % digest,
        "",
        "## Findings",
        "",
        "| Severity | Check | Requirement | Test | Source | Message |",
        "|---|---|---|---|---|---|",
    ]
    for f in doc["findings"]:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            f["severity"], f["check"], f["requirement"], f["test"],
            _cell(f.get("source", "")), _cell(f["message"])))
    for tool, cap in doc["tools"].items():
        v = cap.get("version") or {}
        lines += ["", "## %s" % tool, "",
                  "Version: `%s` -> %s" % (v.get("command", ""), _cell(
                      v.get("output") if v.get("found") else "CLI not found on PATH")), ""]
        if cap.get("repo_trust_level") is not None:
            lines += ["Repository trust level in user config: `%s`" % cap["repo_trust_level"], ""]
        lines += ["| Scope | Kind | Path | Present | SHA-256 | Parse |", "|---|---|---|---|---|---|"]
        for r in cap.get("files", []) + cap.get("instruction_files", []) + \
                cap.get("project_tree", []):
            lines.append("| %s | %s | `%s` | %s | %s | %s |" % (
                r["scope"], r["kind"], _cell(r["path"]), "yes" if r.get("exists") else "no",
                ("`%s`" % r["sha256"]) if r.get("sha256") else "", r.get("parse", "")))
        eff = cap.get("effective_managed")
        if eff and eff.get("used"):
            lines += ["", "Effective managed policy (%s; sources used: %s%s):" % (
                eff["behaviour"], ", ".join(eff["used"]),
                "; skipped: " + ", ".join(eff["skipped"]) if eff["skipped"] else ""), "",
                "```json", json.dumps(eff["settings"], indent=2, sort_keys=True), "```"]
        selected = {r["path"]: r["selected"] for r in cap.get("files", []) if r.get("selected")}
        if selected:
            lines += ["", "Selected settings (secrets redacted):", "", "```json",
                      json.dumps(selected, indent=2, sort_keys=True), "```"]
        lines += ["", "Manual fields (fill in from the tool or console):", ""]
        lines += ["- [ ] " + m for m in cap.get("manual_fields", [])]
    lines += ["", "This file is evidence produced by a script. Review, conclusion and approval "
                  "are recorded by the responsible people in the QMS.", ""]
    return "\n".join(lines)


def _cell(value: Any) -> str:
    return ("" if value is None else str(value)).replace("|", "\\|").replace("\n", " ")


def write_evidence(out_dir: str, base: str, doc: Dict[str, Any],
                   render_md: Callable[[Dict[str, Any], str, str], str]) -> Dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    json_path = out / (base + ".json")
    json_path.write_bytes(data)
    with open(out / (base + ".json.sha256"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("%s  %s\n" % (digest, json_path.name))
    md_path = out / (base + ".md")
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_md(doc, digest, json_path.name))
    return {"json": str(json_path), "markdown": str(md_path), "json_sha256": digest}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="Capture the configuration baseline of AI coding tools (versions, hashed "
                    "config and instruction files, selected keys with secrets redacted) as "
                    "JSON + Markdown evidence (IQ-01, IQ-03).",
        epilog="Exit codes: 0 pass, 1 check failed (parse error, bypass mode, drift), "
               "2 usage error.")
    ap.add_argument("--tool", action="append", required=True,
                    choices=("claude_code", "codex", "other", "all"),
                    help="tool to capture (repeatable; all = claude_code + codex)")
    ap.add_argument("--repo", help="repository working copy to inspect for project settings "
                    "and instruction files")
    ap.add_argument("--out", default="evidence", help="evidence directory (default: evidence)")
    ap.add_argument("--compare", metavar="BASELINE_JSON",
                    help="previous baseline JSON from this script: differences in managed, "
                         "requirements, project and declared files fail; user-scope and cache "
                         "differences warn; server-managed settings are compared value by "
                         "value")
    ap.add_argument("--approved-version", action="append", default=[], metavar="VERSION",
                    help="validated tool version for --compare (repeatable): a version change "
                         "to one of these is info, to any other version a failure")
    ap.add_argument("--operator", default=os.environ.get("KIT_OPERATOR"), metavar="NAME",
                    help="name of the person running the capture, recorded in the evidence "
                         "(required; default $KIT_OPERATOR)")
    ap.add_argument("--home", help="home directory to inspect (default: the current user's)")
    ap.add_argument("--codex-home", help="Codex home (default: $CODEX_HOME or ~/.codex)")
    ap.add_argument("--root", help="prefix for system paths such as /etc (testing or a "
                    "mounted machine image)")
    ap.add_argument("--name", help="display name for --tool other")
    ap.add_argument("--version-cmd", help="version command for --tool other, e.g. "
                    "\"mytool --version\"")
    ap.add_argument("--config", action="append", default=[], metavar="PATH",
                    help="configuration file of --tool other to hash (repeatable)")
    ap.add_argument("--force-toml-subset", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--fail-on-warn", action="store_true", help="exit 1 when warnings exist")
    ap.add_argument("--version", action="version", version="%(prog)s " + SCRIPT_VERSION)
    args = ap.parse_args(argv)
    tools: List[str] = []
    for t in args.tool:
        for x in (["claude_code", "codex"] if t == "all" else [t]):
            if x not in tools:
                tools.append(x)
    args.tools = tools
    if args.repo and not Path(args.repo).expanduser().is_dir():
        ap.error("--repo %s is not a directory" % args.repo)
    if not (args.operator or "").strip():
        ap.error("--operator NAME (or $KIT_OPERATOR) is required: the evidence records who "
                 "captured the baseline")
    return args


def codex_login(tools: Dict[str, Any], runner: Callable[..., Any],
                which: Callable[[str], Optional[str]]) -> Optional[str]:
    """`codex login status` output when Codex is captured (no verified status command is
    used for the other tools)."""
    if "codex" not in tools or not which("codex"):
        return None
    rec = cli_version(["codex", "login", "status"], runner, which)
    return rec.get("output") or None


def run(args: argparse.Namespace, runner: Callable[..., Any] = subprocess.run,
        which: Callable[[str], Optional[str]] = shutil.which,
        platform: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, str]]:
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    ctx = Context(args, platform)
    tools: Dict[str, Any] = {}
    findings: List[Dict[str, str]] = []
    for tool in args.tools:
        if tool == "claude_code":
            cap = capture_claude(ctx)
            cap["version"] = cli_version(["claude", "--version"], runner, which)
            findings += [dict(x, tool=tool) for x in claude_findings(cap)]
        elif tool == "codex":
            cap = capture_codex(ctx)
            cap["version"] = cli_version(["codex", "--version"], runner, which)
            findings += [dict(x, tool=tool) for x in codex_findings(cap)]
        else:
            cap = capture_other(ctx, args)
            cmd = shlex.split(args.version_cmd) if args.version_cmd else []
            cap["version"] = cli_version(cmd, runner, which) if cmd else {
                "command": "", "found": False, "note": "no --version-cmd given"}
        if not cap["version"].get("found"):
            findings.append(finding("info", "version", "%s: CLI not found on PATH; record the "
                                    "version per surface manually." % tool, "REQ-06", "IQ-01"))
        tools[tool] = cap
    doc: Dict[str, Any] = {
        "schema": EVIDENCE_SCHEMA,
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kit_tests": ["IQ-01", "IQ-03"],
        "requirements": ["REQ-06", "REQ-08"],
        "host": {"platform": ctx.platform, "python": "%d.%d.%d" % sys.version_info[:3]},
        "executed_by": executed_by(args.operator, codex_login(tools, runner, which), runner),
        "parameters": {"tools": args.tools, "repo": ctx.repo.name if ctx.repo else None,
                       "compare": Path(args.compare).name if args.compare else None,
                       "root": args.root or None},
        "tools": tools,
    }
    if args.compare:
        try:
            prev = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            findings.append(finding("fail", "drift", "cannot read reference baseline: %s" % exc,
                                    "REQ-06", "IQ-03"))
        else:
            findings += compare(prev, doc, args.approved_version)
    findings.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 9))
    doc["findings"] = findings
    doc["severity_counts"] = {s: sum(1 for f in findings if f["severity"] == s)
                              for s in SEVERITY_ORDER}
    doc["result"] = "fail" if doc["severity_counts"]["fail"] else "pass"
    base = "baseline_%s_%s" % ("-".join(args.tools), now.strftime("%Y%m%dT%H%M%SZ"))
    paths = write_evidence(args.out, base, doc, render_markdown)
    return doc, paths


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    doc, paths = run(args)
    c = doc["severity_counts"]
    found = sum(1 for cap in doc["tools"].values() for r in cap.get("files", [])
                if r.get("exists"))
    print("baseline %s: %s (fail %d, warn %d) - %d configuration file(s) found" % (
        ", ".join(doc["tools"]), doc["result"].upper(), c["fail"], c["warn"], found))
    print("evidence: %s\n          %s\nsha256:   %s" % (paths["json"], paths["markdown"],
                                                       paths["json_sha256"]))
    if doc["result"] != "pass" or (args.fail_on_warn and c["warn"]):
        return EXIT_FAIL
    return EXIT_PASS


if __name__ == "__main__":
    sys.exit(main())
