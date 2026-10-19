"""Configuration: defaults, validation and derived template variables.

The config file is JSON (``kit.config.json``). It holds only the user's
answers; every derived field (booleans, document IDs, lists for loops,
``today``) is computed by :func:`derive` at render time, so the file can never
contain inconsistent derived values.

``VARIABLES`` is the registry of every variable available to templates. It
is used to generate the variable reference in README_DEV.md, and a unit test
checks that :func:`derive` produces exactly these keys.
"""

from __future__ import annotations

import copy
import datetime
import fnmatch
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from . import __version__ as KIT_VERSION

# --------------------------------------------------------------------------
# Option catalogues (order is significant: it is the canonical output order)
# --------------------------------------------------------------------------

CONTEXTS: List[Tuple[str, str, str]] = [
    ("code_product", "Product code",
     "Code for the regulated product (software in or as a medical device)."),
    ("code_tooling", "Internal tooling",
     "Internal tools, scripts and automation that are not part of the product."),
    ("pr_review", "Advisory AI PR review",
     "AI review comments on pull requests; advisory only, never counted as the "
     "required human approval."),
    ("test_generation", "Test generation",
     "Generation of unit, integration or regression tests and test data."),
    ("doc_drafting", "Document drafting",
     "Drafting of controlled documents and records, previewed and approved by a "
     "human before they are written or released."),
    ("agents_qms", "QMS agents",
     "Autonomous or scheduled agents acting on QMS systems."),
]
CONTEXT_KEYS = [c[0] for c in CONTEXTS]

SURFACES: List[Tuple[str, str]] = [
    ("local_cli_ide", "Local CLI / IDE"),
    ("cloud_agent", "Cloud agent"),
    ("pr_review_bot", "PR review bot"),
    ("ci_headless", "CI / headless"),
]
SURFACE_KEYS = [s[0] for s in SURFACES]

# Defaults offered by the wizard per tool type. The model ids are obvious
# placeholders: replace them with the ids from the vendor's current release notes.
# Templates never hard-code model names (they come from approved_models).
TOOL_TYPES: Dict[str, Dict[str, Any]] = {
    "claude_code": {
        "label": "Claude Code (Anthropic)",
        "tool_name": "Claude Code", "tool_id": "CLAUDE", "vendor": "Anthropic",
        "surfaces": ["local_cli_ide", "pr_review_bot", "ci_headless"],
        "approved_models": ["anthropic-model-*"],
    },
    "codex": {
        "label": "OpenAI Codex",
        "tool_name": "OpenAI Codex", "tool_id": "CODEX", "vendor": "OpenAI",
        "surfaces": ["local_cli_ide", "cloud_agent"],
        "approved_models": ["openai-model-*"],
    },
    "copilot": {
        "label": "GitHub Copilot",
        "tool_name": "GitHub Copilot", "tool_id": "COPILOT", "vendor": "GitHub",
        "surfaces": ["local_cli_ide", "pr_review_bot"],
        "approved_models": [],
    },
    "cursor": {
        "label": "Cursor",
        "tool_name": "Cursor", "tool_id": "CURSOR", "vendor": "Anysphere",
        "surfaces": ["local_cli_ide"],
        "approved_models": [],
    },
    "other": {
        "label": "Other AI coding tool",
        "tool_name": "", "tool_id": "", "vendor": "",
        "surfaces": ["local_cli_ide"],
        "approved_models": [],
    },
}
TOOL_KEYS = list(TOOL_TYPES)

REGULATIONS: List[Tuple[str, str, str]] = [
    # (config key, wizard key, label)
    ("reg_iso13485", "iso13485", "ISO 13485:2016 (clause 4.1.6, software validation)"),
    ("reg_fda_qmsr", "fda_qmsr", "FDA QMSR (21 CFR Part 820, incorporates ISO 13485)"),
    ("reg_gxp", "gxp", "GxP: EU GMP Annex 11 + 21 CFR Part 11"),
    ("reg_iso27001", "iso27001", "ISO/IEC 27001 (cross-references)"),
    ("reg_iso42001", "iso42001", "ISO/IEC 42001 (cross-references)"),
]
REG_KEYS = [r[0] for r in REGULATIONS]

CODE_HOSTS: List[Tuple[str, str]] = [
    ("github", "GitHub"), ("gitlab", "GitLab"), ("other", "Other Git hosting")]
RISK_MODELS: List[Tuple[str, str]] = [
    ("csa", "FDA CSA style: high process risk / not high process risk"),
    ("three_level", "Three levels: low / medium / high"),
]
MODEL_POLICIES: List[Tuple[str, str]] = [
    ("envelope", "any model in the approved envelope; output independently verified "
                 "downstream (human review + CI); admission check on entry"),
    ("pinned", "exact model id pinned; the AI output itself counts as a control or as "
               "evidence; any change = confirmatory OQ subset + MA-01 before use"),
]

