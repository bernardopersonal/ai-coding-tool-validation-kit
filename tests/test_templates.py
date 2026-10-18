"""Render EVERY template in templates/ across a matrix of configurations.

Catches, for any template added later:
  * syntax errors (unbalanced / malformed tags, unsupported syntax);
  * unknown variable or section names, in every branch (static check);
  * leftover '{{' in the output, 3+ blank lines, missing final newline;
  * hard-coded model ids and de-identification violations in templates.

Failures are de-duplicated and reported as one readable list.
"""

import itertools
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kit.config import (CONTEXT_KEYS, SURFACE_KEYS, TOOL_KEYS, default_config,  # noqa: E402
                        derive, validate_config)
from kit.package import (SHARED_DIR, discover_templates, is_shared, output_name,  # noqa: E402
                         render_package)
from kit.render import RenderError, Template  # noqa: E402

TEMPLATES_DIR = REPO / "templates"
TEMPLATE_NAME_RE = re.compile(r"^\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md\.tmpl$")

# Example model ids used only by the test matrix (deliberately not real names).
MATRIX_MODELS = {
    "claude_code": ["vendor-a-large-*", "vendor-a-small-2"],
    "codex": ["vendor-b-code-*", "vendor-b-code-1"],
    "copilot": ["vendor-c-*"],
    "cursor": ["vendor-d-fast", "vendor-d-*"],
    "other": ["vendor-e-1"],
}
PINNED = {"claude_code": "vendor-a-small-2", "codex": "vendor-b-code-1",
          "copilot": "vendor-c-7", "cursor": "vendor-d-fast", "other": "vendor-e-1"}
SURFACE_SETS = [list(SURFACE_KEYS), ["local_cli_ide"], ["cloud_agent", "pr_review_bot"],
                ["ci_headless"], ["local_cli_ide", "ci_headless"]]
CONTEXT_SETS = {"all": list(CONTEXT_KEYS), "code_product": ["code_product"],
                "doc_drafting": ["doc_drafting"]}


def make_tool(key, index, policy):
    return {
        "tool_key": key,
        "tool_name": "Tool %s" % key,
        "tool_id": "T%d%s" % (index, key.upper().replace("_", "")[:6]),
        "vendor": "Vendor %d" % index,
        "surfaces": SURFACE_SETS[index % len(SURFACE_SETS)],
        "approved_models": MATRIX_MODELS[key],
        "model_policy": policy,
        "pinned_model": PINNED[key] if policy == "pinned" else "",
    }


def build_matrix():
    """[(label, config)] covering the option space.

    Full cartesian product of risk model x contexts x already_in_use x regs/GxP
    x model policy x code host; every config carries one tool of EACH type
    (so per-tool templates render for every tool type in every combination).
    Plus single-tool configs (one per type) and a mixed-policy config.
    """
    matrix = []
    for risk, ctx_name, in_use, gxp, policy, host in itertools.product(
            ("csa", "three_level"), list(CONTEXT_SETS), (True, False), (True, False),
            ("envelope", "pinned"), ("github", "gitlab", "other")):
        cfg = default_config()
        cfg.update(
            risk_model=risk, contexts=CONTEXT_SETS[ctx_name], already_in_use=in_use,
            reg_gxp=gxp, reg_iso13485=True, reg_fda_qmsr=gxp, reg_iso27001=gxp,
            reg_iso42001=gxp, role_prrc="Regulatory Affairs Manager" if gxp else "",
            code_host=host, periodic_review_months=6 if ctx_name == "all" else 12,
            tools=[make_tool(k, i, policy) for i, k in enumerate(TOOL_KEYS)])
        label = "risk=%s ctx=%s in_use=%s gxp=%s policy=%s host=%s" % (
            risk, ctx_name, in_use, gxp, policy, host)
        matrix.append((label, cfg))
    for i, key in enumerate(TOOL_KEYS):
        for policy in ("envelope", "pinned"):
            cfg = default_config()
            cfg["tools"] = [make_tool(key, i, policy)]
            matrix.append(("single tool=%s policy=%s" % (key, policy), cfg))
    cfg = default_config()
    cfg["tools"] = [make_tool(k, i, "pinned" if i % 2 else "envelope")
                    for i, k in enumerate(TOOL_KEYS)]
    cfg["reg_iso13485"] = cfg["reg_fda_qmsr"] = False
    matrix.append(("mixed policies, no ISO 13485/QMSR flags", cfg))
    matrix.append(("default config", default_config()))
    return matrix


def template_paths():
    return discover_templates(TEMPLATES_DIR)


class TemplateFilesTest(unittest.TestCase):
    def test_templates_exist(self):
        paths = template_paths()
        self.assertTrue(paths, "no templates found in templates/")
        self.assertTrue(any(is_shared(p) for p in paths), "no shared 00-*.md.tmpl template")
        self.assertTrue(any(not is_shared(p) for p in paths), "no per-tool template")

    def test_template_names(self):
        for path in TEMPLATES_DIR.iterdir():
            if path.name.endswith(".tmpl"):
                with self.subTest(template=path.name):
                    self.assertRegex(path.name, TEMPLATE_NAME_RE,
                                     "template names must be NN-lowercase-words.md.tmpl")

    def test_output_names_unique(self):
        names = [(is_shared(p), output_name(p)) for p in template_paths()]
        self.assertEqual(len(names), len(set(names)))

    def test_all_templates_parse(self):
        for path in template_paths():
            with self.subTest(template=path.name):
                try:
                    Template.from_file(path)
                except RenderError as exc:
                    self.fail(str(exc))


