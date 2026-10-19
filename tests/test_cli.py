"""End-to-end tests of the kit.py command line."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kit.config import config_to_json, default_config, validate_config  # noqa: E402
from kit.package import discover_templates, is_shared, output_name  # noqa: E402

KIT = str(REPO / "kit.py")


def run(*args, cwd=None, env=None, stdin=""):
    return subprocess.run([sys.executable, KIT] + list(args), cwd=cwd, env=env, input=stdin,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True, timeout=120)


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def expected_files(self, tool_ids, profile="full"):
        paths = discover_templates(REPO / "templates" / profile)
        files = ["00-shared/" + output_name(p) for p in paths if is_shared(p)]
        files += ["%s/%s" % (t, output_name(p)) for t in tool_ids for p in paths
                  if not is_shared(p)]
        return sorted(files)

    def rendered(self, out):
        return sorted(str(p.relative_to(out)).replace(os.sep, "/")
                      for p in out.rglob("*.md"))

    def test_help_and_version(self):
        proc = run("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for command in ("init", "render", "example-config"):
            self.assertIn(command, proc.stdout)
        for command in ("init", "render"):
            proc = run(command, "--help")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("--profile", proc.stdout)
        self.assertEqual(run("--version").returncode, 0)

    def test_example_config(self):
        proc = run("example-config")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        cfg = json.loads(proc.stdout)
        self.assertEqual(cfg, default_config())
        self.assertEqual(validate_config(cfg), [])

    def test_init_defaults_then_render(self):
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        proc = run("init", "--defaults", "--profile", "full", "--config", str(cfg_path),
                   "--out", str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(cfg_path.read_text(encoding="utf-8")),
                         dict(default_config(), profile="full"))
        self.assertIn("Profile: full", proc.stdout)
        self.assertEqual(self.rendered(out), self.expected_files(["CLAUDE", "CODEX"]))
        # re-running with identical defaults is fine
        proc = run("init", "--defaults", "--profile", "full", "--config", str(cfg_path),
                   "--out", str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # render from the written config into another directory
        out2 = self.tmp / "out2"
        proc = run("render", "--config", str(cfg_path), "--out", str(out2))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.rendered(out2), self.rendered(out))

    def test_init_defaults_is_lite_without_warning(self):
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        proc = run("init", "--defaults", "--config", str(cfg_path), "--out", str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(cfg_path.read_text(encoding="utf-8")), default_config())
        self.assertEqual(default_config()["profile"], "lite")
        self.assertIn("Profile: lite", proc.stdout)
        # the default answers match the lite example: no trigger for the full profile
        self.assertNotIn("Warning: the full profile", proc.stdout)
        self.assertEqual(self.rendered(out), self.expected_files(["CLAUDE", "CODEX"], "lite"))
        plan = (out / "CLAUDE" / "01-validation-plan.md").read_text(encoding="utf-8")
        self.assertNotIn("WARNING", plan)
        self.assertNotIn("NOT VALID FOR RELEASE", plan)

    def test_warning_names_the_config_and_a_separate_directory(self):
        cfg = default_config()
        cfg["contexts"].append("doc_drafting")
        cfg_path, out = self.tmp / "my-answers.json", self.tmp / "out"
        cfg_path.write_text(config_to_json(cfg), encoding="utf-8")
        proc = run("render", "--config", str(cfg_path), "--out", str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Warning: the full profile is recommended", proc.stdout)
        command = "--config %s --profile full --out output-full" % cfg_path
        self.assertIn(command, proc.stdout)
        plan = (out / "CLAUDE" / "01-validation-plan.md").read_text(encoding="utf-8")
        self.assertIn("WARNING: the full profile is recommended", plan)
        self.assertIn(command, plan)

    def test_hard_stop_refuses_lite_unless_forced(self):
        cfg = default_config()
        cfg["agent_qms_write"] = True
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        cfg_path.write_text(config_to_json(cfg), encoding="utf-8")
        proc = run("render", "--config", str(cfg_path), "--out", str(out))
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("hard stop", proc.stderr)
        self.assertIn("L2, hard stop", proc.stderr)
        self.assertFalse(out.exists())
        proc = run("render", "--config", str(cfg_path), "--out", str(out), "--force")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("NOT VALID FOR RELEASE", proc.stdout)
        for name in ("01-validation-plan.md", "02-test-record.md", "03-validation-report.md"):
            self.assertIn("NOT VALID FOR RELEASE",
                          (out / "CLAUDE" / name).read_text(encoding="utf-8"))
        proc = run("render", "--config", str(cfg_path), "--out", str(self.tmp / "full"),
                   "--profile", "full")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_render_config_without_profile_is_full_with_notice(self):
        cfg = default_config()
        del cfg["profile"]
        cfg_path, out = self.tmp / "legacy.json", self.tmp / "out"
        cfg_path.write_text(config_to_json(cfg), encoding="utf-8")
        proc = run("render", "--config", str(cfg_path), "--out", str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Notice: the config has no \"profile\" key", proc.stdout)
        self.assertIn("Profile: full", proc.stdout)
        self.assertNotIn("Warning: the full profile is recommended", proc.stdout)
        self.assertEqual(self.rendered(out), self.expected_files(["CLAUDE", "CODEX"]))
        # --profile silences the notice
        proc = run("render", "--config", str(cfg_path), "--out", str(self.tmp / "o2"),
                   "--profile", "full")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("Notice: the config has no", proc.stdout)

    def test_render_profile_overrides_the_config(self):
        cfg = dict(default_config(), profile="full")
        cfg_path = self.tmp / "kit.config.json"
        text = config_to_json(cfg)
        cfg_path.write_text(text, encoding="utf-8")
        out = self.tmp / "lite"
        proc = run("render", "--config", str(cfg_path), "--out", str(out), "--profile", "lite")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Profile: lite", proc.stdout)
        self.assertEqual(self.rendered(out), self.expected_files(["CLAUDE", "CODEX"], "lite"))
        self.assertEqual(cfg_path.read_text(encoding="utf-8"), text, "render must not "
                                                                       "change the config")

    def test_render_profile_full_overrides_a_lite_config(self):
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "full"
        cfg_path.write_text(config_to_json(default_config()), encoding="utf-8")
        proc = run("render", "--config", str(cfg_path), "--out", str(out), "--profile", "full")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("Warning: the full profile is recommended", proc.stdout)
        self.assertEqual(self.rendered(out), self.expected_files(["CLAUDE", "CODEX"]))

    def test_invalid_profile_option(self):
        proc = run("render", "--config", "x.json", "--profile", "medium")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid choice", proc.stderr)

    def test_invalid_profile_in_config(self):
        cfg_path = self.tmp / "bad.json"
        cfg_path.write_text(json.dumps(dict(default_config(), profile="medium")),
                            encoding="utf-8")
        proc = run("render", "--config", str(cfg_path), "--out", str(self.tmp / "o"))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("profile must be one of: lite, full", proc.stderr)
        self.assertFalse((self.tmp / "o").exists())

    def test_templates_root_with_profile_subdirectories(self):
        root = self.tmp / "templates"
        for profile in ("lite", "full"):
            (root / profile).mkdir(parents=True)
            (root / profile / ("01-%s.md.tmpl" % profile)).write_text("# {{profile}}\n",
                                                                     encoding="utf-8")
        cfg_path = self.tmp / "kit.config.json"
        cfg_path.write_text(config_to_json(default_config()), encoding="utf-8")
        for profile in ("lite", "full"):
            out = self.tmp / ("out-" + profile)
            proc = run("render", "--config", str(cfg_path), "--out", str(out), "--templates",
                       str(root), "--profile", profile)
            with self.subTest(profile=profile):
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(self.rendered(out), ["CLAUDE/01-%s.md" % profile,
                                                      "CODEX/01-%s.md" % profile])

    def test_notice_for_files_not_written_by_this_render(self):
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        cfg_path.write_text(config_to_json(dict(default_config(), profile="full")),
                            encoding="utf-8")
        (out / "CLAUDE").mkdir(parents=True)
        (out / "CLAUDE" / "01-validation-plan.md").write_text("old\n", encoding="utf-8")
        proc = run("render", "--config", str(cfg_path), "--out", str(out))
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("other profile", proc.stderr)
        self.assertEqual((out / "CLAUDE" / "01-validation-plan.md").read_text(encoding="utf-8"),
                         "old\n")
        proc = run("render", "--config", str(cfg_path), "--out", str(out), "--force")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("were not written by this render", proc.stdout)
        self.assertIn("01-validation-plan.md", proc.stdout)
        proc = run("render", "--config", str(cfg_path), "--out", str(self.tmp / "clean"))
        self.assertNotIn("were not written by this render", proc.stdout)

    def test_init_defaults_does_not_clobber_edited_config(self):
        cfg_path = self.tmp / "kit.config.json"
        cfg = default_config()
        cfg["org_name"] = "Edited Org"
        cfg_path.write_text(config_to_json(cfg), encoding="utf-8")
        proc = run("init", "--defaults", "--config", str(cfg_path), "--out",
                   str(self.tmp / "o"))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--force", proc.stderr)
        self.assertIn("Edited Org", cfg_path.read_text(encoding="utf-8"))
        proc = run("init", "--defaults", "--profile", "full", "--force", "--config",
                   str(cfg_path), "--out", str(self.tmp / "o"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(cfg_path.read_text(encoding="utf-8")),
                         dict(default_config(), profile="full"))

    def test_init_defaults_with_other_profile_does_not_clobber(self):
        cfg_path = self.tmp / "kit.config.json"
        cfg_path.write_text(config_to_json(default_config()), encoding="utf-8")
        proc = run("init", "--defaults", "--profile", "full", "--config", str(cfg_path),
                   "--out", str(self.tmp / "o"))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(cfg_path.read_text(encoding="utf-8"))["profile"], "lite")

    def test_interactive_init_accepting_defaults(self):
        """The wizard defaults to the recommendation: lite for the example answers."""
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        proc = run("init", "--config", str(cfg_path), "--out", str(out), stdin="\n" * 200)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(json.loads(cfg_path.read_text(encoding="utf-8")), default_config())
        self.assertIn("Recommended for these answers: lite", proc.stdout)
        self.assertEqual(self.rendered(out), self.expected_files(["CLAUDE", "CODEX"], "lite"))

    def test_interactive_init_with_profile_option(self):
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        proc = run("init", "--config", str(cfg_path), "--out", str(out), "--profile", "full",
                   "--templates", str(REPO / "templates"), stdin="\n" * 200)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("set with --profile", proc.stdout)
        self.assertEqual(json.loads(cfg_path.read_text(encoding="utf-8"))["profile"], "full")

    def test_render_invalid_config(self):
        cfg = default_config()
        cfg["role_approver"] = cfg["role_executor"]
        cfg_path = self.tmp / "bad.json"
        cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
        proc = run("render", "--config", str(cfg_path), "--out", str(self.tmp / "o"))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("executor != approver", proc.stderr)
        self.assertFalse((self.tmp / "o").exists())

    def test_render_error_reports_template_and_writes_nothing(self):
        tdir = self.tmp / "templates"
        tdir.mkdir()
        (tdir / "01-good.md.tmpl").write_text("# {{tool_name}}\n", encoding="utf-8")
        (tdir / "02-bad.md.tmpl").write_text("{{#ctx_code_product}}\n{{tool_nme}}\n"
                                             "{{/ctx_code_product}}\n", encoding="utf-8")
        cfg_path = self.tmp / "kit.config.json"
        cfg_path.write_text(config_to_json(default_config()), encoding="utf-8")
        out = self.tmp / "o"
        proc = run("render", "--config", str(cfg_path), "--out", str(out),
                   "--templates", str(tdir))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("02-bad.md.tmpl:2", proc.stderr)
        self.assertIn("tool_nme", proc.stderr)
        self.assertIn("did you mean 'tool_name'", proc.stderr)
        self.assertFalse(out.exists())

    def test_docx_without_pandoc_prints_notice(self):
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        env = dict(os.environ, PATH=str(self.tmp / "empty-path"))
        proc = run("init", "--defaults", "--profile", "full", "--docx", "--config",
                   str(cfg_path), "--out", str(out), env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("pandoc not found", proc.stdout)
        self.assertEqual(list(out.rglob("*.docx")), [])

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc not installed")
    def test_docx_with_pandoc(self):
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        proc = run("init", "--defaults", "--profile", "full", "--docx", "--config",
                   str(cfg_path), "--out", str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(list(out.rglob("*.docx"))), len(list(out.rglob("*.md"))))

    def test_vars_lists_every_variable(self):
        from kit.config import VARIABLES
        proc = run("vars")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for _scope, name, _type, _desc in VARIABLES:
            self.assertIn("`%s`" % name, proc.stdout)


if __name__ == "__main__":
    unittest.main()
