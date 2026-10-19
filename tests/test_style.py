"""Style rules of the kit owner, enforced on the repository and on rendered packages.

* no section sign in any tracked text file, nor in the rendered default packages:
  clauses are cited as "ISO 13485:2016 clause 4.1.6", "21 CFR 820.10",
  "MDR Article 10(8)", "section 3 of this plan";
* README.md states no times or durations at all;
* GUIDE.md and docs/*.md make no effort or speed claims (minimum observation
  periods and review cadences that are acceptance criteria may stay);
* README.md and GUIDE.md carry the "shadow AI" message, and GUIDE.md stays within
  its word budget;
* the work instruction of both profiles has an explicit "No shadow AI" rule;
* lite and full document IDs never collide for the default config, so an ID always
  names one document when a team upgrades from lite to full.
"""

import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kit.config import LITE_TOOL_DOCS, SHARED_DOCS, TOOL_DOCS, default_config, derive  # noqa: E402
from kit.package import SHARED_DIR, load_templates, profile_templates_dir, render_all  # noqa: E402

SECTION_SIGN = chr(0xA7)   # written as a code point: this file follows its own rule
GUIDE_BUDGET = 1250   # whitespace-separated tokens, as the lite word budget
SKIP_DIRS = {".git", "__pycache__"}

NUMBER = (r"(?:\d+(?:[.,]\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
          r"twelve|fifteen|twenty|thirty|forty|sixty|ninety|a\s+few|few|several|"
          r"a\s+couple\s+of|couple\s+of|half\s+an?|an?)")
RANGE = r"(?:\s*(?:-|–|to|or)\s*" + NUMBER + r")?"
QUALIFIER = r"(?:\s+(?:more|working|business|calendar|full))?"
UNITS = r"(?:seconds?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?)"
DURATION_RE = re.compile(r"\b" + NUMBER + RANGE + QUALIFIER + r"[\s-]+" + UNITS + r"\b", re.I)
# "a second vendor" or "GAMP 5 Second Edition" are ordinals, not durations ("1 second",
# "one second" and "5-second" are durations).
ORDINAL_SECOND_RE = re.compile(r"^(?!(?:1|one)\s).*\ssecond$", re.I)
README_TIME_PHRASES = [
    re.compile(p, re.I) for p in (
        r"\bquick start in\b", r"\bminutes of reading\b", r"\bhours, not weeks\b",
        r"\b(?:seconds|minutes|hours|days|weeks|months|years)\b",
        r"\b(?:daily|weekly|monthly|yearly|annually|overnight)\b",
        r"\bin (?:about|under|less than) (?:a|an|one)\b",
    )]
EFFORT_PHRASES = ["minutes of reading", "in about a week", "1-2 days", "1–2 days",
                  "hours, not weeks", "in a week", "one week, not", "total effort",
                  "of people's time", "quick start in"]


