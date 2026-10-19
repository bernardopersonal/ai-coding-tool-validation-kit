"""Checks specific to the lite profile (templates/lite/).

* the lite package is the agreed file set (3 per-tool documents, 2 shared);
* lite is a strict subset of full: every canonical ID used by lite exists in full;
* the test record carries the lite tests, the plan the requirement subset;
* the plan warns prominently, with the reasons, when the full profile is recommended;
* hard stops (L1, L2, L8, L9): lite is refused without ``force`` and marked NOT VALID
  FOR RELEASE with it; the lite templates have no pinned-policy path;
* every lite test ID is listed in "Differences under shared IDs" of docs/lite-vs-full.md;
* word budget with the default config: each per-tool package <= 5,000 words in
  total, each shared document <= 1,200 words (whitespace-separated tokens of the
  rendered Markdown).

Nothing is skipped: missing lite templates fail the tests.
"""

import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))

from kit.config import default_config, derive  # noqa: E402
from kit.package import (SHARED_DIR, RenderRefused, is_shared, load_templates,  # noqa: E402
                         output_name, render_all, render_package)
from test_templates import LITE_TEMPLATES_DIR, TEMPLATES_DIR, template_paths  # noqa: E402

LITE_SHARED = ["ai-assisted-development-work-instruction.md", "tool-discovery-checklist.md"]
LITE_PER_TOOL = ["01-validation-plan.md", "02-test-record.md", "03-validation-report.md"]
PLAN, RECORD, REPORT = LITE_PER_TOOL

PER_TOOL_BUDGET = 5000
SHARED_BUDGET = 1200

ID_RE = re.compile(r"\b(?:REQ|IQ|OQ|MA|PQ|RV)-\d{2}\b")
ESSENTIAL_TESTS = ["IQ-03", "OQ-01", "OQ-02", "OQ-03", "OQ-04", "OQ-05", "OQ-06", "OQ-07",
                   "OQ-08", "OQ-09", "OQ-10", "MA-01", "PQ-01", "PQ-02"]
TEST_HEADING_RE = re.compile(r"^### ((?:IQ|OQ|MA|PQ)-\d{2}(?: and (?:IQ|OQ|MA|PQ)-\d{2})?) ",
                             re.M)
LITE_VS_FULL = REPO / "docs" / "lite-vs-full.md"
REQ_ALWAYS = ["REQ-01", "REQ-02", "REQ-03", "REQ-04", "REQ-05", "REQ-06", "REQ-08", "REQ-09",
              "REQ-10", "REQ-16", "REQ-17"]
# Criteria for "lite is not enough" that the answers cannot show; the plan states them.
NOT_IN_CONFIG_CRITERIA = [r"(?i)high process risk", r"(?i)notified body", r"(?i)audit"]


def words(text):
    return len(text.split())


def no_trigger_config():
    """Default answers without any trigger for the full profile."""
    cfg = default_config()
    cfg["contexts"] = ["code_product", "code_tooling", "pr_review", "test_generation"]
    cfg["reg_gxp"] = False
    for tool in cfg["tools"]:
        tool["model_policy"], tool["pinned_model"] = "envelope", ""
    return cfg


def trigger_configs():
    """[(label, config)] with exactly one trigger for the full profile each."""
    out = []
    cfg = no_trigger_config()
    cfg["tools"][1].update(approved_models=["openai-model-*", "openai-model-a"],
                           model_policy="pinned", pinned_model="openai-model-a")
    out.append(("pinned", cfg))
    for ctx in ("agents_qms", "doc_drafting"):
        cfg = no_trigger_config()
        cfg["contexts"] = cfg["contexts"] + [ctx]
        out.append((ctx, cfg))
    cfg = no_trigger_config()
    cfg["reg_gxp"] = True
    out.append(("gxp", cfg))
    return out


class LiteTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = template_paths("lite")
        if not cls.paths:
            raise AssertionError("templates/lite/ has no *.md.tmpl templates")
        cls.templates = load_templates(LITE_TEMPLATES_DIR)

    def render(self, cfg):
        """{relative output path: text} for the lite profile."""
        return dict(render_all(cfg, self.templates, today="2026-01-15", profile="lite"))

    def per_tool(self, rendered, tool_id, name):
        key = "%s/%s" % (tool_id, name)
        if key not in rendered:
            self.fail("lite profile does not render %s (templates/lite/ needs %s.tmpl)"
                      % (key, name))
        return rendered[key]


class LiteFileSetTest(LiteTestCase):
    def test_lite_file_set(self):
        shared = sorted(output_name(p) for p in self.paths if is_shared(p))
        per_tool = sorted(output_name(p) for p in self.paths if not is_shared(p))
        self.assertEqual(shared, sorted(LITE_SHARED), "lite shared documents")
        self.assertEqual(per_tool, sorted(LITE_PER_TOOL), "lite per-tool documents")

    def test_lite_ids_are_a_subset_of_full(self):
        full_ids = set()
        for path in template_paths("full"):
            full_ids |= set(ID_RE.findall(path.read_text(encoding="utf-8")))
        for path in self.paths:
            with self.subTest(template=path.name):
                extra = sorted(set(ID_RE.findall(path.read_text(encoding="utf-8"))) - full_ids)
                self.assertEqual(extra, [], "%s uses IDs that the full profile does not "
                                            "define (lite must be a strict subset)" % path.name)


