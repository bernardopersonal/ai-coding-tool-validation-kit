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


class WizardTests(unittest.TestCase):
    def test_all_defaults_reproduce_default_config(self):
        script = Script([])
        cfg = run_wizard(input_fn=lambda prompt: (script.prompts.append(prompt), "")[1],
                         print_fn=script.print)
        self.assertEqual(cfg, default_config())
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
        errors = "\n".join(script.printed)
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

    def test_input_end_aborts(self):
        with self.assertRaises(WizardAbort):
            run_wizard(input_fn=Script([]).input, print_fn=lambda *a, **k: None)

    def test_endless_invalid_answers_abort(self):
        with self.assertRaises(WizardAbort):
            run_wizard(input_fn=lambda prompt: "???" if "code" in prompt else "",
                       print_fn=lambda *a, **k: None)


if __name__ == "__main__":
    unittest.main()
