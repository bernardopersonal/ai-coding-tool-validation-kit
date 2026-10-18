"""Unit tests for the template engine (kit/render.py)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kit.render import RenderError, Template, parse, render, render_file  # noqa: E402


def r(text, *frames):
    return render(text, list(frames) if frames else [{}], "t.md.tmpl")


class VariableTests(unittest.TestCase):
    def test_substitution(self):
        self.assertEqual(r("Hello {{name}}!", {"name": "Acme"}), "Hello Acme!\n")

    def test_whitespace_inside_tags(self):
        self.assertEqual(r("{{ name }}/{{# on }}x{{/ on }}", {"name": "a", "on": True}),
                         "a/x\n")

    def test_booleans_render_yes_no(self):
        self.assertEqual(r("{{a}} {{b}}", {"a": True, "b": False}), "yes no\n")

    def test_numbers(self):
        self.assertEqual(r("{{n}} months", {"n": 12}), "12 months\n")

    def test_dotted_names(self):
        self.assertEqual(r("{{a.b.c}}", {"a": {"b": {"c": "deep"}}}), "deep\n")

    def test_no_html_escaping(self):
        self.assertEqual(r("{{v}}", {"v": "<a & b>"}), "<a & b>\n")

    def test_stack_lookup_order(self):
        glob = {"name": "global", "only_global": "g"}
        tool = {"name": "tool"}
        self.assertEqual(r("{{name}} {{only_global}}", glob, tool), "tool g\n")

    def test_single_braces_are_text(self):
        self.assertEqual(r("{org}-{tool} {\"a\": {\"b\": 1}}", {}),
                         "{org}-{tool} {\"a\": {\"b\": 1}}\n")


class SectionTests(unittest.TestCase):
    def test_truthy_and_falsy_bool(self):
        self.assertEqual(r("{{#on}}A{{/on}}{{#off}}B{{/off}}", {"on": True, "off": False}),
                         "A\n")

    def test_inverted_sections(self):
        ctx = {"off": False, "empty": [], "blank": "", "zero": 0, "none": None, "on": True,
               "items": ["x"]}
        self.assertEqual(
            r("{{^off}}1{{/off}}{{^empty}}2{{/empty}}{{^blank}}3{{/blank}}"
              "{{^zero}}4{{/zero}}{{^none}}5{{/none}}{{^on}}X{{/on}}{{^items}}Y{{/items}}",
              ctx), "12345\n")

    def test_list_of_dicts_iterates(self):
        ctx = {"tools": [{"n": "A"}, {"n": "B"}]}
        self.assertEqual(r("{{#tools}}[{{n}}]{{/tools}}", ctx), "[A][B]\n")

    def test_list_of_scalars_with_dot(self):
        self.assertEqual(r("{{#m}}<{{.}}>{{/m}}", {"m": ["x*", "y"]}), "<x*><y>\n")

    def test_empty_list_renders_nothing(self):
        self.assertEqual(r("a{{#m}}<{{.}}>{{/m}}b", {"m": []}), "ab\n")

    def test_dict_section_pushes(self):
        self.assertEqual(r("{{#org}}{{name}}{{/org}}", {"org": {"name": "Acme"}}), "Acme\n")

    def test_string_section_pushes_value(self):
        ctx = {"prrc": "Jane Roe"}
        self.assertEqual(r("{{#prrc}}PRRC: {{.}} / {{prrc}}{{/prrc}}", ctx),
                         "PRRC: Jane Roe / Jane Roe\n")
        self.assertEqual(r("x{{#prrc}}PRRC{{/prrc}}", {"prrc": ""}), "x\n")

    def test_nested_loops_and_outer_scope(self):
        ctx = {"org": "Acme", "tools": [
            {"id": "A", "models": ["m1", "m2"]}, {"id": "B", "models": ["m3"]}]}
        text = "{{#tools}}{{id}}:{{#models}}{{.}}@{{org}}/{{id}} {{/models}};{{/tools}}"
        self.assertEqual(r(text, ctx), "A:m1@Acme/A m2@Acme/A ;B:m3@Acme/B ;\n")

    def test_nested_sections_same_and_different_flags(self):
        ctx = {"a": True, "b": False}
        self.assertEqual(r("{{#a}}A{{^b}}notB{{#a}}again{{/a}}{{/b}}{{/a}}", ctx),
                         "AnotBagain\n")

    def test_item_shadows_global(self):
        ctx = {"label": "global", "items": [{"label": "item"}]}
        self.assertEqual(r("{{#items}}{{label}}{{/items}} {{label}}", ctx), "item global\n")


class StandaloneAndWhitespaceTests(unittest.TestCase):
    def test_standalone_section_lines_leave_no_blank_lines(self):
        text = "a\n{{#on}}\nb\n{{/on}}\n{{#off}}\nc\n{{/off}}\nd\n"
        self.assertEqual(r(text, {"on": True, "off": False}), "a\nb\nd\n")

    def test_indented_standalone_and_trailing_spaces(self):
        text = "a\n   {{#on}}  \n  b\n\t{{/on}}\t\nc\n"
        self.assertEqual(r(text, {"on": True}), "a\n  b\nc\n")

    def test_standalone_inverted(self):
        text = "x\n{{^on}}\nno\n{{/on}}\ny\n"
        self.assertEqual(r(text, {"on": True}), "x\ny\n")
        self.assertEqual(r(text, {"on": False}), "x\nno\ny\n")

    def test_line_with_only_several_section_tags_is_standalone(self):
        text = "a\n{{#x}}{{^y}}\nb\n{{/y}}{{/x}}\nc\n"
        self.assertEqual(r(text, {"x": True, "y": False}), "a\nb\nc\n")

    def test_list_iteration_with_standalone_lines(self):
        text = "Models:\n{{#m}}\n- {{.}}\n{{/m}}\nEnd\n"
        self.assertEqual(r(text, {"m": ["a", "b"]}), "Models:\n- a\n- b\nEnd\n")

    def test_inline_section_is_not_standalone(self):
        text = "a {{#on}}b{{/on}}\nc\n"
        self.assertEqual(r(text, {"on": False}), "a \nc\n")

    def test_variable_alone_on_line_is_not_standalone(self):
        self.assertEqual(r("a\n{{v}}\nb\n", {"v": "x"}), "a\nx\nb\n")

    def test_standalone_on_last_line_without_newline(self):
        self.assertEqual(r("a\n{{#on}}\nb\n{{/on}}", {"on": True}), "a\nb\n")

    def test_three_or_more_blank_lines_collapse_to_two(self):
        self.assertEqual(r("a\n\n\n\n\nb\n", {}), "a\n\n\nb\n")
        self.assertEqual(r("a\n\n\nb\n", {}), "a\n\n\nb\n")
        self.assertEqual(r("a\n  \n\t\n \n \nb\n", {}), "a\n\n\nb\n")

    def test_blank_lines_from_empty_sections_collapse(self):
        text = "a\n\n{{#off}}\nx\n{{/off}}\n\n{{#off}}\ny\n{{/off}}\n\n\nb\n"
        self.assertEqual(r(text, {"off": False}), "a\n\n\nb\n")

    def test_single_trailing_newline(self):
        self.assertEqual(r("a\n\n\n", {}), "a\n")
        self.assertEqual(r("a", {}), "a\n")

    def test_crlf_input(self):
        self.assertEqual(r("a\r\n{{#on}}\r\nb\r\n{{/on}}\r\n", {"on": True}), "a\nb\n")


class ErrorTests(unittest.TestCase):
    def assertRenderError(self, text, ctx, *fragments, name=None):
        with self.assertRaises(RenderError) as cm:
            render(text, ctx, "templates/x.md.tmpl")
        message = str(cm.exception)
        self.assertIn("templates/x.md.tmpl", message)
        for fragment in fragments:
            self.assertIn(fragment, message)
        if name is not None:
            self.assertEqual(cm.exception.name, name)
        return cm.exception

    def test_unknown_variable(self):
        exc = self.assertRenderError("a\n{{missing}}", {"x": 1}, "unknown variable 'missing'",
                                     name="missing")
        self.assertEqual(exc.line, 2)
        self.assertEqual(exc.template, "templates/x.md.tmpl")

    def test_unknown_section(self):
        self.assertRenderError("{{#nope}}x{{/nope}}", {}, "unknown section 'nope'", name="nope")
        self.assertRenderError("{{^nope}}x{{/nope}}", {}, "unknown section 'nope'", name="nope")

    def test_unknown_name_inside_unrendered_branch_is_caught(self):
        self.assertRenderError("{{#off}}{{tpyo}}{{/off}}", {"off": False},
                               "unknown variable 'tpyo'", name="tpyo")
        self.assertRenderError("{{^on}}{{#tpyo}}x{{/tpyo}}{{/on}}", {"on": True},
                               "unknown section 'tpyo'")
        self.assertRenderError("{{#items}}{{nme}}{{/items}}", {"items": [{"name": "a"}]},
                               "unknown variable 'nme'")

    def test_suggestion_for_typo(self):
        self.assertRenderError("{{ctx_code_prodct}}", {"ctx_code_product": True},
                               "did you mean 'ctx_code_product'")

    def test_dotted_missing_key(self):
        self.assertRenderError("{{a.c}}", {"a": {"b": 1}}, "'a' has no key 'c'")

    def test_unclosed_section(self):
        self.assertRenderError("{{#a}}x", {"a": True}, "never closed", name="a")

    def test_mismatched_closing_tag(self):
        self.assertRenderError("{{#a}}{{#b}}x{{/a}}{{/b}}", {"a": True, "b": True},
                               "does not match", name="a")

    def test_closing_without_opening(self):
        self.assertRenderError("x{{/a}}", {"a": True}, "no matching opening tag", name="a")

    def test_unclosed_tag(self):
        self.assertRenderError("a {{name\n}}", {"name": "x"}, "malformed or unclosed tag")

    def test_unsupported_syntax(self):
        for text in ("{{!comment}}", "{{>partial}}", "{{&raw}}", "{{{triple}}}",
                     "{{=<% %>=}}", "{{}}", "{{a b}}", "{{#.}}x{{/.}}", "{{9x}}", "{{.a}}"):
            with self.subTest(text=text):
                with self.assertRaises(RenderError):
                    render(text, {"a": 1, "raw": 1, "triple": 1}, "t")

    def test_dot_outside_scalar_section(self):
        self.assertRenderError("{{.}}", {"a": 1}, "'{{.}}'")
        self.assertRenderError("{{#items}}{{.}}{{/items}}", {"items": [{"a": 1}]}, "'{{.}}'")

    def test_list_or_dict_as_variable(self):
        self.assertRenderError("{{items}}", {"items": ["a"]}, "cannot be output")
        self.assertRenderError("{{d}}", {"d": {"a": 1}}, "cannot be output")

    def test_null_value(self):
        self.assertRenderError("{{v}}", {"v": None}, "is null")

    def test_leftover_braces_from_value(self):
        self.assertRenderError("x {{v}}", {"v": "{{oops}}"}, "leftover '{{'")

    def test_error_line_numbers(self):
        with self.assertRaises(RenderError) as cm:
            parse("line1\nline2\n{{#a}}\n", "p.tmpl")
        self.assertEqual(cm.exception.line, 3)
        self.assertTrue(str(cm.exception).startswith("p.tmpl:3:"))


class ApiTests(unittest.TestCase):
    def test_template_reuse_and_check(self):
        tpl = Template("{{#items}}{{.}}{{/items}}", "t")
        self.assertEqual(tpl.render({"items": [1, 2]}), "12\n")
        self.assertEqual(tpl.render([{"items": ["a"]}]), "a\n")
        tpl.check({"items": []})  # empty list: item shape unknown, accepted

    def test_render_file_reports_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "01-doc.md.tmpl")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("ok {{a}}\n{{b}}\n")
            self.assertRaises(RenderError, render_file, path, {"a": 1})
            try:
                render_file(path, {"a": 1})
            except RenderError as exc:
                self.assertIn(path, str(exc))
                self.assertEqual(exc.name, "b")
            self.assertEqual(render_file(path, {"a": 1, "b": 2}), "ok 1\n2\n")


if __name__ == "__main__":
    unittest.main()