# Validation profiles. Both use the same canonical IDs (REQ-xx, IQ-xx, OQ-xx, MA-01,
# PQ-xx); lite is a strict subset of full, so lite evidence is reused when upgrading.
PROFILES: List[Tuple[str, str]] = [
    ("lite", "risk-proportionate minimum: validation plan, test record and report per "
             "tool, for AI output that is always independently verified downstream "
             "(human review + CI); needs an approver at two gates and a PQ addendum after "
             "release; not available with a hard stop (L1, L2, L8, L9)"),
    ("full", "in-depth package: 8 documents per tool plus the shared code-host gate "
             "qualification"),
]
PROFILE_KEYS = [p[0] for p in PROFILES]
NEW_CONFIG_PROFILE = "lite"   # default for configs created by the kit (init --defaults)
LEGACY_PROFILE = "full"       # configs without the key (kit 0.1.0) keep rendering as full

# Per-tool documents (template number -> title) and shared documents.
TOOL_DOCS: List[Tuple[str, str]] = [
    ("01", "Inventory and intended use"),
    ("02", "Requirements"),
    ("03", "Risk assessment"),
    ("04", "Validation plan"),
    ("05", "Test protocol"),
    ("06", "Configuration baseline"),
    ("07", "Validation report"),
    ("08", "Change and revalidation"),
]
LITE_TOOL_DOCS: Dict[str, str] = {
    "01": "Validation plan",
    "02": "Test record",
    "03": "Validation report",
}
# Lite documents get their own number token (per tool nn "L01" to "L03", shared
# GEN-L01 and GEN-L02) so that a document ID always names one document: the lite plan
# never shares an ID with the full inventory (01), nor the lite work instruction with
# the full one (GEN-01). On upgrade the full documents supersede the lite records under
# their own IDs; the evidence IDs (IQ, OQ, MA, PQ) are reused.
LITE_DOC_NN: Dict[str, str] = {nn: "L" + nn for nn in LITE_TOOL_DOCS}

# Answers that make the lite profile impossible or questionable. Each item:
# (config key, wizard question, L number). All are optional booleans (absent = false).
LITE_STOP_KEYS: List[Tuple[str, str, str]] = [
    ("agent_qms_write",
     "Can an agent, interactive or autonomous, write to QMS systems outside the code-host "
     "gate (eQMS, issue tracker or document system, for example through MCP or an API)?",
     "L2"),
    ("ai_output_as_evidence",
     "Are AI-generated tests or other AI output used as verification evidence or as QMS "
     "records without independent review of their adequacy?",
     "L8"),
    ("agent_untrusted_with_secrets",
     "Does an agent that holds write credentials or secrets beyond the pull-request path read "
     "untrusted content (issues or comments from outside contributors, web pages, "
     "third-party MCP results)?",
     "L9"),
]
LITE_STOP_CONFIG_KEYS = [k for k, _, _ in LITE_STOP_KEYS]
SHARED_DOCS: List[Tuple[str, str, str]] = [
    ("doc_id_wi", "01", "AI-assisted development work instruction"),
    ("doc_id_discovery", "02", "Tool discovery checklist"),
    ("doc_id_gates", "03", "Code-host gate qualification"),
]
# Shared documents of the lite profile (doc_id_gates has no lite counterpart: lite records
# the code-host steps in the first tool's test record, so it keeps the full ID).
LITE_SHARED_NN: Dict[str, str] = {"doc_id_wi": "L01", "doc_id_discovery": "L02"}
SHARED_TOOL_TOKEN = "GEN"

# --------------------------------------------------------------------------
# Default configuration (fictional example company)
# --------------------------------------------------------------------------

DEFAULT_CONFIG: Dict[str, Any] = {
    "profile": NEW_CONFIG_PROFILE,
    "org_name": "Acme MedSoft",
    "org_code": "ACME",
    "doc_id_pattern": "{org}-VAL-{tool}-{nn}",
    "product_context": "Class II SaMD (FDA 510(k)); EU MDR Class IIa planned",
    "reg_iso13485": True,
    "reg_fda_qmsr": True,
    "reg_gxp": False,
    "reg_iso27001": False,
    "reg_iso42001": False,
    "role_executor": "Validation Engineer",
    "role_approver": "Head of QA",
    "role_tool_owner": "Engineering Lead",
    "role_prrc": "",
    "code_host": "github",
    "tools": [
        {
            "tool_key": "claude_code",
            "tool_name": "Claude Code",
            "tool_id": "CLAUDE",
            "vendor": "Anthropic",
            "surfaces": ["local_cli_ide", "pr_review_bot", "ci_headless"],
            "approved_models": ["anthropic-model-*"],
            "model_policy": "envelope",
            "pinned_model": "",
        },
        {
            "tool_key": "codex",
            "tool_name": "OpenAI Codex",
            "tool_id": "CODEX",
            "vendor": "OpenAI",
            "surfaces": ["local_cli_ide", "cloud_agent"],
            "approved_models": ["openai-model-*"],
            "model_policy": "envelope",
            "pinned_model": "",
        },
    ],
    "contexts": ["code_product", "code_tooling", "pr_review"],
    "agent_qms_write": False,
    "ai_output_as_evidence": False,
    "agent_untrusted_with_secrets": False,
    "risk_model": "csa",
    "already_in_use": True,
    "periodic_review_months": 12,
}


