"""Tests for kit/config.py: defaults, validation, derive() and the variable registry."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kit.config import (CONTEXT_KEYS, SURFACE_KEYS, TOOL_KEYS, VARIABLES,  # noqa: E402
                        ConfigError, config_to_json, default_config, derive, load_config,
                        validate_config, variable_names, variables_markdown)


def tool(**overrides):
    base = {"tool_key": "claude_code", "tool_name": "Claude Code", "tool_id": "CLAUDE",
            "vendor": "Anthropic", "surfaces": ["local_cli_ide"],
            "approved_models": ["vendor-a-small-*"], "model_policy": "envelope",
            "pinned_model": ""}
    base.update(overrides)
    return base


class DefaultConfigTests(unittest.TestCase):
    def test_default_is_valid(self):
        self.assertEqual(validate_config(default_config()), [])

    def test_default_is_fictional_and_two_tools(self):
        cfg = default_config()
        self.assertEqual(cfg["org_name"], "Acme MedSoft")
        self.assertEqual([t["tool_key"] for t in cfg["tools"]], ["claude_code", "codex"])
        self.assertEqual(cfg["profile"], "lite")

    def test_json_puts_profile_first(self):
        self.assertEqual(next(iter(json.loads(config_to_json(default_config())))), "profile")

    def test_json_round_trip(self):
        cfg = default_config()
        self.assertEqual(json.loads(config_to_json(cfg)), cfg)

    def test_load_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kit.config.json"
            path.write_text(config_to_json(default_config()), encoding="utf-8")
            self.assertEqual(load_config(path), default_config())
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ConfigError) as cm:
                load_config(path)
            self.assertIn("invalid JSON", str(cm.exception))


class DeriveTests(unittest.TestCase):
    def setUp(self):
        self.ctx = derive(default_config(), today="2026-01-31")

    def test_doc_ids(self):
        full = derive(default_config(), today="2026-01-31", profile="full")
        claude = full["tools_list"][0]
        self.assertEqual(claude["doc_id_01"], "ACME-VAL-CLAUDE-01")
        self.assertEqual(claude["doc_id_08"], "ACME-VAL-CLAUDE-08")
        self.assertEqual(full["tools_list"][1]["doc_id_05"], "ACME-VAL-CODEX-05")
        self.assertEqual(full["doc_id_wi"], "ACME-VAL-GEN-01")
        self.assertEqual(full["doc_id_discovery"], "ACME-VAL-GEN-02")

    def test_lite_doc_ids_do_not_collide_with_full(self):
        lite = self.ctx["tools_list"][0]   # the default config renders lite
        self.assertEqual([lite["doc_id_%02d" % n] for n in (1, 2, 3)],
                         ["ACME-VAL-CLAUDE-L01", "ACME-VAL-CLAUDE-L02", "ACME-VAL-CLAUDE-L03"])
        self.assertEqual(lite["doc_id_05"], "ACME-VAL-CLAUDE-05")
        self.assertEqual(self.ctx["doc_id_wi"], "ACME-VAL-GEN-L01")
        self.assertEqual(self.ctx["doc_id_discovery"], "ACME-VAL-GEN-L02")
        self.assertEqual(self.ctx["doc_id_gates"], "ACME-VAL-GEN-03")   # full-only document

    def test_custom_pattern(self):
        cfg = default_config()
        cfg["doc_id_pattern"] = "VAL-{nn}-{tool}"
        ctx = derive(cfg, profile="full")
        self.assertEqual(ctx["tools_list"][0]["doc_id_03"], "VAL-03-CLAUDE")
        self.assertEqual(ctx["doc_id_wi"], "VAL-01-GEN")

    def test_booleans(self):
        ctx, claude, codex = self.ctx, self.ctx["tools_list"][0], self.ctx["tools_list"][1]
        self.assertTrue(claude["is_claude_code"])
        self.assertFalse(claude["is_codex"])
        self.assertTrue(codex["is_codex"])
        self.assertTrue(claude["policy_envelope"])
        self.assertFalse(claude["policy_pinned"])
        self.assertEqual(claude["pinned_model"], "")
        self.assertTrue(claude["surf_ci_headless"])
        self.assertFalse(claude["surf_cloud_agent"])
        self.assertTrue(ctx["code_github"])
        self.assertFalse(ctx["code_gitlab"])
        self.assertTrue(ctx["risk_csa"])
        self.assertFalse(ctx["risk_three"])
        self.assertFalse(ctx["ctx_doc_drafting"])
        self.assertTrue(ctx["ctx_code_product"])
        self.assertFalse(ctx["ctx_agents_qms"])
        self.assertEqual(ctx["today"], "2026-01-31")
        self.assertFalse(ctx["owner_is_executor"])
        self.assertFalse(ctx["agent_qms_write"] or ctx["ai_output_as_evidence"] or
                         ctx["agent_untrusted_with_secrets"])
        self.assertEqual(ctx["config_file"], "kit.config.json")
        self.assertEqual(derive(default_config(), config_file="x/my.json")["config_file"],
                         "x/my.json")

    def test_owner_is_executor(self):
        cfg = default_config()
        cfg["role_tool_owner"] = " validation engineer "
        self.assertTrue(derive(cfg)["owner_is_executor"])

    def test_lists(self):
        self.assertEqual(self.ctx["contexts_list"][0],
                         {"key": "code_product", "label": "Product code",
                          "description": self.ctx["contexts_list"][0]["description"]})
        self.assertIs(self.ctx["tools"], self.ctx["tools_list"])
        claude = self.ctx["tools_list"][0]
        self.assertEqual(claude["approved_models"], ["anthropic-model-*"])
        self.assertEqual([s["key"] for s in claude["surfaces_list"]], claude["surfaces"])

    def test_canonical_order(self):
        cfg = default_config()
        cfg["contexts"] = ["doc_drafting", "code_product"]
        cfg["tools"][0]["surfaces"] = ["ci_headless", "local_cli_ide"]
        ctx = derive(cfg)
        self.assertEqual(ctx["contexts"], ["code_product", "doc_drafting"])
        self.assertEqual(ctx["tools_list"][0]["surfaces"], ["local_cli_ide", "ci_headless"])

    def test_pinned(self):
        cfg = default_config()
        cfg["tools"][0].update(approved_models=["vendor-a-small-*"], model_policy="pinned",
                               pinned_model="vendor-a-small-2")
        claude = derive(cfg)["tools_list"][0]
        self.assertTrue(claude["policy_pinned"])
        self.assertEqual(claude["pinned_model"], "vendor-a-small-2")

    def test_derive_does_not_mutate_input(self):
        cfg = default_config()
        derive(cfg)
        self.assertEqual(cfg, default_config())

    def test_today_from_config(self):
        cfg = default_config()
        cfg["today"] = "2030-01-02"
        self.assertEqual(derive(cfg)["today"], "2030-01-02")


class RegistryTests(unittest.TestCase):
    """The registry (and therefore README_DEV.md) must match derive() exactly."""

    def test_global_keys_match_registry(self):
        ctx = derive(default_config())
        self.assertEqual(sorted(ctx), sorted(variable_names("global")))

    def test_tool_keys_match_registry(self):
        for key in TOOL_KEYS:
            cfg = default_config()
            cfg["tools"] = [tool(tool_key=key, tool_id="T" + key.upper()[:5])]
            t = derive(cfg)["tools_list"][0]
            self.assertEqual(sorted(t), sorted(variable_names("tool")), key)

    def test_item_keys_match_registry(self):
        ctx = derive(default_config())
        self.assertEqual(sorted(ctx["contexts_list"][0]), sorted(variable_names("context item")))
        self.assertEqual(sorted(ctx["tools_list"][0]["surfaces_list"][0]),
                         sorted(variable_names("surface item")))

    def test_registry_types(self):
        ctx = derive(default_config())
        frames = {"global": ctx, "tool": ctx["tools_list"][0],
                  "context item": ctx["contexts_list"][0],
                  "surface item": ctx["tools_list"][0]["surfaces_list"][0]}
        expected = {"str": str, "bool": bool, "int": int}
        for scope, name, vtype, _desc in VARIABLES:
            value = frames[scope][name]
            if vtype.startswith("list"):
                self.assertIsInstance(value, list, name)
            else:
                self.assertIs(type(value), expected[vtype], name)

    def test_registry_has_no_duplicates(self):
        seen = [(v[0], v[1]) for v in VARIABLES]
        self.assertEqual(len(seen), len(set(seen)))

    def test_global_and_tool_names_disjoint(self):
        self.assertFalse(set(variable_names("global")) & set(variable_names("tool")))

    def test_readme_dev_is_in_sync(self):
        readme = (REPO / "README_DEV.md").read_text(encoding="utf-8")
        self.assertIn(variables_markdown(), readme,
                      "README_DEV.md variable list is stale: run "
                      "'python3 kit.py vars --update README_DEV.md'")


class ValidationTests(unittest.TestCase):
    def errors(self, mutate):
        cfg = default_config()
        mutate(cfg)
        return "\n".join(validate_config(cfg))

    def assertInvalid(self, mutate, fragment):
        errs = self.errors(mutate)
        self.assertIn(fragment, errs)
        with self.assertRaises(ConfigError):
            cfg = default_config()
            mutate(cfg)
            derive(cfg)

    def test_unknown_and_derived_keys(self):
        self.assertInvalid(lambda c: c.update(colour="red"), "unknown key 'colour'")
        self.assertInvalid(lambda c: c.update(risk_csa=True), "derived automatically")
        self.assertInvalid(lambda c: c["tools"][0].update(is_codex=True), "derived automatically")

    def test_comment_keys_allowed(self):
        self.assertEqual(self.errors(lambda c: c.update(_comment="note")), "")

    def test_missing_keys(self):
        self.assertInvalid(lambda c: c.pop("risk_model"), "missing key(s): risk_model")
        self.assertInvalid(lambda c: c["tools"][0].pop("vendor"), "missing key(s): vendor")

    def test_role_prrc_optional(self):
        self.assertEqual(self.errors(lambda c: c.pop("role_prrc")), "")

    def test_lite_stop_keys_optional_booleans(self):
        for key in ("agent_qms_write", "ai_output_as_evidence", "agent_untrusted_with_secrets"):
            with self.subTest(key=key):
                self.assertEqual(self.errors(lambda c: c.pop(key)), "")
                self.assertEqual(self.errors(lambda c: c.update({key: True})), "")
                self.assertInvalid(lambda c: c.update({key: "yes"}), "%s must be true or false"
                                   % key)

    def test_profile_optional(self):
        self.assertEqual(self.errors(lambda c: c.pop("profile")), "")
        self.assertEqual(self.errors(lambda c: c.update(profile="full")), "")

    def test_executor_differs_from_approver(self):
        self.assertInvalid(lambda c: c.update(role_approver="validation engineer"),
                           "executor != approver")

    def test_enums(self):
        self.assertInvalid(lambda c: c.update(code_host="bitbucket"), "code_host")
        self.assertInvalid(lambda c: c.update(risk_model="fmea"), "risk_model")
        self.assertInvalid(lambda c: c.update(contexts=["code_product", "x"]), "unknown value")
        self.assertInvalid(lambda c: c.update(contexts=[]), "at least 1")
        self.assertInvalid(lambda c: c["tools"][0].update(tool_key="vim"), "tool_key")
        self.assertInvalid(lambda c: c["tools"][0].update(surfaces=["moon"]), "surfaces")
        self.assertInvalid(lambda c: c["tools"][0].update(model_policy="any"), "model_policy")
        self.assertInvalid(lambda c: c.update(profile="medium"), "profile must be one of")
        self.assertInvalid(lambda c: c.update(profile=None), "profile must be one of")

    def test_types(self):
        self.assertInvalid(lambda c: c.update(reg_gxp="yes"), "reg_gxp must be true or false")
        self.assertInvalid(lambda c: c.update(periodic_review_months="12"), "integer")
        self.assertInvalid(lambda c: c.update(periodic_review_months=True), "integer")
        self.assertInvalid(lambda c: c.update(tools=[]), "non-empty")
        self.assertInvalid(lambda c: c.update(today="18/10/2026"), "ISO date")

    def test_tool_ids(self):
        self.assertInvalid(lambda c: c["tools"][1].update(tool_id="CLAUDE"), "more than one")
        self.assertInvalid(lambda c: c["tools"][0].update(tool_id="GEN"), "reserved")
        self.assertInvalid(lambda c: c["tools"][0].update(tool_id="claude"), "uppercase")
        self.assertInvalid(lambda c: c["tools"][0].update(tool_id="../X"), "uppercase")

    def test_doc_id_pattern(self):
        self.assertInvalid(lambda c: c.update(doc_id_pattern="{org}-{nn}"), "{tool} and {nn}")
        self.assertInvalid(lambda c: c.update(doc_id_pattern="{org}-{tool}-{nn}-{rev}"),
                           "unknown token")
        self.assertInvalid(lambda c: c.update(doc_id_pattern="{org-{tool}-{nn}"), "braces")

    def test_models_and_policy(self):
        self.assertInvalid(lambda c: c["tools"][0].update(approved_models=[]), "non-empty")
        self.assertInvalid(lambda c: c["tools"][0].update(approved_models=["bad model"]),
                           "not a valid model")
        self.assertInvalid(lambda c: c["tools"][0].update(model_policy="pinned"),
                           "requires pinned_model")
        self.assertInvalid(lambda c: c["tools"][0].update(model_policy="pinned",
                                                          pinned_model="vendor-x"),
                           "does not match any approved_models")
        self.assertInvalid(lambda c: c["tools"][0].update(model_policy="pinned",
                                                          pinned_model="vendor-a-large-*"),
                           "not a pattern")
        self.assertInvalid(lambda c: c["tools"][0].update(pinned_model="vendor-a-large-2"),
                           "only allowed with model_policy 'pinned'")

    def test_no_mustache_in_values(self):
        self.assertInvalid(lambda c: c.update(org_name="Acme {{x}}"), "must not contain")

    def test_all_option_keys_accepted(self):
        cfg = default_config()
        cfg["contexts"] = list(CONTEXT_KEYS)
        cfg["tools"][0]["surfaces"] = list(SURFACE_KEYS)
        self.assertEqual(validate_config(cfg), [])

    def test_not_an_object(self):
        self.assertTrue(validate_config([]))


if __name__ == "__main__":
    unittest.main()
