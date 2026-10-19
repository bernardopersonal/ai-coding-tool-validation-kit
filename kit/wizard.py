"""Interactive questionnaire that produces a kit config (dict).

Every question shows its default in brackets; pressing Enter accepts it.
Multi-select questions take comma-separated keys (or option numbers).
``python3 kit.py init --defaults`` skips the wizard entirely.

The I/O functions are injectable (``input_fn`` / ``print_fn``) for tests.
"""

from __future__ import annotations

import copy
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .config import (CODE_HOSTS, CONTEXTS, DEFAULT_CONFIG, LITE_STOP_KEYS, MODEL_POLICIES,
                     PROFILE_KEYS, PROFILES, REGULATIONS, RISK_MODELS, SURFACES, TOOL_TYPES,
                     check_doc_id_pattern, check_model, check_org_code, check_pinned_model,
                     check_text, check_tool_id, config_profile, full_profile_reasons,
                     is_pattern, lite_blockers, validate_config)

MAX_ATTEMPTS = 10
NONE_TOKEN = "-"

Validator = Callable[[str], Optional[str]]


class WizardAbort(Exception):
    """The user aborted, input ended, or too many invalid answers."""


class _IO:
    def __init__(self, input_fn: Callable[[str], str], print_fn: Callable[..., None]) -> None:
        self._input = input_fn
        self.print = print_fn

    def input(self, prompt: str) -> str:
        try:
            return self._input(prompt)
        except EOFError:
            raise WizardAbort("input ended before the questionnaire was complete")
        except KeyboardInterrupt:
            raise WizardAbort("interrupted")


def _prompt(label: str, default_display: Optional[str]) -> str:
    if default_display is None or default_display == "":
        return "%s: " % label
    return "%s [%s]: " % (label, default_display)


def _loop(io: _IO, prompt: str, parse: Callable[[str], Tuple[Any, Optional[str]]]) -> Any:
    for _ in range(MAX_ATTEMPTS):
        raw = io.input(prompt).strip()
        value, err = parse(raw)
        if err is None:
            return value
        io.print("  ! " + err)
    raise WizardAbort("too many invalid answers for: " + prompt.strip())


def ask_text(io: _IO, label: str, default: str, validate: Optional[Validator] = None,
             optional: bool = False, transform: Callable[[str], str] = lambda s: s) -> str:
    """Free text. ``optional`` allows an empty answer via '-' (shown as 'none')."""
    shown = default if default else ("none" if optional else None)
    if optional:
        label = "%s (enter %s for none)" % (label, NONE_TOKEN)

    def parse(raw: str) -> Tuple[Any, Optional[str]]:
        if raw == "":
            value = default
        elif optional and raw == NONE_TOKEN:
            value = ""
        else:
            value = transform(raw)
        if value == "" and not optional:
            return None, "a value is required"
        return value, (validate(value) if validate and value != "" else None)

    return _loop(io, _prompt(label, shown), parse)


def ask_bool(io: _IO, label: str, default: bool) -> bool:
    def parse(raw: str) -> Tuple[Any, Optional[str]]:
        if raw == "":
            return default, None
        low = raw.lower()
        if low in ("y", "yes", "true", "1"):
            return True, None
        if low in ("n", "no", "false", "0"):
            return False, None
        return None, "answer yes or no"

    return _loop(io, _prompt(label, "yes" if default else "no"), parse)


def ask_int(io: _IO, label: str, default: int, lo: int, hi: int) -> int:
    def parse(raw: str) -> Tuple[Any, Optional[str]]:
        if raw == "":
            return default, None
        try:
            value = int(raw)
        except ValueError:
            return None, "enter a whole number"
        if not lo <= value <= hi:
            return None, "enter a number between %d and %d" % (lo, hi)
        return value, None

    return _loop(io, _prompt(label, str(default)), parse)


def _show_options(io: _IO, title: str, options: Sequence[Tuple[str, str]]) -> None:
    io.print(title)
    width = max(len(k) for k, _ in options)
    for i, (key, desc) in enumerate(options, start=1):
        io.print("  %d. %s  %s" % (i, key.ljust(width), desc))


def _resolve_key(token: str, keys: List[str]) -> Optional[str]:
    if token in keys:
        return token
    if token.isdigit() and 1 <= int(token) <= len(keys):
        return keys[int(token) - 1]
    return None