class LiteContentTest(LiteTestCase):
    def test_test_record_has_the_essential_tests(self):
        rendered = self.render(default_config())
        for tool in ("CLAUDE", "CODEX"):
            text = self.per_tool(rendered, tool, RECORD)
            missing = [t for t in ESSENTIAL_TESTS if t not in text]
            with self.subTest(tool=tool):
                self.assertEqual(missing, [], "essential tests missing from the lite test "
                                              "record")

    def test_test_record_gives_the_script_commands(self):
        text = self.per_tool(self.render(default_config()), "CLAUDE", RECORD)
        for command in ("checks/capture_baseline.py", "checks/check_github_gates.py",
                        "admission/run_admission.py", "checks/canary/"):
            with self.subTest(command=command):
                self.assertIn(command, text)

    def test_plan_lists_the_requirement_subset(self):
        ctx = derive(default_config())
        rendered = self.render(default_config())
        for tool in ctx["tools_list"]:
            expected = list(REQ_ALWAYS)
            if tool["surf_local_cli_ide"] or tool["surf_ci_headless"]:
                expected.append("REQ-07")
            if ctx["ctx_pr_review"] or tool["surf_pr_review_bot"]:
                expected.append("REQ-15")
            text = self.per_tool(rendered, tool["tool_id"], PLAN)
            with self.subTest(tool=tool["tool_id"]):
                self.assertEqual([r for r in expected if r not in text], [])

    def test_plan_and_report_show_the_model_envelope(self):
        cfg = default_config()
        cfg["tools"][0]["approved_models"] = ["vendor-zz-family-*", "vendor-zz-exact-9"]
        rendered = self.render(cfg)
        for name in (PLAN, REPORT):
            text = self.per_tool(rendered, "CLAUDE", name)
            with self.subTest(document=name):
                self.assertIn("vendor-zz-family-*", text)
                self.assertIn("vendor-zz-exact-9", text)

    def test_plan_states_when_lite_is_not_enough(self):
        text = self.per_tool(self.render(no_trigger_config()), "CLAUDE", PLAN)
        for pattern in NOT_IN_CONFIG_CRITERIA + [r"(?i)pinned", r"GxP",
                                                 r"agents_qms|QMS agent",
                                                 r"doc_drafting|[Dd]ocument drafting"]:
            with self.subTest(criterion=pattern):
                self.assertRegex(text, pattern)

    def test_plan_lists_l1_to_l9(self):
        text = self.per_tool(self.render(no_trigger_config()), "CLAUDE", PLAN)
        rows = [line for line in text.splitlines() if re.match(r"\| L[1-9] \|", line)]
        self.assertEqual([r.split("|")[1].strip() for r in rows],
                         ["L%d" % n for n in range(1, 10)])
        for number in ("L1", "L2", "L8", "L9"):
            row = [r for r in rows if r.startswith("| %s |" % number)][0]
            self.assertIn("Hard stop", row)

    def test_interim_use_block_when_already_in_use(self):
        cfg = no_trigger_config()
        cfg["already_in_use"] = True
        self.assertRegex(self.per_tool(self.render(cfg), "CLAUDE", PLAN), r"(?i)interim")


class LiteWarningTest(LiteTestCase):
    def test_no_trigger_config_recommends_lite(self):
        self.assertEqual(derive(no_trigger_config())["full_reasons"], [])

    def test_plan_warns_prominently_with_the_reasons(self):
        all_reasons = set()
        for label, cfg in trigger_configs():
            ctx = derive(cfg)
            self.assertTrue(ctx["full_recommended"], label)
            all_reasons |= set(ctx["full_reasons"])
            rendered = self.render(cfg)
            for tool in ctx["tools_list"]:
                text = self.per_tool(rendered, tool["tool_id"], PLAN)
                with self.subTest(trigger=label, tool=tool["tool_id"]):
                    for reason in ctx["full_reasons"]:
                        self.assertIn(reason, text, "the lite plan must list every reason "
                                                    "({{#full_reasons}}{{.}}{{/full_reasons}})")
                        self.assertLess(text.index(reason), len(text) // 2,
                                        "the full-profile warning must be prominent (in the "
                                        "first half of the plan)")
        quiet = self.render(no_trigger_config())
        for tool in ("CLAUDE", "CODEX"):
            text = self.per_tool(quiet, tool, PLAN)
            with self.subTest(trigger="none", tool=tool):
                self.assertEqual([r for r in all_reasons if r in text], [])