def tracked_files():
    """Paths (relative to the repository) of the tracked and the new, not ignored files.

    Uses git when the repository is a git work tree; otherwise walks the tree
    without .git and __pycache__.
    """
    git = shutil.which("git")
    if git and (REPO / ".git").exists():
        try:
            out = subprocess.run(
                [git, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                cwd=str(REPO), capture_output=True, check=True).stdout
            names = sorted({n for n in out.decode("utf-8").split("\0") if n})
            return [n for n in names if (REPO / n).is_file()]
        except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
            pass
    names = []
    for root, dirs, files in os.walk(str(REPO)):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith(".pyc"):
                names.append(Path(root, name).relative_to(REPO).as_posix())
    return sorted(names)


def read_text_file(rel):
    """Text of a UTF-8 text file, or None for binary files."""
    data = (REPO / rel).read_bytes()
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def durations(text):
    """[(line number, expression)] of the duration expressions in ``text``."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        for match in DURATION_RE.finditer(line):
            if not ORDINAL_SECOND_RE.match(match.group(0)):
                found.append((number, match.group(0)))
        for pattern in README_TIME_PHRASES:
            found.extend((number, m.group(0)) for m in pattern.finditer(line))
    return found


def render_default(profile):
    """{relative output path: text} of the default config in ``profile``."""
    templates = load_templates(profile_templates_dir(profile))
    return dict(render_all(default_config(), templates, today="2026-01-15", profile=profile))


class SectionSignTest(unittest.TestCase):
    def test_no_section_sign_in_tracked_files(self):
        files = tracked_files()
        self.assertTrue(any(f.endswith("README.md") for f in files), "no files found")
        offenders = []
        for rel in files:
            text = read_text_file(rel)
            if text is None:
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if SECTION_SIGN in line:
                    offenders.append("%s:%d: %s" % (rel, number, line.strip()[:100]))
        self.assertEqual(offenders, [], "write 'clause 4.1.6', '21 CFR 820.10', 'Article 4' or "
                                        "'section 3' instead of the section sign:\n"
                         + "\n".join(offenders))

    def test_no_section_sign_in_rendered_packages(self):
        for profile in ("lite", "full"):
            for rel, text in render_default(profile).items():
                with self.subTest(profile=profile, document=rel):
                    self.assertNotIn(SECTION_SIGN, text)


class TimesAndEffortTest(unittest.TestCase):
    def test_duration_detector(self):
        for text in ("15-minute quick start", "in about a week", "1-2 days", "1–2 days",
                     "hours, not weeks", "at least 4 weeks", "12 months", "about 3 minutes",
                     "an hour", "a week", "two and a half hours", "Quick start in 5 steps",
                     "five minutes of reading", "review it weekly"):
            with self.subTest(text=text):
                self.assertTrue(durations(text), text)
        for text in ("Quick start", "a second vendor", "GAMP 5 Second Edition",
                     "Version 0.2.0", "12 test records covering 14 IDs", "in force 2 Feb 2026",
                     "REQ-01 to REQ-17", "--prs 20"):
            with self.subTest(text=text):
                self.assertEqual(durations(text), [], text)

    def test_readme_states_no_times_or_durations(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        found = durations(text)
        self.assertEqual(found, [], "README.md must state no times or durations; refer to the "
                                    "plan or the templates for periods: %s" % found)

    def test_guide_and_docs_make_no_effort_claims(self):
        files = [REPO / "GUIDE.md"] + sorted((REPO / "docs").glob("*.md"))
        self.assertGreater(len(files), 1, "docs/*.md not found")
        for path in files:
            text = path.read_text(encoding="utf-8").casefold()
            for phrase in EFFORT_PHRASES:
                with self.subTest(file=path.name, phrase=phrase):
                    self.assertNotIn(phrase.casefold(), text)


class MessagingTest(unittest.TestCase):
    def test_readme_and_guide_say_no_shadow_ai(self):
        for name in ("README.md", "GUIDE.md"):
            with self.subTest(file=name):
                self.assertIn("shadow AI", (REPO / name).read_text(encoding="utf-8"))
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("Why it matters", readme)
        self.assertIn("clause 4.1.6", readme)

    def test_guide_word_budget(self):
        count = len((REPO / "GUIDE.md").read_text(encoding="utf-8").split())
        self.assertLessEqual(count, GUIDE_BUDGET, "GUIDE.md has %d words (budget %d); shorten "
                                                  "the text" % (count, GUIDE_BUDGET))

    def test_work_instructions_have_the_no_shadow_ai_rule(self):
        name = "00-ai-assisted-development-work-instruction.md.tmpl"
        for profile in ("lite", "full"):
            with self.subTest(profile=profile):
                template = profile_templates_dir(profile) / name
                self.assertIn("No shadow AI", template.read_text(encoding="utf-8"))
                rendered = render_default(profile)[
                    SHARED_DIR + "/ai-assisted-development-work-instruction.md"]
                self.assertIn("No shadow AI", rendered, "the rule must not depend on options")


class DocumentIdTest(unittest.TestCase):
    """Lite and full never share a document ID (default config)."""

    @staticmethod
    def derived_ids(profile):
        ctx = derive(default_config(), today="2026-01-15", profile=profile)
        tool_nns = list(LITE_TOOL_DOCS) if profile == "lite" else [nn for nn, _ in TOOL_DOCS]
        shared = ["doc_id_wi", "doc_id_discovery"] + (
            [] if profile == "lite" else ["doc_id_gates"])
        ids = {ctx[var]: var for var in shared}
        for tool in ctx["tools_list"]:
            for nn in tool_nns:
                ids[tool["doc_id_" + nn]] = "%s doc_id_%s" % (tool["tool_id"], nn)
        return ids

    @staticmethod
    def rendered_ids(profile):
        ids = {}
        for rel, text in render_default(profile).items():
            heading = next(line for line in text.splitlines() if line.startswith("# "))
            ids.setdefault(heading.split()[1], []).append(rel)
        return ids

    def test_shared_documents_are_all_covered(self):
        self.assertEqual([v for v, _, _ in SHARED_DOCS],
                         ["doc_id_wi", "doc_id_discovery", "doc_id_gates"])

    def test_derived_ids_do_not_collide(self):
        lite, full = self.derived_ids("lite"), self.derived_ids("full")
        self.assertEqual(len(lite), 2 + 3 * len(default_config()["tools"]))
        self.assertEqual(len(full), 3 + 8 * len(default_config()["tools"]))
        self.assertEqual(sorted(set(lite) & set(full)), [])

    def test_rendered_ids_do_not_collide(self):
        lite, full = self.rendered_ids("lite"), self.rendered_ids("full")
        for profile, ids in (("lite", lite), ("full", full)):
            with self.subTest(profile=profile):
                self.assertEqual({i: r for i, r in ids.items() if len(r) > 1}, {},
                                 "one ID for several documents")
        self.assertEqual(sorted(set(lite) & set(full)), [],
                         "the same document ID names a lite and a full document")
        self.assertIn("ACME-VAL-CLAUDE-L01", lite)
        self.assertIn("ACME-VAL-GEN-L01", lite)
        self.assertIn("ACME-VAL-CLAUDE-01", full)
        self.assertIn("ACME-VAL-GEN-01", full)


if __name__ == "__main__":
    unittest.main()
