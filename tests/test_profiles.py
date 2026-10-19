"""Profile support: selection, backward compatibility and the full-profile recommendation."""

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kit.config import (DEFAULT_CONFIG, LEGACY_PROFILE, NEW_CONFIG_PROFILE,  # noqa: E402
                        PROFILE_KEYS, ConfigError, config_profile, default_config, derive,
                        effective_profile, full_profile_reasons, lite_blockers,
                        validate_config)
from kit.package import (TEMPLATES_ROOT, RenderRefused, profile_templates_dir,  # noqa: E402
                         render_package, resolve_templates_dir)


def quiet_config():
    """Default answers without any trigger for the full profile."""
    cfg = default_config()
    cfg["contexts"] = ["code_product", "code_tooling", "pr_review", "test_generation"]
    cfg["reg_gxp"] = False
    return cfg


def pin(cfg, index=0):
    tool = cfg["tools"][index]
    tool["approved_models"] = ["vendor-a-*", "vendor-a-1"]
    tool["model_policy"], tool["pinned_model"] = "pinned", "vendor-a-1"
    return cfg


class ProfileSelectionTests(unittest.TestCase):
    def test_profiles(self):
        self.assertEqual(PROFILE_KEYS, ["lite", "full"])
        self.assertEqual(NEW_CONFIG_PROFILE, "lite")
        self.assertEqual(LEGACY_PROFILE, "full")

    def test_new_configs_default_to_lite(self):
        self.assertEqual(default_config()["profile"], "lite")
        self.assertEqual(DEFAULT_CONFIG["profile"], "lite")
        ctx = derive(default_config())
        self.assertEqual(ctx["profile"], "lite")
        self.assertTrue(ctx["profile_lite"])
        self.assertFalse(ctx["profile_full"])

    def test_config_value_is_used(self):
        cfg = default_config()
        cfg["profile"] = "full"
        ctx = derive(cfg)
        self.assertEqual((ctx["profile"], ctx["profile_lite"], ctx["profile_full"]),
                         ("full", False, True))

    def test_override_wins_over_config(self):
        cfg = default_config()
        self.assertEqual(derive(cfg, profile="full")["profile"], "full")
        cfg["profile"] = "full"
        self.assertEqual(derive(cfg, profile="lite")["profile"], "lite")
        self.assertEqual(effective_profile(cfg, "lite"), "lite")
        self.assertEqual(effective_profile(cfg), "full")
        self.assertEqual(cfg["profile"], "full", "the override must not change the config")

    def test_invalid_profile(self):
        cfg = default_config()
        cfg["profile"] = "medium"
        self.assertIn("profile must be one of: lite, full", "\n".join(validate_config(cfg)))
        with self.assertRaises(ConfigError):
            derive(cfg)
        with self.assertRaises(ConfigError):
            effective_profile(default_config(), "medium")
        with self.assertRaises(ConfigError):
            derive(default_config(), profile="medium")

    def test_derived_profile_keys_rejected(self):
        for key in ("profile_lite", "profile_full", "full_recommended", "full_reasons"):
            cfg = default_config()
            cfg[key] = True
            with self.subTest(key=key):
                self.assertIn("derived automatically", "\n".join(validate_config(cfg)))


class BackwardCompatibilityTests(unittest.TestCase):
    def legacy(self):
        cfg = default_config()
        del cfg["profile"]
        return cfg

    def test_config_without_profile_is_valid_and_renders_full(self):
        cfg = self.legacy()
        self.assertEqual(validate_config(cfg), [])
        self.assertEqual(config_profile(cfg), "full")
        ctx = derive(cfg)
        self.assertEqual(ctx["profile"], "full")
        self.assertTrue(ctx["profile_full"])

    def test_legacy_config_renders_the_full_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = render_package(self.legacy(), None, tmp, today="2026-01-15")
            names = {p.name for p in written}
        self.assertIn("05-test-protocol.md", names)
        self.assertIn("code-host-gate-qualification.md", names)

    def test_legacy_config_can_be_overridden(self):
        self.assertEqual(derive(self.legacy(), profile="lite")["profile"], "lite")


class TemplateDirectoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def make_root(self):
        root = self.tmp / "templates"
        for profile in PROFILE_KEYS:
            (root / profile).mkdir(parents=True)
            (root / profile / "00-shared-doc.md.tmpl").write_text(
                "# shared {{profile}} lite={{profile_lite}} full={{profile_full}}\n",
                encoding="utf-8")
            (root / profile / ("01-%s-doc.md.tmpl" % profile)).write_text(
                "# {{tool_id}} {{profile}}\n", encoding="utf-8")
        return root

    def test_kit_profile_directories(self):
        self.assertEqual(profile_templates_dir("full"), TEMPLATES_ROOT / "full")
        self.assertEqual(profile_templates_dir("lite"), TEMPLATES_ROOT / "lite")
        self.assertEqual(resolve_templates_dir(None, "lite"), TEMPLATES_ROOT / "lite")
        with self.assertRaises(ValueError):
            profile_templates_dir("medium")

    def test_root_with_profile_subdirectories(self):
        root = self.make_root()
        self.assertEqual(resolve_templates_dir(root, "lite"), root / "lite")
        self.assertEqual(resolve_templates_dir(root, "full"), root / "full")
        self.assertEqual(resolve_templates_dir(root / "full", "lite"), root / "full",
                         "a directory without profile subdirectories is used as it is")

    def test_render_package_picks_the_profile_directory(self):
        root = self.make_root()
        for profile in PROFILE_KEYS:
            out = self.tmp / ("out-" + profile)
            written = render_package(default_config(), root, out, profile=profile)
            rel = sorted(str(p.relative_to(out)).replace("\\", "/") for p in written)
            with self.subTest(profile=profile):
                self.assertEqual(rel, ["00-shared/shared-doc.md",
                                       "CLAUDE/01-%s-doc.md" % profile,
                                       "CODEX/01-%s-doc.md" % profile])
                shared = (out / "00-shared" / "shared-doc.md").read_text(encoding="utf-8")
                self.assertEqual(shared, "# shared %s lite=%s full=%s\n" % (
                    profile, "yes" if profile == "lite" else "no",
                    "yes" if profile == "full" else "no"))

    def test_render_package_uses_the_config_profile(self):
        root = self.make_root()
        cfg = default_config()
        cfg["profile"] = "full"
        written = render_package(cfg, root, self.tmp / "o")
        self.assertIn("01-full-doc.md", {p.name for p in written})

    def test_invalid_config_is_rejected_before_templates_are_read(self):
        cfg = default_config()
        cfg["profile"] = "medium"
        with self.assertRaises(ConfigError):
            render_package(cfg, self.make_root(), self.tmp / "o")