class LiteHardStopTest(LiteTestCase):
    def blocked_configs(self):
        out = trigger_configs()[:2]   # pinned, agents_qms
        for key in ("agent_qms_write", "ai_output_as_evidence", "agent_untrusted_with_secrets"):
            cfg = no_trigger_config()
            cfg[key] = True
            out.append((key, cfg))
        return out

    def test_lite_does_not_render_for_a_hard_stop(self):
        import tempfile
        for label, cfg in self.blocked_configs():
            with self.subTest(trigger=label), tempfile.TemporaryDirectory() as tmp:
                self.assertTrue(derive(cfg)["lite_blocked"])
                with self.assertRaises(RenderRefused):
                    render_package(cfg, LITE_TEMPLATES_DIR, tmp, profile="lite")
                written = render_package(cfg, LITE_TEMPLATES_DIR, tmp, profile="lite",
                                         force=True)
                for path in written:
                    text = path.read_text(encoding="utf-8")
                    if path.parent.name != SHARED_DIR:
                        self.assertIn("NOT VALID FOR RELEASE", text, path.name)
                        self.assertNotIn("WARNING: the full profile is recommended", text)

    def test_conditional_triggers_render_with_the_warning(self):
        for label, cfg in trigger_configs()[2:]:   # doc_drafting, gxp
            with self.subTest(trigger=label):
                self.assertFalse(derive(cfg)["lite_blocked"])
                text = self.per_tool(self.render(cfg), "CLAUDE", PLAN)
                self.assertIn("WARNING: the full profile is recommended", text)
                self.assertIn("no, because", text)
                self.assertNotIn("NOT VALID FOR RELEASE", text)

    def test_no_pinned_policy_path_in_lite_templates(self):
        for path in self.paths:
            text = path.read_text(encoding="utf-8")
            with self.subTest(template=path.name):
                self.assertFalse("pinned_model" in text, "pinned_model in %s" % path.name)
                lines = [line for line in text.splitlines() if "policy_pinned" in line]
                self.assertTrue(all(line.startswith("| L1 |") for line in lines),
                                "policy_pinned only in the L1 row of the plan: %s" % lines)


class LiteVsFullDocTest(LiteTestCase):
    def test_every_lite_test_id_is_in_the_differences_table(self):
        doc = LITE_VS_FULL.read_text(encoding="utf-8")
        section = doc.split("## Differences under shared IDs", 1)[1].split("\n## ", 1)[0]
        listed = set()
        for line in section.splitlines():
            if line.startswith("| ") and not line.startswith("| ID"):
                listed |= set(ID_RE.findall(line.split("|")[1]))
        record = [p for p in self.paths if output_name(p) == RECORD][0]
        ids = set()
        for heading in TEST_HEADING_RE.findall(record.read_text(encoding="utf-8")):
            ids |= set(ID_RE.findall(heading))
        self.assertEqual(sorted(ids), sorted(set(ESSENTIAL_TESTS)))
        self.assertEqual(sorted(ids - listed), [], "lite test IDs missing from the "
                                                   "differences table of docs/lite-vs-full.md")


class LiteWordBudgetTest(LiteTestCase):
    """Default config: per-tool package <= 5,000 words, shared document <= 1,200 words."""

    def test_per_tool_package_budget(self):
        self.assertTrue(any(not is_shared(p) for p in self.paths), "no per-tool lite templates")
        rendered = self.render(default_config())
        totals = {}
        for rel, text in rendered.items():
            folder, name = rel.split("/", 1)
            if folder != SHARED_DIR:
                totals.setdefault(folder, {})[name] = words(text)
        for tool, counts in sorted(totals.items()):
            with self.subTest(tool=tool):
                self.assertLessEqual(
                    sum(counts.values()), PER_TOOL_BUDGET,
                    "lite package %s/ has %d words (budget %d): %s" % (
                        tool, sum(counts.values()), PER_TOOL_BUDGET,
                        ", ".join("%s %d" % kv for kv in sorted(counts.items()))))

    def test_shared_document_budget(self):
        rendered = self.render(default_config())
        shared = {rel: words(text) for rel, text in rendered.items()
                  if rel.startswith(SHARED_DIR + "/")}
        self.assertTrue(shared, "no shared lite documents")
        for rel, count in sorted(shared.items()):
            with self.subTest(document=rel):
                self.assertLessEqual(count, SHARED_BUDGET, "%s has %d words (budget %d)" % (
                    rel, count, SHARED_BUDGET))


class FullIsUnchangedTest(unittest.TestCase):
    def test_full_templates_keep_the_in_depth_file_set(self):
        names = sorted(output_name(p) for p in template_paths("full"))
        self.assertEqual(names, sorted([
            "ai-assisted-development-work-instruction.md", "code-host-gate-qualification.md",
            "tool-discovery-checklist.md", "01-inventory-and-intended-use.md",
            "02-requirements.md", "03-risk-assessment.md", "04-validation-plan.md",
            "05-test-protocol.md", "06-configuration-baseline.md", "07-validation-report.md",
            "08-change-and-revalidation.md"]))
        self.assertEqual(TEMPLATES_DIR, REPO / "templates" / "full")


if __name__ == "__main__":
    unittest.main()