class TemplateMatrixTest(unittest.TestCase):
    MAX_REPORTED = 25

    @classmethod
    def setUpClass(cls):
        cls.templates = []
        cls.parse_errors = []
        for path in template_paths():
            try:
                cls.templates.append(Template.from_file(path))
            except RenderError as exc:
                cls.parse_errors.append(str(exc))

    def test_matrix_configs_are_valid(self):
        for label, cfg in build_matrix():
            with self.subTest(config=label):
                self.assertEqual(validate_config(cfg), [])

    def test_render_all_templates_across_matrix(self):
        if self.parse_errors:
            self.fail("templates do not parse:\n  " + "\n  ".join(self.parse_errors))
        failures = {}  # (template, message) -> first config label
        renders = 0
        for label, cfg in build_matrix():
            ctx = derive(cfg, today="2026-01-15")
            for tpl in self.templates:
                stacks = [("shared", [ctx])] if is_shared(tpl.path) else [
                    (tool["tool_id"], [ctx, tool]) for tool in ctx["tools_list"]]
                for where, stack in stacks:
                    renders += 1
                    try:
                        out = tpl.render(stack)
                    except RenderError as exc:
                        failures.setdefault((tpl.path, str(exc)), "%s [%s]" % (label, where))
                        continue
                    for problem in self._output_problems(out):
                        failures.setdefault((tpl.path, problem), "%s [%s]" % (label, where))
        if failures:
            lines = ["%s\n      first seen with: %s" % (msg if msg.startswith(path) else
                                                         "%s: %s" % (path, msg), where)
                     for (path, msg), where in list(failures.items())[:self.MAX_REPORTED]]
            self.fail("%d distinct template problem(s) in %d renders:\n  - %s" % (
                len(failures), renders, "\n  - ".join(lines)))

    @staticmethod
    def _output_problems(out):
        problems = []
        if "{{" in out:
            problems.append("leftover '{{' in output")
        if re.search(r"\n[ \t]*\n[ \t]*\n[ \t]*\n", out):
            problems.append("3+ consecutive blank lines in output")
        if out and not out.endswith("\n"):
            problems.append("output does not end with a newline")
        if not out.strip():
            problems.append("output is empty")
        return problems

    def test_package_layout_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = render_package(default_config(), TEMPLATES_DIR, tmp, today="2026-01-15")
            rel = sorted(str(p.relative_to(tmp)).replace("\\", "/") for p in written)
            shared = [output_name(p) for p in template_paths() if is_shared(p)]
            per_tool = [output_name(p) for p in template_paths() if not is_shared(p)]
            expected = sorted(["%s/%s" % (SHARED_DIR, n) for n in shared] +
                              ["%s/%s" % (t, n) for t in ("CLAUDE", "CODEX") for n in per_tool])
            self.assertEqual(rel, expected)


# --------------------------------------------------------------------------
# Content hygiene (spec: vendor-agnostic templates, de-identification rules)
# --------------------------------------------------------------------------

# Model names must come from approved_models, never from template text.
HARDCODED_MODEL_RE = re.compile(
    r"(?i)\b(claude-(?:opus|sonnet|haiku|fable|instant)[\w.*-]*|"
    r"(?:claude|opus|sonnet|haiku|fable)\s+\d+(?:\.\d+)?|"
    r"gpt-?\d[\w.*-]*|codex-mini[\w.-]*|o[134]-(?:mini|pro|preview)[\w.-]*|"
    r"gemini-[\w.-]+)\b")

# De-identification: no internal document codes; patterns kept outside the repository.
# One regular expression per line ('#' starts a comment), read from the file named by
# $KIT_DEID_PATTERNS or from tests/deid-local.txt (git-ignored, never committed or packaged).
FORBIDDEN_RE = []
_LOCAL = Path(os.environ.get("KIT_DEID_PATTERNS") or (REPO / "tests" / "deid-local.txt"))
if _LOCAL.is_file():
    FORBIDDEN_RE += [re.compile(line.strip()) for line in
                     _LOCAL.read_text(encoding="utf-8").splitlines()
                     if line.strip() and not line.lstrip().startswith("#")]
SCANNED_SUFFIXES = {".md", ".tmpl", ".py", ".json", ".toml", ".yml", ".yaml", ".sh", ".txt",
                    ".cfg", ".ini"}
SKIPPED_DIRS = {".git", "tests", "__pycache__", "output", "node_modules", ".venv"}


class TemplateHygieneTest(unittest.TestCase):
    def test_no_hardcoded_model_ids_in_templates(self):
        for path in template_paths():
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                match = HARDCODED_MODEL_RE.search(line)
                with self.subTest(template=path.name, line=lineno):
                    self.assertIsNone(
                        match, "%s:%d hard-codes model %r; use {{#approved_models}}{{.}}"
                               "{{/approved_models}} or {{pinned_model}}" % (
                                   path.name, lineno, match.group(0) if match else ""))


class RepoDeidentificationTest(unittest.TestCase):
    @unittest.skipUnless(FORBIDDEN_RE, "no local de-identification patterns: set "
                         "KIT_DEID_PATTERNS or create tests/deid-local.txt (not committed)")
    def test_no_forbidden_identifiers_in_repo(self):
        hits = []
        for path in sorted(REPO.rglob("*")):
            if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
                continue
            if set(path.relative_to(REPO).parts[:-1]) & SKIPPED_DIRS:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), start=1):
                for pattern in FORBIDDEN_RE:
                    if pattern.search(line):
                        hits.append("%s:%d: %r matches %s" % (
                            path.relative_to(REPO), lineno, line.strip()[:80], pattern.pattern))
        self.assertEqual(hits, [], "de-identification rule violated:\n  " + "\n  ".join(hits))


if __name__ == "__main__":
    unittest.main()