class FullRecommendedTests(unittest.TestCase):
    def check(self, cfg, expected_count, *fragments):
        reasons = full_profile_reasons(cfg)
        ctx = derive(cfg)
        self.assertEqual(ctx["full_reasons"], reasons)
        self.assertEqual(ctx["full_recommended"], bool(reasons))
        self.assertEqual(len(reasons), expected_count, reasons)
        joined = "\n".join(reasons)
        for fragment in fragments:
            self.assertIn(fragment, joined)
        for reason in reasons:
            self.assertIsInstance(reason, str)
            self.assertNotIn("{{", reason)
            self.assertLess(len(reason), 200, "reasons must be short")
        return reasons

    def test_no_trigger(self):
        self.check(quiet_config(), 0)

    def test_default_config_has_no_trigger(self):
        self.check(default_config(), 0)
        cfg = default_config()
        cfg["contexts"].append("doc_drafting")
        self.check(cfg, 1, "L3", "doc_drafting")
        self.assertEqual(lite_blockers(cfg), [], "L3 is a warning, not a hard stop")

    def test_each_trigger_alone(self):
        cfg = pin(quiet_config())
        self.check(cfg, 1, "pinned", "Claude Code (CLAUDE)")
        cfg = quiet_config()
        cfg["contexts"].append("agents_qms")
        self.check(cfg, 1, "agents_qms")
        cfg = quiet_config()
        cfg["contexts"] = ["doc_drafting"]
        self.check(cfg, 1, "doc_drafting")
        cfg = quiet_config()
        cfg["reg_gxp"] = True
        self.check(cfg, 1, "GxP")
        for key, number in (("agent_qms_write", "L2"), ("ai_output_as_evidence", "L8"),
                            ("agent_untrusted_with_secrets", "L9")):
            cfg = quiet_config()
            cfg[key] = True
            reasons = self.check(cfg, 1, number + ", hard stop")
            self.assertEqual(lite_blockers(cfg), reasons)

    def test_hard_stops_and_warnings(self):
        cfg = pin(quiet_config())
        cfg["contexts"] += ["doc_drafting", "agents_qms"]
        cfg["reg_gxp"] = cfg["agent_qms_write"] = True
        blockers = lite_blockers(cfg)
        self.assertEqual([b.split(",")[0] for b in blockers], ["L1", "L2", "L2"])
        self.assertTrue(set(blockers) <= set(full_profile_reasons(cfg)))
        ctx = derive(cfg)
        self.assertTrue(ctx["lite_blocked"])
        self.assertEqual(ctx["lite_blockers"], blockers)
        self.assertFalse(derive(quiet_config())["lite_blocked"])

    def test_pinned_on_any_tool(self):
        cfg = pin(quiet_config(), index=1)
        reasons = self.check(cfg, 1, "OpenAI Codex (CODEX)")
        self.assertNotIn("CLAUDE", reasons[0])
        self.check(pin(pin(quiet_config(), 0), 1), 1, "(CLAUDE)", "(CODEX)")

    def test_all_triggers(self):
        cfg = pin(quiet_config())
        cfg["contexts"] += ["doc_drafting", "agents_qms"]
        cfg["reg_gxp"] = True
        self.check(cfg, 4, "pinned", "agents_qms", "doc_drafting", "GxP")

    def test_three_level_risk_model_is_not_a_trigger_by_itself(self):
        cfg = quiet_config()
        cfg["risk_model"] = "three_level"
        self.check(cfg, 0)

    def test_other_answers_are_not_triggers(self):
        cfg = quiet_config()
        cfg.update(already_in_use=True, reg_iso27001=True, reg_iso42001=True,
                   code_host="other", periodic_review_months=3)
        cfg["tools"][0]["surfaces"] = ["cloud_agent", "pr_review_bot", "ci_headless"]
        self.check(cfg, 0)

    def test_recommendation_is_independent_of_the_profile(self):
        cfg = default_config()
        cfg["contexts"].append("doc_drafting")
        lite, full = derive(cfg, profile="lite"), derive(cfg, profile="full")
        self.assertEqual(lite["full_reasons"], full["full_reasons"])
        self.assertTrue(lite["full_recommended"] and full["full_recommended"])


class RefusalTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_lite_refused_for_a_hard_stop(self):
        for label, mutate in (("pinned", pin), ("agents_qms", lambda c: c["contexts"].append(
                "agents_qms") or c), ("agent_qms_write", lambda c: c.update(
                    agent_qms_write=True) or c)):
            cfg = mutate(quiet_config())
            out = self.tmp / label
            with self.subTest(trigger=label):
                with self.assertRaises(RenderRefused) as cm:
                    render_package(cfg, None, out, profile="lite")
                self.assertIn("hard stop", str(cm.exception))
                self.assertFalse(out.exists(), "nothing is written when refused")
                written = render_package(cfg, None, out, profile="lite", force=True)
                plans = [p for p in written if p.name.endswith("-validation-plan.md")]
                self.assertTrue(plans)
                for path in written:
                    if path.parent.name != "00-shared":
                        self.assertIn("NOT VALID FOR RELEASE", path.read_text(encoding="utf-8"))
                full = render_package(cfg, None, self.tmp / (label + "-full"), profile="full")
                self.assertTrue(full)

    def test_other_profile_directory_refused(self):
        out = self.tmp / "out"
        render_package(quiet_config(), None, out, profile="lite")
        with self.assertRaises(RenderRefused) as cm:
            render_package(quiet_config(), None, out, profile="full")
        self.assertIn("other profile", str(cm.exception))
        render_package(quiet_config(), None, out, profile="lite")   # same profile: fine
        written = render_package(quiet_config(), None, out, profile="full", force=True)
        self.assertIn("05-test-protocol.md", {p.name for p in written})


if __name__ == "__main__":
    unittest.main()
