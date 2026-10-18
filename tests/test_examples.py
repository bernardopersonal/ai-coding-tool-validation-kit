"""Checks of the fictional filled example in examples/acme-medsoft/."""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))

from kit.config import load_config  # noqa: E402
from kit.package import render_package  # noqa: E402
from test_templates import HARDCODED_MODEL_RE, TEMPLATES_DIR  # noqa: E402

EXAMPLE = REPO / "examples" / "acme-medsoft"
CONFIG = EXAMPLE / "kit.config.json"
PACKAGE = EXAMPLE / "package"
BANNER = "> FICTIONAL EXAMPLE - not a real validation record."
GENERIC_NOTE = "Complete every `[fill in]`"


def example_files():
    return sorted(p for p in EXAMPLE.rglob("*") if p.is_file())


class ExampleTest(unittest.TestCase):
    def test_config_is_valid_and_frozen(self):
        cfg = load_config(CONFIG)
        self.assertEqual(cfg["today"], "2026-10-18")
        self.assertEqual(cfg["org_name"], "Acme MedSoft")
        self.assertIn("FICTIONAL EXAMPLE", json.loads(CONFIG.read_text(encoding="utf-8"))["_comment"])

    def test_package_has_the_rendered_file_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = render_package(load_config(CONFIG), TEMPLATES_DIR, tmp)
            expected = sorted(str(p.relative_to(tmp)).replace("\\", "/") for p in written)
        actual = sorted(str(p.relative_to(PACKAGE)).replace("\\", "/")
                        for p in PACKAGE.rglob("*.md"))
        self.assertEqual(actual, expected)

    def test_every_markdown_file_starts_with_the_banner(self):
        for path in example_files():
            if path.suffix == ".md":
                with self.subTest(file=str(path.relative_to(EXAMPLE))):
                    self.assertTrue(path.read_text(encoding="utf-8").startswith(BANNER))

    def test_no_tags_placeholders_or_real_model_names(self):
        for path in example_files():
            text = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(EXAMPLE))
            with self.subTest(file=rel):
                self.assertNotIn("{{", text)
                match = HARDCODED_MODEL_RE.search(text)
                self.assertIsNone(match, "%s names model %r; use placeholder ids" % (
                    rel, match.group(0) if match else ""))
                if path.parent != EXAMPLE:
                    leftovers = [line for line in text.splitlines()
                                 if "[fill in" in line and GENERIC_NOTE not in line]
                    self.assertEqual(leftovers, [], "unfilled placeholders in %s" % rel)

    def test_use_before_validation_has_a_nonconformity_reference(self):
        """A tool already in use needs a nonconformity reference in section 12 of its plan."""
        cfg = load_config(CONFIG)
        if not cfg.get("already_in_use"):
            self.skipTest("already_in_use is false")
        for tool in cfg["tools"]:
            plan = PACKAGE / tool["tool_id"] / "04-validation-plan.md"
            with self.subTest(tool=tool["tool_id"]):
                text = plan.read_text(encoding="utf-8")
                rows = [line for line in text.splitlines()
                        if line.startswith("| Nonconformity and CAPA (mandatory) |")]
                self.assertEqual(len(rows), 1, "section 12 has no nonconformity row in %s" % plan)
                match = re.search(r"NC ref:\s*([^;|]*)", rows[0])
                self.assertIsNotNone(match, "no 'NC ref:' in the nonconformity row of %s" % plan)
                ref = match.group(1).strip()
                self.assertNotEqual(ref, "", "empty NC reference in %s" % plan)
                self.assertFalse(ref.lower().startswith(("none", "n/a", "[fill in")),
                                 "NC reference %r is not a reference in %s" % (ref, plan))


if __name__ == "__main__":
    unittest.main()
