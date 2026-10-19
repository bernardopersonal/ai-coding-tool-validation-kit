"""Tests for the interactive wizard (kit/wizard.py) using scripted input."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kit.config import default_config, validate_config  # noqa: E402
from kit.wizard import WizardAbort, run_wizard  # noqa: E402


class Script:
    """Feeds scripted answers to input() and records the prompts."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.prompts = []
        self.printed = []

    def input(self, prompt):
        self.prompts.append(prompt)
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)

    def print(self, *args, **_kwargs):
        self.printed.append(" ".join(str(a) for a in args))


def answer_profile(answer, printed):
    """input_fn: Enter everywhere, ``answer`` at the profile question."""
    def fake_input(prompt):
        if printed and printed[-1].lstrip().startswith("2. full"):
            return answer
        return ""
    return fake_input


class WizardTests(unittest.TestCase):
    def test_all_defaults_reproduce_default_config(self):
        """Every default accepted: the example answers, profile = the recommendation (lite:
        the example answers contain no trigger for full)."""
        script = Script([])
        cfg = run_wizard(input_fn=lambda prompt: (script.prompts.append(prompt), "")[1],
                         print_fn=script.print)
        self.assertEqual(cfg, default_config())
        self.assertEqual(script.prompts[-1], "Choice [lite]: ")
        printed = "\n".join(script.printed)
        self.assertIn("Recommended for these answers: lite.", printed)
        self.assertIn("Hard stops for the lite profile", printed)
        self.assertIn("make L8 relevant", printed)   # code_tooling
        self.assertIn("make L9 relevant", printed)   # PR review bot, CI and cloud surfaces
        self.assertTrue(any(p.startswith("L2 Can an agent") for p in script.prompts))
        self.assertIn("Organisation name [Acme MedSoft]: ", script.prompts)
        self.assertTrue(any(p.startswith("Approved models (comma-separated) [anthropic-model-*")
                            for p in script.prompts))

    def test_custom_answers_with_reprompts(self):
        script = Script([
            "Example Devices GmbH", "EXD", "", "Class IIa SaMD",
            "iso13485,gxp",
            "QA Engineer", "qa engineer", "Quality Manager", "", "Jane Roe",
            "gitlab",
            "agents_qms,code_product,bogus", "agents_qms,code_product",
            "2", "n", "", "1",
            "copilot", "", "gen", "copilot", "", "pr_review_bot",
            "", "vendor-x-*, vendor-x-1",
            "pinned", "",
            "", "", "",          # hard-stop questions L2, L8, L9; no profile question
        ])
        cfg = run_wizard(input_fn=script.input, print_fn=script.print)
        self.assertEqual(script.answers, [], "not all scripted answers were consumed")
        self.assertEqual(validate_config(cfg), [])
        self.assertEqual(cfg["org_name"], "Example Devices GmbH")
        self.assertEqual(cfg["doc_id_pattern"], "{org}-VAL-{tool}-{nn}")
        self.assertTrue(cfg["reg_iso13485"] and cfg["reg_gxp"])
        self.assertFalse(cfg["reg_fda_qmsr"] or cfg["reg_iso27001"] or cfg["reg_iso42001"])
        self.assertEqual(cfg["role_approver"], "Quality Manager")
        self.assertEqual(cfg["role_tool_owner"], "Engineering Lead")
        self.assertEqual(cfg["role_prrc"], "Jane Roe")
        self.assertEqual(cfg["code_host"], "gitlab")
        self.assertEqual(cfg["contexts"], ["code_product", "agents_qms"])
        self.assertEqual(cfg["risk_model"], "three_level")
        self.assertFalse(cfg["already_in_use"])
        self.assertEqual(cfg["periodic_review_months"], 6)  # recommended for agents_qms
        self.assertEqual(cfg["tools"], [{
            "tool_key": "copilot", "tool_name": "GitHub Copilot", "tool_id": "COPILOT",
            "vendor": "GitHub", "surfaces": ["pr_review_bot"],
            "approved_models": ["vendor-x-*", "vendor-x-1"], "model_policy": "pinned",
            "pinned_model": "vendor-x-1"}])
        self.assertEqual(cfg["profile"], "full")  # pinned and agents_qms: hard stops
        errors = "\n".join(script.printed)
        self.assertIn("The full profile is required because:", errors)
        self.assertIn("Profile: full (lite is not available with a hard stop).", errors)
        for fragment in ("Model policy pinned for GitHub Copilot (COPILOT)",
                         "Context agents_qms", "GxP in scope"):
            self.assertIn(fragment, errors)
        self.assertIn("different role from the executor", errors)
        self.assertIn("unknown option 'bogus'", errors)
        self.assertIn("reserved", errors)
        self.assertIn("enter at least one value", errors)

    def test_clear_optional_values(self):
        defaults = default_config()
        defaults["role_prrc"] = "Someone"
        answers = {"PRRC": "-", "Selection (comma-separated, - for none)": "-"}

        def fake_input(prompt):
            for start, answer in answers.items():
                if prompt.startswith(start):
                    return answer
            return ""

        cfg = run_wizard(defaults, input_fn=fake_input, print_fn=lambda *a, **k: None)
        self.assertEqual(cfg["role_prrc"], "")
        self.assertFalse(any(cfg[k] for k in ("reg_iso13485", "reg_fda_qmsr", "reg_gxp")))

    def test_profile_defaults_to_lite_without_triggers(self):
        defaults = default_config()
        defaults["contexts"] = ["code_product", "pr_review"]
        printed = []
        cfg = run_wizard(defaults, input_fn=answer_profile("", printed),
                         print_fn=lambda *a, **k: printed.append(" ".join(map(str, a))))
        self.assertEqual(cfg["profile"], "lite")
        text = "\n".join(printed)
        self.assertIn("Recommended for these answers: lite.", text)
        self.assertIn("No trigger for the full profile", text)
        self.assertIn("high process risk", text)
        self.assertEqual(validate_config(cfg), [])

    def test_choosing_lite_against_the_recommendation_warns(self):
        printed = []
        defaults = default_config()
        defaults["contexts"].append("doc_drafting")
        cfg = run_wizard(defaults, input_fn=answer_profile("lite", printed),
                         print_fn=lambda *a, **k: printed.append(" ".join(map(str, a))))
        self.assertEqual(cfg["profile"], "lite")
        self.assertIn("lite chosen although full is recommended", "\n".join(printed))

    def test_choosing_full_without_triggers(self):
        defaults = default_config()
        defaults["contexts"] = ["code_product"]
        printed = []
        cfg = run_wizard(defaults, input_fn=answer_profile("2", printed),
                         print_fn=lambda *a, **k: printed.append(" ".join(map(str, a))))
        self.assertEqual(cfg["profile"], "full")

    def test_existing_full_choice_stays_the_default(self):
        defaults = default_config()
        defaults["contexts"] = ["code_product"]
        defaults["profile"] = "full"
        printed = []
        cfg = run_wizard(defaults, input_fn=answer_profile("", printed),
                         print_fn=lambda *a, **k: printed.append(" ".join(map(str, a))))
        self.assertEqual(cfg["profile"], "full")
        self.assertIn("Keeping full from the existing config", "\n".join(printed))

    def test_legacy_config_without_profile_defaults_to_full(self):
        defaults = default_config()
        defaults["contexts"] = ["code_product"]
        del defaults["profile"]
        printed = []
        cfg = run_wizard(defaults, input_fn=answer_profile("", printed),
                         print_fn=lambda *a, **k: printed.append(" ".join(map(str, a))))
        self.assertEqual(cfg["profile"], "full")

    def test_existing_lite_choice_follows_the_recommendation(self):
        defaults = default_config()  # profile lite, but doc_drafting recommends full
        defaults["contexts"].append("doc_drafting")
        printed = []
        cfg = run_wizard(defaults, input_fn=answer_profile("", printed),
                         print_fn=lambda *a, **k: printed.append(" ".join(map(str, a))))
        self.assertEqual(cfg["profile"], "full")

    def test_hard_stop_sets_full(self):
        defaults = default_config()
        defaults["agent_untrusted_with_secrets"] = True
        printed = []
        cfg = run_wizard(defaults, input_fn=lambda prompt: "",
                         print_fn=lambda *a, **k: printed.append(" ".join(map(str, a))))
        self.assertEqual(cfg["profile"], "full")
        self.assertTrue(cfg["agent_untrusted_with_secrets"])
        text = "\n".join(printed)
        self.assertIn("L9, hard stop", text)
        self.assertIn("lite is not available with a hard stop", text)
        printed = []
        cfg = run_wizard(defaults, input_fn=lambda prompt: "", profile="lite",
                         print_fn=lambda *a, **k: printed.append(" ".join(map(str, a))))
        self.assertEqual(cfg["profile"], "lite")
        self.assertIn("NOT VALID FOR RELEASE", "\n".join(printed))

    def test_profile_option_skips_the_question(self):
        script = Script([])
        printed = []
        defaults = default_config()
        defaults["contexts"].append("doc_drafting")
        cfg = run_wizard(defaults,
                         input_fn=lambda prompt: (script.prompts.append(prompt), "")[1],
                         print_fn=lambda *a, **k: printed.append(" ".join(map(str, a))),
                         profile="lite")
        self.assertEqual(cfg["profile"], "lite")
        text = "\n".join(printed)
        self.assertIn("Profile: lite (set with --profile).", text)
        self.assertIn("lite was chosen although full is recommended", text)
        self.assertNotIn("2. full", text)
        self.assertNotEqual(script.prompts[-1], "Choice [full]: ")
        with self.assertRaises(WizardAbort):
            run_wizard(input_fn=lambda prompt: "", print_fn=lambda *a, **k: None,
                       profile="medium")

    def test_input_end_aborts(self):
        with self.assertRaises(WizardAbort):
            run_wizard(input_fn=Script([]).input, print_fn=lambda *a, **k: None)

    def test_endless_invalid_answers_abort(self):
        with self.assertRaises(WizardAbort):
            run_wizard(input_fn=lambda prompt: "???" if "code" in prompt else "",
                       print_fn=lambda *a, **k: None)


if __name__ == "__main__":
    unittest.main()