def default_config() -> Dict[str, Any]:
    """A fresh deep copy of DEFAULT_CONFIG."""
    return copy.deepcopy(DEFAULT_CONFIG)


# --------------------------------------------------------------------------
# Variable registry (the ONLY variables templates may use)
# --------------------------------------------------------------------------

def _tool_bool_vars() -> List[Tuple[str, str, str, str]]:
    return [("tool", "is_" + k, "bool", "Tool type is `%s` (%s)." % (k, TOOL_TYPES[k]["label"]))
            for k in TOOL_KEYS]


VARIABLES: List[Tuple[str, str, str, str]] = (
    # (scope, name, type, description)
    [
        ("global", "kit_version", "str", "Kit version that rendered the document."),
        ("global", "today", "str", "Render date, ISO format (YYYY-MM-DD). Optional config "
                                   "override: `today`."),
        ("global", "org_name", "str", "Organisation legal name."),
        ("global", "org_code", "str", "Short organisation code used in document IDs."),
        ("global", "doc_id_pattern", "str", "Document ID pattern with tokens `{org}`, "
                                            "`{tool}`, `{nn}`."),
        ("global", "product_context", "str", "Product / regulatory context (free text)."),
        ("global", "profile", "str", "Validation profile rendered: `lite` or `full` (config key "
                                     "`profile`, overridden by `--profile`; a config without the "
                                     "key renders as `full`)."),
        ("global", "profile_lite", "bool", "`profile` is `lite` (templates/lite/)."),
        ("global", "profile_full", "bool", "`profile` is `full` (templates/full/)."),
        ("global", "full_recommended", "bool", "The answers contain a trigger for the full "
                                               "profile: a hard stop (`lite_blocked`), context "
                                               "`doc_drafting` (L3) or GxP (L4). Independent of "
                                               "the profile rendered."),
        ("global", "full_reasons", "list[str]", "One short sentence per trigger behind "
                                                "`full_recommended`, starting with its L number; "
                                                "empty list when none (scalars: use `{{.}}`)."),
        ("global", "lite_blocked", "bool", "The answers contain a hard stop for the lite "
                                           "profile: model policy `pinned` (L1), context "
                                           "`agents_qms` or `agent_qms_write` (L2), "
                                           "`ai_output_as_evidence` (L8), "
                                           "`agent_untrusted_with_secrets` (L9). A lite render "
                                           "then needs `--force` and is not valid for release."),
        ("global", "lite_blockers", "list[str]", "The reasons of `full_reasons` that are hard "
                                                 "stops (scalars: use `{{.}}`)."),
        ("global", "config_file", "str", "Config file as given to `render` / `init` "
                                         "(`kit.config.json` when rendered without a file)."),
    ]
    + [("global", key, "bool", label) for key, _, label in REGULATIONS]
    + [
        ("global", "role_executor", "str", "Role that executes the validation."),
        ("global", "role_approver", "str", "Role that approves the validation "
                                           "(always different from the executor)."),
        ("global", "role_tool_owner", "str", "Role that owns the tool and its configuration."),
        ("global", "owner_is_executor", "bool", "`role_tool_owner` and `role_executor` are the "
                                                "same role (small team: the approver does the "
                                                "technical review)."),
        ("global", "role_prrc", "str", "PRRC role/name; empty string if not set (use "
                                       "`{{#role_prrc}}...{{/role_prrc}}`)."),
        ("global", "code_host", "str", "Git hosting: `github`, `gitlab` or `other`."),
        ("global", "code_github", "bool", "`code_host` is `github`."),
        ("global", "code_gitlab", "bool", "`code_host` is `gitlab`."),
        ("global", "code_other", "bool", "`code_host` is `other`."),
        ("global", "contexts", "list[str]", "Selected context keys, canonical order "
                                            "(scalars: use `{{.}}`)."),
        ("global", "contexts_list", "list[context]", "Selected contexts as items "
                                                     "{key, label, description}."),
    ]
    + [("global", "ctx_" + k, "bool", "Context `%s` selected: %s" % (k, d))
       for k, _, d in CONTEXTS]
    + [("global", k, "bool", "%s: %s (optional config key, default false)." % (n, q))
       for k, q, n in LITE_STOP_KEYS]
    + [
        ("global", "risk_model", "str", "`csa` or `three_level`."),
        ("global", "risk_csa", "bool", "`risk_model` is `csa` (high / not high process risk)."),
        ("global", "risk_three", "bool", "`risk_model` is `three_level` (low / medium / high)."),
        ("global", "already_in_use", "bool", "Tool already in use: add retrospective "
                                             "validation and interim-use justification."),
        ("global", "periodic_review_months", "int", "Periodic review interval in months."),
        ("global", "doc_id_wi", "str", "Doc ID of the shared work instruction "
                                       "(tool token `GEN`; full: nn `01`; lite: nn `L01`)."),
        ("global", "doc_id_discovery", "str", "Doc ID of the shared tool-discovery checklist "
                                              "(tool token `GEN`; full: nn `02`; lite: nn "
                                              "`L02`)."),
        ("global", "doc_id_gates", "str", "Doc ID of the shared code-host gate qualification "
                                          "(tool token `GEN`, nn `03`): OQ-01 to OQ-07 and OQ-12 "
                                          "executed once per code host for all tools (full "
                                          "profile only)."),
        ("global", "tools_list", "list[tool]", "All tools (each item has the tool variables "
                                               "below)."),
        ("global", "tools", "list[tool]", "Alias of `tools_list`."),
        ("tool", "tool_key", "str", "Tool type: `claude_code`, `codex`, `copilot`, `cursor` "
                                    "or `other`."),
        ("tool", "tool_name", "str", "Display name, e.g. Claude Code."),
        ("tool", "tool_id", "str", "Short code used in doc IDs and as output folder name."),
        ("tool", "vendor", "str", "Vendor name."),
        ("tool", "surfaces", "list[str]", "Surface keys in use, canonical order "
                                          "(scalars: use `{{.}}`)."),
        ("tool", "surfaces_list", "list[surface]", "Surfaces in use as items {key, label}."),
    ]
    + [("tool", "surf_" + k, "bool", "Surface `%s` (%s) in use." % (k, label))
       for k, label in SURFACES]
    + [
        ("tool", "approved_models", "list[str]", "Approved model ids or family patterns "
                                                 "(scalars: use `{{.}}`)."),
        ("tool", "model_policy", "str", "`envelope` or `pinned`."),
        ("tool", "policy_envelope", "bool", "`model_policy` is `envelope`."),
        ("tool", "policy_pinned", "bool", "`model_policy` is `pinned`."),
        ("tool", "pinned_model", "str", "Exact pinned model id; empty string when envelope."),
    ]
    + _tool_bool_vars()
    + [("tool", "doc_id_" + nn, "str", "Doc ID of per-tool document %s (%s)." % (
        nn, "full: %s, nn `%s`; lite: %s, nn `%s`" % (title, nn, LITE_TOOL_DOCS[nn],
                                                     LITE_DOC_NN[nn])
        if nn in LITE_TOOL_DOCS else "full: %s" % title)) for nn, title in TOOL_DOCS]
    + [
        ("context item", "key", "str", "Context key, e.g. `code_product`."),
        ("context item", "label", "str", "Short human-readable label."),
        ("context item", "description", "str", "One-sentence description."),
        ("surface item", "key", "str", "Surface key, e.g. `local_cli_ide`."),
        ("surface item", "label", "str", "Short human-readable label."),
    ]
)

