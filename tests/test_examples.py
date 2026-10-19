"""Checks of the fictional filled examples.

* examples/acme-medsoft/       the full profile (templates/full/);
* examples/acme-medsoft-lite/  the lite profile (templates/lite/).

Both: valid frozen config, the rendered file set, the banner on every Markdown
file, no leftover template syntax or placeholders, no real model names, and a
nonconformity reference for use before validation when the tool is already in
use.
"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))

from kit.config import full_profile_reasons, load_config  # noqa: E402
from kit.package import render_package  # noqa: E402
from test_templates import HARDCODED_MODEL_RE, LITE_TEMPLATES_DIR, TEMPLATES_DIR  # noqa: E402

BANNER = "> FICTIONAL EXAMPLE - not a real validation record."
NC_ROW = "| Nonconformity and CAPA (mandatory) |"
FULL_WARNING = "WARNING: the full profile is recommended"


def first_heading(path):
    """First line of ``path`` that starts with "# " (the document ID and title)."""
    return next((line for line in Path(path).read_text(encoding="utf-8").splitlines()
                 if line.startswith("# ")), None)


class ExampleChecks:
    """Shared checks; subclasses set EXAMPLE, PROFILE, TEMPLATES, TODAY, PLACEHOLDERS, PLAN."""

    EXAMPLE = None          # example directory
    PROFILE = None          # "full" or "lite"
    TEMPLATES = None        # templates directory of the profile
    TODAY = None            # frozen render date in the config
    # Placeholder markers that must not survive in a filled document, each with
    # the generated note that names it (that line is allowed), or None.
    PLACEHOLDERS = {}
    PLAN = None             # per-tool document holding the interim-use block

    @property
    def config_path(self):
        return self.EXAMPLE / "kit.config.json"

    @property
    def package(self):
        return self.EXAMPLE / "package"

    def example_files(self):
        return sorted(p for p in self.EXAMPLE.rglob("*") if p.is_file())

    def test_config_is_valid_and_frozen(self):
        cfg = load_config(self.config_path)
        self.assertEqual(cfg["today"], self.TODAY)
        self.assertEqual(cfg["org_name"], "Acme MedSoft")
        self.assertEqual(cfg["profile"], self.PROFILE,
                         "%s is the %s-profile example" % (self.EXAMPLE.name, self.PROFILE))
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertIn("FICTIONAL EXAMPLE", raw["_comment"])

    def test_package_has_the_rendered_file_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = render_package(load_config(self.config_path), self.TEMPLATES, tmp,
                                     profile=self.PROFILE)
            expected = sorted(str(p.relative_to(tmp)).replace("\\", "/") for p in written)
            actual = sorted(str(p.relative_to(self.package)).replace("\\", "/")
                            for p in self.package.rglob("*.md"))
            self.assertEqual(actual, expected)
            # Same document ID and title as the kit renders today (catches a stale
            # example after a change of a document number token).
            for rel in expected:
                with self.subTest(document=rel):
                    rendered = first_heading(Path(tmp) / rel)
                    self.assertIsNotNone(rendered, "%s has no '# ' heading" % rel)
                    self.assertEqual(first_heading(self.package / rel), rendered)

    def test_every_markdown_file_starts_with_the_banner(self):
        for path in self.example_files():
            if path.suffix == ".md":
                with self.subTest(file=str(path.relative_to(self.EXAMPLE))):
                    self.assertTrue(path.read_text(encoding="utf-8").startswith(BANNER))

    def test_no_tags_placeholders_or_real_model_names(self):
        for path in self.example_files():
            text = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(self.EXAMPLE))
            with self.subTest(file=rel):
                self.assertNotIn("{{", text, "leftover template syntax in %s" % rel)
                self.assertNotIn("}}", text, "leftover template syntax in %s" % rel)
                match = HARDCODED_MODEL_RE.search(text)
                self.assertIsNone(match, "%s names model %r; use placeholder ids" % (
                    rel, match.group(0) if match else ""))
                if path.parent == self.EXAMPLE:
                    continue  # README and config describe the placeholders
                for marker, note in self.PLACEHOLDERS.items():
                    leftovers = [line for line in text.splitlines()
                                 if marker in line and not (note and note in line)]
                    self.assertEqual(leftovers, [], "unfilled %r in %s" % (marker, rel))

    def test_use_before_validation_has_a_nonconformity_reference(self):
        """A tool already in use needs a nonconformity reference in the interim-use block."""
        cfg = load_config(self.config_path)
        if not cfg.get("already_in_use"):
            self.skipTest("already_in_use is false")
        for tool in cfg["tools"]:
            plan = self.package / tool["tool_id"] / self.PLAN
            with self.subTest(tool=tool["tool_id"]):
                text = plan.read_text(encoding="utf-8")
                rows = [line for line in text.splitlines() if line.startswith(NC_ROW)]
                self.assertEqual(len(rows), 1, "no nonconformity row in %s" % plan)
                match = re.search(r"NC ref:\s*([^;|]*)", rows[0])
                self.assertIsNotNone(match, "no 'NC ref:' in the nonconformity row of %s" % plan)
                ref = match.group(1).strip()
                self.assertNotEqual(ref, "", "empty NC reference in %s" % plan)
                self.assertFalse(ref.lower().startswith(("none", "n/a", "[fill in", "___")),
                                 "NC reference %r is not a reference in %s" % (ref, plan))


class FullExampleTest(ExampleChecks, unittest.TestCase):
    EXAMPLE = REPO / "examples" / "acme-medsoft"
    PROFILE = "full"
    TEMPLATES = TEMPLATES_DIR
    TODAY = "2026-10-18"
    PLACEHOLDERS = {"[fill in": "Complete every `[fill in]`"}
    PLAN = "04-validation-plan.md"   # section 12 Interim-use justification


class LiteExampleTest(ExampleChecks, unittest.TestCase):
    EXAMPLE = REPO / "examples" / "acme-medsoft-lite"
    PROFILE = "lite"
    TEMPLATES = LITE_TEMPLATES_DIR
    TODAY = "2026-10-19"
    PLACEHOLDERS = {"[fill in": "Complete every `[fill in]`",
                    "______": "Complete every `______`",
                    "[yes/no": None, "[lite / full]": None}
    PLAN = "01-validation-plan.md"   # section 9 Interim use

    def test_profile_decision_matches_the_answers(self):
        """Lite example without triggers: no full-profile warning, every L1-L9 answered."""
        cfg = load_config(self.config_path)
        self.assertEqual(full_profile_reasons(cfg), [],
                         "the lite example's answers should not call for the full profile")
        for tool in cfg["tools"]:
            text = (self.package / tool["tool_id"] / self.PLAN).read_text(encoding="utf-8")
            with self.subTest(tool=tool["tool_id"]):
                self.assertNotIn(FULL_WARNING, text)
                self.assertNotIn("NOT VALID FOR RELEASE", text)
                rows = [line for line in text.splitlines() if re.match(r"\| L[1-9] \|", line)]
                self.assertEqual(len(rows), 9, "plan section 2 must list L1 to L9")
                for row in rows:
                    self.assertRegex(row.rsplit("|", 2)[-2].strip(), r"^(no|\*\*yes\*\*|yes)\b",
                                     "unanswered condition: %s" % row)


if __name__ == "__main__":
    unittest.main()
