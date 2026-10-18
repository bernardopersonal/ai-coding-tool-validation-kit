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

    def expected_files(self, tool_ids):
        paths = discover_templates(REPO / "templates")
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
        self.assertEqual(run("--version").returncode, 0)

    def test_example_config(self):
        proc = run("example-config")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        cfg = json.loads(proc.stdout)
        self.assertEqual(cfg, default_config())
        self.assertEqual(validate_config(cfg), [])

    def test_init_defaults_then_render(self):
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        proc = run("init", "--defaults", "--config", str(cfg_path), "--out", str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(cfg_path.read_text(encoding="utf-8")), default_config())
        self.assertEqual(self.rendered(out), self.expected_files(["CLAUDE", "CODEX"]))
        # re-running with identical defaults is fine
        proc = run("init", "--defaults", "--config", str(cfg_path), "--out", str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # render from the written config into another directory
        out2 = self.tmp / "out2"
        proc = run("render", "--config", str(cfg_path), "--out", str(out2))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.rendered(out2), self.rendered(out))

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
        proc = run("init", "--defaults", "--force", "--config", str(cfg_path), "--out",
                   str(self.tmp / "o"))
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_interactive_init_accepting_defaults(self):
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        proc = run("init", "--config", str(cfg_path), "--out", str(out), stdin="\n" * 200)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(json.loads(cfg_path.read_text(encoding="utf-8")), default_config())

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
        proc = run("init", "--defaults", "--docx", "--config", str(cfg_path), "--out",
                   str(out), env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("pandoc not found", proc.stdout)
        self.assertEqual(list(out.rglob("*.docx")), [])

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc not installed")
    def test_docx_with_pandoc(self):
        cfg_path, out = self.tmp / "kit.config.json", self.tmp / "out"
        proc = run("init", "--defaults", "--docx", "--config", str(cfg_path), "--out",
                   str(out))
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