SCOPE_TITLES = [
    ("global", "Global variables (every template)"),
    ("tool", "Tool variables (per-tool templates, and inside `{{#tools_list}}` loops)"),
    ("context item", "Items of `contexts_list` (inside `{{#contexts_list}}`)"),
    ("surface item", "Items of `surfaces_list` (inside `{{#surfaces_list}}`)"),
]


def variable_names(scope: str) -> List[str]:
    return [v[1] for v in VARIABLES if v[0] == scope]


def variables_markdown() -> str:
    """Markdown reference of every template variable (used by README_DEV.md)."""
    out: List[str] = []
    for scope, title in SCOPE_TITLES:
        out.append("#### " + title)
        out.append("")
        out.append("| Variable | Type | Description |")
        out.append("|---|---|---|")
        for vscope, name, vtype, desc in VARIABLES:
            if vscope == scope:
                out.append("| `%s` | %s | %s |" % (name, vtype, desc))
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

class ConfigError(Exception):
    """Invalid configuration; ``errors`` lists every problem found."""

    def __init__(self, errors: List[str], source: str = "config") -> None:
        self.errors = list(errors)
        self.source = source
        super().__init__("%s is invalid:\n  - %s" % (source, "\n  - ".join(self.errors)))


REQUIRED_KEYS = [
    "org_name", "org_code", "doc_id_pattern", "product_context",
    "reg_iso13485", "reg_fda_qmsr", "reg_gxp", "reg_iso27001", "reg_iso42001",
    "role_executor", "role_approver", "role_tool_owner", "code_host", "tools",
    "contexts", "risk_model", "already_in_use", "periodic_review_months",
]
OPTIONAL_KEYS = ["role_prrc", "today", "profile"] + LITE_STOP_CONFIG_KEYS
TOOL_REQUIRED_KEYS = ["tool_key", "tool_name", "tool_id", "vendor", "surfaces",
                      "approved_models", "model_policy"]
TOOL_OPTIONAL_KEYS = ["pinned_model"]