def ask_choice(io: _IO, title: str, options: Sequence[Tuple[str, str]], default: str) -> str:
    keys = [k for k, _ in options]
    _show_options(io, title, options)

    def parse(raw: str) -> Tuple[Any, Optional[str]]:
        if raw == "":
            return default, None
        key = _resolve_key(raw, keys)
        if key is None:
            return None, "choose one of: " + ", ".join(keys)
        return key, None

    return _loop(io, _prompt("Choice", default), parse)


def ask_multi(io: _IO, title: str, options: Sequence[Tuple[str, str]], default: List[str],
              min_count: int = 1) -> List[str]:
    keys = [k for k, _ in options]
    _show_options(io, title, options)

    def parse(raw: str) -> Tuple[Any, Optional[str]]:
        if raw == "":
            chosen = list(default)
        elif raw == NONE_TOKEN and min_count == 0:
            chosen = []
        else:
            chosen = []
            for token in [t.strip() for t in raw.split(",") if t.strip()]:
                key = _resolve_key(token, keys)
                if key is None:
                    return None, "unknown option '%s'; choose from: %s" % (
                        token, ", ".join(keys))
                if key not in chosen:
                    chosen.append(key)
        if len(chosen) < min_count:
            return None, "select at least %d option(s)" % min_count
        return [k for k in keys if k in chosen], None  # canonical order

    label = "Selection (comma-separated%s)" % (
        ", %s for none" % NONE_TOKEN if min_count == 0 else "")
    return _loop(io, _prompt(label, ",".join(default)), parse)


def ask_list(io: _IO, label: str, default: List[str], validate_item: Validator) -> List[str]:
    def parse(raw: str) -> Tuple[Any, Optional[str]]:
        items = list(default) if raw == "" else [t.strip() for t in raw.split(",") if t.strip()]
        if not items:
            return None, "enter at least one value"
        seen: List[str] = []
        for item in items:
            err = validate_item(item)
            if err:
                return None, err
            if item not in seen:
                seen.append(item)
        return seen, None

    return _loop(io, _prompt(label, ", ".join(default)), parse)


# --------------------------------------------------------------------------

def _ask_tool(io: _IO, index: int, total: int, base: Optional[Dict[str, Any]],
              used_ids: List[str]) -> Dict[str, Any]:
    io.print("")
    io.print("--- Tool %d of %d ---" % (index + 1, total))
    type_options = [(k, v["label"]) for k, v in TOOL_TYPES.items()]
    key = ask_choice(io, "Tool type:", type_options, base["tool_key"] if base else "other")
    src = copy.deepcopy(base) if base and base.get("tool_key") == key else {
        "tool_name": TOOL_TYPES[key]["tool_name"], "tool_id": TOOL_TYPES[key]["tool_id"],
        "vendor": TOOL_TYPES[key]["vendor"], "surfaces": list(TOOL_TYPES[key]["surfaces"]),
        "approved_models": list(TOOL_TYPES[key]["approved_models"]),
        "model_policy": "envelope", "pinned_model": ""}
    if src["tool_id"] in used_ids:
        src["tool_id"] = ""
    tool: Dict[str, Any] = {"tool_key": key}
    tool["tool_name"] = ask_text(io, "Tool name", src["tool_name"],
                                 lambda v: check_text(v, "tool name", max_len=80))
    tool["tool_id"] = ask_text(io, "Tool ID code (doc IDs and output folder, e.g. CLAUDE)",
                               src["tool_id"], lambda v: check_tool_id(v, used_ids),
                               transform=lambda s: s.upper())
    tool["vendor"] = ask_text(io, "Vendor", src["vendor"],
                              lambda v: check_text(v, "vendor", max_len=80))
    tool["surfaces"] = ask_multi(io, "Surfaces in use:", SURFACES, src["surfaces"])
    io.print("Approved models: the envelope of model ids or family patterns allowed for "
             "this tool (e.g. vendor-family-*). The defaults are placeholders: take the ids from "
             "the vendor's current release notes. Each model is admitted with MA-01.")
    tool["approved_models"] = ask_list(io, "Approved models (comma-separated)",
                                       src["approved_models"], check_model)
    tool["model_policy"] = ask_choice(io, "Model policy:", MODEL_POLICIES,
                                      src.get("model_policy", "envelope"))
    tool["pinned_model"] = ""
    if tool["model_policy"] == "pinned":
        default_pin = src.get("pinned_model", "")
        if not default_pin or check_pinned_model(default_pin, tool["approved_models"]):
            exact = [m for m in tool["approved_models"] if not is_pattern(m)]
            default_pin = exact[0] if exact else ""
        tool["pinned_model"] = ask_text(
            io, "Pinned model id (exact id inside the approved envelope)", default_pin,
            lambda v: check_pinned_model(v, tool["approved_models"]))
    return tool