ORG_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,15}$")
TOOL_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,15}$")
MODEL_RE = re.compile(r"^[A-Za-z0-9*?][A-Za-z0-9._:/@+*?\[\]-]{0,99}$")
PATTERN_TOKENS = ("org", "tool", "nn")


def _is_bool(v: Any) -> bool:
    return isinstance(v, bool)


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def check_text(value: Any, label: str, allow_empty: bool = False,
               max_len: int = 300) -> Optional[str]:
    if not isinstance(value, str):
        return "%s must be a string" % label
    if not allow_empty and not value.strip():
        return "%s must not be empty" % label
    if len(value) > max_len:
        return "%s is longer than %d characters" % (label, max_len)
    if "{{" in value or "}}" in value:
        return "%s must not contain '{{' or '}}'" % label
    return None


def check_org_code(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not ORG_CODE_RE.match(value):
        return ("org_code must be 1-16 characters: letters, digits, '-' or '_' "
                "(starting with a letter or digit)")
    return None


def check_doc_id_pattern(value: Any) -> Optional[str]:
    err = check_text(value, "doc_id_pattern")
    if err:
        return err
    tokens = re.findall(r"\{([^{}]*)\}", value)
    unknown = [t for t in tokens if t not in PATTERN_TOKENS]
    if unknown:
        return "doc_id_pattern has unknown token(s) %s; allowed: {org}, {tool}, {nn}" % (
            ", ".join("{%s}" % t for t in unknown))
    if "{tool}" not in value or "{nn}" not in value:
        return "doc_id_pattern must contain both {tool} and {nn} so that IDs are unique"
    stripped = re.sub(r"\{(org|tool|nn)\}", "", value)
    if "{" in stripped or "}" in stripped:
        return "doc_id_pattern has unbalanced braces"
    return None


def check_tool_id(value: Any, used: Optional[List[str]] = None) -> Optional[str]:
    if not isinstance(value, str) or not TOOL_ID_RE.match(value):
        return ("tool_id must be 1-16 characters: uppercase letters, digits or '_', "
                "starting with a letter (e.g. CLAUDE)")
    if value == SHARED_TOOL_TOKEN:
        return "tool_id '%s' is reserved for the shared documents" % SHARED_TOOL_TOKEN
    if used and value in used:
        return "tool_id '%s' is used by more than one tool" % value
    return None


def check_model(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not MODEL_RE.match(value):
        return ("model entry %r is not a valid model id or pattern (letters, digits, "
                "'._:/@+-', wildcards '*', '?', '[...]'; no spaces)" % (value,))
    return None


def is_pattern(model: str) -> bool:
    return any(ch in model for ch in "*?[")


def model_in_envelope(model: str, approved: List[str]) -> bool:
    return any(fnmatch.fnmatchcase(model, entry) for entry in approved)


def check_pinned_model(value: Any, approved: List[str]) -> Optional[str]:
    err = check_model(value)
    if err:
        return err
    if is_pattern(value):
        return "pinned_model must be an exact model id (patterns belong in approved_models)"
    if not model_in_envelope(value, approved):
        return "pinned_model '%s' does not match any approved_models entry" % value
    return None


def _check_key_list(values: Any, allowed: List[str], label: str,
                    min_count: int = 1) -> List[str]:
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        return ["%s must be a list of strings" % label]
    errors = []
    unknown = [v for v in values if v not in allowed]
    if unknown:
        errors.append("%s has unknown value(s) %s; allowed: %s" % (
            label, ", ".join(unknown), ", ".join(allowed)))
    if len(set(values)) != len(values):
        errors.append("%s has duplicate values" % label)
    if len(values) < min_count:
        errors.append("%s needs at least %d value(s)" % (label, min_count))
    return errors


def _unknown_keys(obj: Dict[str, Any], allowed: List[str], derived: List[str],
                  prefix: str) -> List[str]:
    errors = []
    for key in obj:
        if key.startswith("_") or key in allowed:
            continue
        if key in derived:
            errors.append("%s'%s' is derived automatically; remove it from the config"
                          % (prefix, key))
        else:
            errors.append("%sunknown key '%s'" % (prefix, key))
    return errors


def validate_tool(tool: Any, index: int, used_ids: List[str]) -> List[str]:
    if not isinstance(tool, dict):
        return ["tools[%d] must be an object" % index]
    tid = tool.get("tool_id")
    prefix = "tools[%d]%s: " % (index, " (%s)" % tid if isinstance(tid, str) and tid else "")
    errors = _unknown_keys(tool, TOOL_REQUIRED_KEYS + TOOL_OPTIONAL_KEYS,
                           variable_names("tool"), prefix)
    missing = [k for k in TOOL_REQUIRED_KEYS if k not in tool]
    if missing:
        errors.append(prefix + "missing key(s): " + ", ".join(missing))

    def add(err: Optional[str]) -> None:
        if err:
            errors.append(prefix + err)

    if "tool_key" in tool and tool["tool_key"] not in TOOL_KEYS:
        add("tool_key must be one of: " + ", ".join(TOOL_KEYS))
    if "tool_name" in tool:
        add(check_text(tool["tool_name"], "tool_name", max_len=80))
    if "tool_id" in tool:
        add(check_tool_id(tool["tool_id"], used_ids))
    if "vendor" in tool:
        add(check_text(tool["vendor"], "vendor", max_len=80))
    if "surfaces" in tool:
        errors.extend(prefix + e for e in _check_key_list(tool["surfaces"], SURFACE_KEYS,
                                                          "surfaces"))
    approved = tool.get("approved_models")
    approved_ok = False
    if "approved_models" in tool:
        if not isinstance(approved, list) or not approved:
            add("approved_models must be a non-empty list of model ids or patterns")
        else:
            model_errors = [check_model(m) for m in approved]
            for err in model_errors:
                add(err)
            if len(set(approved)) != len(approved):
                add("approved_models has duplicate entries")
            approved_ok = not any(model_errors)
    policy = tool.get("model_policy")
    if "model_policy" in tool and policy not in ("envelope", "pinned"):
        add("model_policy must be 'envelope' or 'pinned'")
    pinned = tool.get("pinned_model", "")
    if policy == "pinned":
        if not pinned:
            add("model_policy 'pinned' requires pinned_model (an exact model id)")
        elif approved_ok:
            add(check_pinned_model(pinned, approved))
    elif policy == "envelope" and pinned not in ("", None):
        add("pinned_model is only allowed with model_policy 'pinned' (set it to \"\")")
    return errors


def validate_config(cfg: Any) -> List[str]:
    """Return a list of human-readable errors (empty when the config is valid)."""
    if not isinstance(cfg, dict):
        return ["the configuration must be a JSON object"]
    errors = _unknown_keys(cfg, REQUIRED_KEYS + OPTIONAL_KEYS, variable_names("global"), "")
    missing = [k for k in REQUIRED_KEYS if k not in cfg]
    if missing:
        errors.append("missing key(s): " + ", ".join(missing))

    def add(err: Optional[str]) -> None:
        if err:
            errors.append(err)

    for key, max_len in (("org_name", 120), ("product_context", 300),
                         ("role_executor", 80), ("role_approver", 80),
                         ("role_tool_owner", 80)):
        if key in cfg:
            add(check_text(cfg[key], key, max_len=max_len))
    if "role_prrc" in cfg:
        add(check_text(cfg["role_prrc"], "role_prrc", allow_empty=True, max_len=80))
    if "org_code" in cfg:
        add(check_org_code(cfg["org_code"]))
    if "doc_id_pattern" in cfg:
        add(check_doc_id_pattern(cfg["doc_id_pattern"]))
    for key in REG_KEYS + ["already_in_use"] + LITE_STOP_CONFIG_KEYS:
        if key in cfg and not _is_bool(cfg[key]):
            add("%s must be true or false" % key)
    executor, approver = cfg.get("role_executor"), cfg.get("role_approver")
    if isinstance(executor, str) and isinstance(approver, str) and executor.strip() and \
            executor.strip().casefold() == approver.strip().casefold():
        add("role_executor and role_approver must be different (executor != approver)")
    if "profile" in cfg and cfg["profile"] not in PROFILE_KEYS:
        add("profile must be one of: " + ", ".join(PROFILE_KEYS))
    if "code_host" in cfg and cfg["code_host"] not in [h[0] for h in CODE_HOSTS]:
        add("code_host must be one of: " + ", ".join(h[0] for h in CODE_HOSTS))
    if "risk_model" in cfg and cfg["risk_model"] not in [r[0] for r in RISK_MODELS]:
        add("risk_model must be one of: " + ", ".join(r[0] for r in RISK_MODELS))
    if "contexts" in cfg:
        errors.extend(_check_key_list(cfg["contexts"], CONTEXT_KEYS, "contexts"))
    if "periodic_review_months" in cfg:
        months = cfg["periodic_review_months"]
        if not _is_int(months) or not 1 <= months <= 36:
            add("periodic_review_months must be an integer between 1 and 36")
    if "today" in cfg:
        today = cfg["today"]
        try:
            datetime.date.fromisoformat(today)
            if len(today) != 10:
                raise ValueError
        except (TypeError, ValueError):
            add("today must be an ISO date string (YYYY-MM-DD)")
    if "tools" in cfg:
        tools = cfg["tools"]
        if not isinstance(tools, list) or not tools:
            add("tools must be a non-empty list")
        else:
            used: List[str] = []
            for i, tool in enumerate(tools):
                errors.extend(validate_tool(tool, i, used))
                if isinstance(tool, dict) and isinstance(tool.get("tool_id"), str):
                    used.append(tool["tool_id"])
    return errors


# --------------------------------------------------------------------------
# Loading / saving
# --------------------------------------------------------------------------

def load_config(path: Union[str, Path]) -> Dict[str, Any]:
    """Read and validate a JSON config file; raises ConfigError."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(["cannot read file: %s" % exc], str(path))
    try:
        cfg = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(["invalid JSON at line %d column %d: %s" % (
            exc.lineno, exc.colno, exc.msg)], str(path))
    errors = validate_config(cfg)
    if errors:
        raise ConfigError(errors, str(path))
    return cfg


def _ordered(obj: Dict[str, Any], order: List[str]) -> Dict[str, Any]:
    rank: Dict[str, int] = {}
    for i, k in enumerate(order):
        rank.setdefault(k, i)  # first occurrence wins
    keys = sorted(obj, key=lambda k: (0 if k.startswith("_") else 1, rank.get(k, len(rank))))
    return {k: obj[k] for k in keys}


def config_to_json(cfg: Dict[str, Any]) -> str:
    """Serialise a config with a stable, canonical key order."""
    out = _ordered(cfg, list(DEFAULT_CONFIG) + OPTIONAL_KEYS)
    if isinstance(out.get("tools"), list):
        out["tools"] = [_ordered(t, TOOL_REQUIRED_KEYS + TOOL_OPTIONAL_KEYS)
                        if isinstance(t, dict) else t for t in out["tools"]]
    return json.dumps(out, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------

def config_profile(cfg: Dict[str, Any]) -> str:
    """Profile stored in a config; a config without the key renders as full (0.1.0)."""
    return cfg.get("profile") or LEGACY_PROFILE


def effective_profile(cfg: Dict[str, Any], override: Optional[str] = None) -> str:
    """``override`` (e.g. ``--profile``) wins over the config; raises ConfigError if invalid."""
    if override is not None and override not in PROFILE_KEYS:
        raise ConfigError(["profile must be one of: " + ", ".join(PROFILE_KEYS)])
    return override or config_profile(cfg)


def _profile_triggers(cfg: Dict[str, Any]) -> List[Tuple[str, bool]]:
    """[(reason, hard stop)] in L-number order, read from the answers."""
    out: List[Tuple[str, bool]] = []
    tools = cfg.get("tools") if isinstance(cfg.get("tools"), list) else []
    pinned = ["%s (%s)" % (t.get("tool_name", ""), t.get("tool_id", "")) for t in tools
              if isinstance(t, dict) and t.get("model_policy") == "pinned"]
    if pinned:
        out.append(("L1, hard stop: Model policy pinned for %s: the AI output itself counts "
                    "as a control or as evidence." % ", ".join(pinned), True))
    contexts = cfg.get("contexts") if isinstance(cfg.get("contexts"), list) else []
    if "agents_qms" in contexts:
        out.append(("L2, hard stop: Context agents_qms: autonomous or scheduled agents act on "
                    "QMS systems (REQ-14, OQ-30).", True))
    if cfg.get("agent_qms_write") is True:
        out.append(("L2, hard stop: An agent can write to QMS systems outside the code-host "
                    "gate (agent_qms_write).", True))
    if "doc_drafting" in contexts:
        out.append(("L3: Context doc_drafting: the AI drafts controlled documents or records; "
                    "full is required unless each draft is independently verified (REQ-13, "
                    "OQ-20).", False))
    if cfg.get("reg_gxp") is True:
        out.append(("L4: GxP in scope (EU GMP Annex 11, 21 CFR Part 11): full is required for "
                    "high-impact GxP use.", False))
    if cfg.get("ai_output_as_evidence") is True:
        out.append(("L8, hard stop: AI output is used as verification evidence or as a QMS "
                    "record without independent review of its adequacy.", True))
    if cfg.get("agent_untrusted_with_secrets") is True:
        out.append(("L9, hard stop: An agent with write credentials or secrets reads untrusted "
                    "content (full adds OQ-40).", True))
    return out


def full_profile_reasons(cfg: Dict[str, Any]) -> List[str]:
    """Short reasons why the answers call for the full profile (empty: lite may do).

    Triggers read from the answers, each starting with its L number (lite plan
    section 2): model policy ``pinned`` (L1), context ``agents_qms`` or
    ``agent_qms_write`` (L2), context ``doc_drafting`` (L3), GxP (L4),
    ``ai_output_as_evidence`` (L8) and ``agent_untrusted_with_secrets`` (L9).
    L1, L2, L8 and L9 are hard stops (:func:`lite_blockers`). ``risk_model``
    ``three_level`` is not a trigger by itself. Triggers that cannot be read from
    the answers (L5 to L7: a CSA "high process risk" determination, auditor or
    customer expectations, previous audit findings on the tool) are decided in
    the lite plan.
    """
    return [reason for reason, _hard in _profile_triggers(cfg)]


def lite_blockers(cfg: Dict[str, Any]) -> List[str]:
    """The hard stops among :func:`full_profile_reasons` (L1, L2, L8, L9)."""
    return [reason for reason, hard in _profile_triggers(cfg) if hard]


# --------------------------------------------------------------------------
# Derivation
# --------------------------------------------------------------------------

def format_doc_id(pattern: str, org: str, tool: str, nn: str) -> str:
    values = {"org": org, "tool": tool, "nn": nn}
    return re.sub(r"\{(org|tool|nn)\}", lambda m: values[m.group(1)], pattern)


def derive_tool(tool: Dict[str, Any], cfg: Dict[str, Any],
                profile: str = LEGACY_PROFILE) -> Dict[str, Any]:
    surfaces = [k for k in SURFACE_KEYS if k in tool["surfaces"]]
    policy = tool["model_policy"]
    out: Dict[str, Any] = {
        "tool_key": tool["tool_key"],
        "tool_name": tool["tool_name"],
        "tool_id": tool["tool_id"],
        "vendor": tool["vendor"],
        "surfaces": surfaces,
        "surfaces_list": [{"key": k, "label": label} for k, label in SURFACES
                          if k in surfaces],
    }
    for key in SURFACE_KEYS:
        out["surf_" + key] = key in surfaces
    out["approved_models"] = list(tool["approved_models"])
    out["model_policy"] = policy
    out["policy_envelope"] = policy == "envelope"
    out["policy_pinned"] = policy == "pinned"
    out["pinned_model"] = tool.get("pinned_model", "") if policy == "pinned" else ""
    for key in TOOL_KEYS:
        out["is_" + key] = tool["tool_key"] == key
    for nn, _title in TOOL_DOCS:
        token = LITE_DOC_NN.get(nn, nn) if profile == "lite" else nn
        out["doc_id_" + nn] = format_doc_id(cfg["doc_id_pattern"], cfg["org_code"],
                                            tool["tool_id"], token)
    return out


def derive(cfg: Dict[str, Any], today: Optional[str] = None,
           profile: Optional[str] = None,
           config_file: Optional[str] = None) -> Dict[str, Any]:
    """Validate ``cfg`` and return the global template context.

    ``profile`` overrides the config's ``profile`` (``--profile``).
    ``config_file`` is the config path as given on the command line. Each item
    of ``tools_list`` is the per-tool context (pushed on top of the global
    context when per-tool templates are rendered).
    """
    errors = validate_config(cfg)
    if errors:
        raise ConfigError(errors)
    profile = effective_profile(cfg, profile)
    cfg = copy.deepcopy(cfg)
    ctx: Dict[str, Any] = {
        "kit_version": KIT_VERSION,
        "today": today or cfg.get("today") or datetime.date.today().isoformat(),
    }
    for key in ("org_name", "org_code", "doc_id_pattern", "product_context"):
        ctx[key] = cfg[key]
    ctx["profile"] = profile
    for key in PROFILE_KEYS:
        ctx["profile_" + key] = profile == key
    reasons = full_profile_reasons(cfg)
    ctx["full_recommended"] = bool(reasons)
    ctx["full_reasons"] = reasons
    blockers = lite_blockers(cfg)
    ctx["lite_blocked"] = bool(blockers)
    ctx["lite_blockers"] = blockers
    ctx["config_file"] = config_file or "kit.config.json"
    for key in REG_KEYS:
        ctx[key] = bool(cfg[key])
    for key in ("role_executor", "role_approver", "role_tool_owner"):
        ctx[key] = cfg[key].strip()
    ctx["owner_is_executor"] = (ctx["role_tool_owner"].casefold() ==
                                ctx["role_executor"].casefold())
    ctx["role_prrc"] = cfg.get("role_prrc", "").strip()
    ctx["code_host"] = cfg["code_host"]
    for host, _label in CODE_HOSTS:
        ctx["code_" + host] = cfg["code_host"] == host
    selected = [k for k in CONTEXT_KEYS if k in cfg["contexts"]]
    ctx["contexts"] = selected
    ctx["contexts_list"] = [{"key": k, "label": label, "description": desc}
                            for k, label, desc in CONTEXTS if k in selected]
    for key in CONTEXT_KEYS:
        ctx["ctx_" + key] = key in selected
    for key in LITE_STOP_CONFIG_KEYS:
        ctx[key] = cfg.get(key) is True
    ctx["risk_model"] = cfg["risk_model"]
    ctx["risk_csa"] = cfg["risk_model"] == "csa"
    ctx["risk_three"] = cfg["risk_model"] == "three_level"
    ctx["already_in_use"] = bool(cfg["already_in_use"])
    ctx["periodic_review_months"] = cfg["periodic_review_months"]
    for var, nn, _title in SHARED_DOCS:
        token = LITE_SHARED_NN.get(var, nn) if profile == "lite" else nn
        ctx[var] = format_doc_id(cfg["doc_id_pattern"], cfg["org_code"],
                                 SHARED_TOOL_TOKEN, token)
    tools = [derive_tool(t, cfg, profile) for t in cfg["tools"]]
    ctx["tools_list"] = tools
    ctx["tools"] = tools
    return ctx