# Triggers for the full profile that cannot be read from the answers (L5 to L7).
FULL_TRIGGERS_NOT_IN_ANSWERS = (
    "a CSA \"high process risk\" determination for any intended use (L5)",
    "a notified body, the FDA or a customer expects more depth (L6)",
    "previous audit findings on the tool (L7)",
)


def _ask_lite_stops(io: _IO, cfg: Dict[str, Any], d: Dict[str, Any]) -> None:
    """The yes/no answers behind the hard stops L2 (write path), L8 and L9."""
    io.print("")
    io.print("Hard stops for the lite profile: a 'yes' requires the full profile.")
    contexts = cfg["contexts"]
    surfaces = {s for t in cfg["tools"] for s in t["surfaces"]}
    hints = {
        "ai_output_as_evidence": "test_generation" in contexts or "code_tooling" in contexts,
        "agent_untrusted_with_secrets": bool(surfaces & {"cloud_agent", "pr_review_bot",
                                                         "ci_headless"}),
    }
    for key, question, number in LITE_STOP_KEYS:
        if hints.get(key):
            io.print("Hint: your contexts or surfaces make %s relevant; answer it carefully."
                     % number)
        cfg[key] = ask_bool(io, "%s %s" % (number, question), bool(d.get(key, False)))


def _ask_profile(io: _IO, cfg: Dict[str, Any], previous: Optional[str],
                 override: Optional[str]) -> str:
    """Show the recommendation and its reasons, then ask (default: the recommendation).

    A ``full`` choice in an existing config stays the default, because the
    reasons for it may not be visible in the answers. ``override`` (from
    ``--profile``) is used without asking.
    """
    reasons = full_profile_reasons(cfg)
    blocked = bool(lite_blockers(cfg))
    recommended = "full" if reasons else "lite"
    io.print("")
    io.print("Validation profile. Recommended for these answers: %s." % recommended)
    if reasons:
        io.print("The full profile is %s because:" % ("required" if blocked else "recommended"))
        for reason in reasons:
            io.print("  - " + reason)
    else:
        io.print("No trigger for the full profile in the answers: lite fits teams where the AI "
                 "output is always independently verified downstream (human review + CI).")
    io.print("Choose full in any case if: " + "; ".join(FULL_TRIGGERS_NOT_IN_ANSWERS) + ".")
    if override is not None:
        io.print("Profile: %s (set with --profile)." % override)
        if override == "lite" and blocked:
            io.print("  ! lite is not available with a hard stop: 'render' refuses it unless "
                     "--force, and then marks it NOT VALID FOR RELEASE.")
        elif override == "lite" and reasons:
            io.print("  ! lite was chosen although full is recommended; the lite validation "
                     "plan shows a warning with the reasons.")
        return override
    if blocked:
        io.print("Profile: full (lite is not available with a hard stop).")
        return "full"
    default = recommended
    if previous == "full" and recommended == "lite":
        default = "full"
        io.print("Keeping full from the existing config as the default.")
    choice = ask_choice(io, "Profile:", PROFILES, default)
    if choice == "lite" and reasons:
        io.print("  ! lite chosen although full is recommended; the lite validation plan shows "
                 "a warning with the reasons.")
    return choice


def run_wizard(defaults: Optional[Dict[str, Any]] = None,
               input_fn: Callable[[str], str] = input,
               print_fn: Callable[..., None] = print,
               profile: Optional[str] = None) -> Dict[str, Any]:
    """Ask every question and return a validated config dict.

    The profile is asked last, after the answers that decide whether the full
    profile is recommended; ``profile`` (``--profile``) skips that question.
    """
    if profile is not None and profile not in PROFILE_KEYS:
        raise WizardAbort("profile must be one of: " + ", ".join(PROFILE_KEYS))
    d = copy.deepcopy(defaults if defaults is not None else DEFAULT_CONFIG)
    io = _IO(input_fn, print_fn)
    io.print("AI Coding Tool Validation Kit - configuration wizard")
    io.print("Press Enter to accept the [default]. Validate the intended use and the "
             "guardrails around the tool; do not try to qualify the LLM.")
    io.print("")

    cfg: Dict[str, Any] = {}
    cfg["org_name"] = ask_text(io, "Organisation name", d["org_name"],
                               lambda v: check_text(v, "organisation name", max_len=120))
    cfg["org_code"] = ask_text(io, "Organisation code (used in document IDs)", d["org_code"],
                               check_org_code)
    cfg["doc_id_pattern"] = ask_text(io, "Document ID pattern (tokens {org}, {tool}, {nn})",
                                     d["doc_id_pattern"], check_doc_id_pattern)
    cfg["product_context"] = ask_text(io, "Product / regulatory context",
                                      d["product_context"],
                                      lambda v: check_text(v, "product context"))
    reg_options = [(wkey, label) for _, wkey, label in REGULATIONS]
    reg_default = [wkey for key, wkey, _ in REGULATIONS if d.get(key)]
    regs = ask_multi(io, "Regulatory frameworks in scope:", reg_options, reg_default,
                     min_count=0)
    for key, wkey, _ in REGULATIONS:
        cfg[key] = wkey in regs

    io.print("")
    cfg["role_executor"] = ask_text(io, "Role executing the validation", d["role_executor"],
                                    lambda v: check_text(v, "role", max_len=80))
    executor = cfg["role_executor"]

    def check_approver(v: str) -> Optional[str]:
        if v.strip().casefold() == executor.strip().casefold():
            return "the approver must be a different role from the executor"
        return check_text(v, "role", max_len=80)

    approver_default = d["role_approver"]
    if approver_default.strip().casefold() == executor.strip().casefold():
        approver_default = ""
    cfg["role_approver"] = ask_text(io, "Role approving the validation", approver_default,
                                    check_approver)
    cfg["role_tool_owner"] = ask_text(io, "Tool owner role", d["role_tool_owner"],
                                      lambda v: check_text(v, "role", max_len=80))
    cfg["role_prrc"] = ask_text(io, "PRRC (person responsible for regulatory compliance)",
                                d.get("role_prrc", ""),
                                lambda v: check_text(v, "PRRC", max_len=80), optional=True)

    io.print("")
    cfg["code_host"] = ask_choice(io, "Git hosting platform:", CODE_HOSTS, d["code_host"])
    cfg["contexts"] = ask_multi(io, "Contexts of use:", [(k, label) for k, label, _ in CONTEXTS],
                                d["contexts"])
    cfg["risk_model"] = ask_choice(io, "Risk model:", RISK_MODELS, d["risk_model"])
    cfg["already_in_use"] = ask_bool(io, "Are the tools already in use (retrospective "
                                         "validation + interim-use justification)?",
                                     d["already_in_use"])
    months = d["periodic_review_months"]
    if "agents_qms" in cfg["contexts"] and months > 6:
        io.print("Hint: 6 months is recommended when agents_qms is in scope.")
        months = 6
    elif "code_product" in cfg["contexts"] and months > 6:
        io.print("Hint: consider 6 months if product code is high risk.")
    cfg["periodic_review_months"] = ask_int(io, "Periodic review interval (months)", months,
                                            1, 36)

    io.print("")
    base_tools = d.get("tools") or []
    count = ask_int(io, "Number of AI coding tools to validate", max(len(base_tools), 1), 1, 10)
    tools: List[Dict[str, Any]] = []
    for i in range(count):
        base = base_tools[i] if i < len(base_tools) else None
        tool = _ask_tool(io, i, count, base, [t["tool_id"] for t in tools])
        tools.append(tool)
    cfg["tools"] = tools
    _ask_lite_stops(io, cfg, d)
    # An existing config without the key (kit 0.1.0) rendered as full.
    previous = config_profile(defaults) if defaults is not None else None
    cfg["profile"] = _ask_profile(io, cfg, previous, profile)
    if d.get("today"):
        cfg["today"] = d["today"]

    errors = validate_config(cfg)
    if errors:  # defensive: every answer was validated individually
        raise WizardAbort("the answers do not form a valid config:\n  - " +
                          "\n  - ".join(errors))
    io.print("")
    io.print("Summary: %s (%s); tools: %s; contexts: %s; risk model: %s; profile: %s." % (
        cfg["org_name"], cfg["org_code"],
        ", ".join("%s [%s]" % (t["tool_name"], t["tool_id"]) for t in tools),
        ", ".join(cfg["contexts"]), cfg["risk_model"], cfg["profile"]))
    return cfg


def confirm(prompt: str, default: bool = True, input_fn: Callable[[str], str] = input,
            print_fn: Callable[..., None] = print) -> bool:
    return ask_bool(_IO(input_fn, print_fn), prompt, default)
