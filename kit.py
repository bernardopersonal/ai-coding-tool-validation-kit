#!/usr/bin/env python3
"""AI Coding Tool Validation Kit - command line interface.

  python3 kit.py init [--defaults] [--config PATH] [--out DIR] [--docx] [--force]
  python3 kit.py render --config PATH [--out DIR] [--docx]
  python3 kit.py example-config
  python3 kit.py vars [--update README_DEV.md]

Python 3.9+ standard library only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kit import __version__  # noqa: E402
from kit.config import (ConfigError, config_to_json, default_config, load_config,  # noqa: E402
                        variables_markdown)
from kit.package import (DEFAULT_TEMPLATES_DIR, convert_to_docx, render_package,  # noqa: E402
                         write_text_lf)
from kit.render import RenderError  # noqa: E402
from kit.wizard import WizardAbort, confirm, run_wizard  # noqa: E402

VARS_BEGIN = "<!-- BEGIN GENERATED VARIABLES (python3 kit.py vars --update README_DEV.md) -->"
VARS_END = "<!-- END GENERATED VARIABLES -->"

EXIT_OK, EXIT_RENDER, EXIT_CONFIG = 0, 1, 2


def _err(message: str) -> None:
    print(message, file=sys.stderr)


def _render(cfg: dict, args: argparse.Namespace) -> int:
    try:
        written = render_package(cfg, args.templates, args.out)
    except ConfigError as exc:
        _err("Configuration error: %s" % exc)
        return EXIT_CONFIG
    except RenderError as exc:
        _err("Render error: %s" % exc)
        return EXIT_RENDER
    out = Path(args.out)
    print("Rendered %d file(s) into %s/" % (len(written), out))
    for path in written:
        print("  " + str(path.relative_to(out)))
    if args.docx:
        if convert_to_docx(written):
            return EXIT_RENDER
    return EXIT_OK


def cmd_init(args: argparse.Namespace) -> int:
    cfg_path = Path(args.config)
    if args.defaults:
        cfg = default_config()
    else:
        defaults = None
        if cfg_path.exists():
            try:
                defaults = load_config(cfg_path)
                print("Using the answers in %s as defaults.\n" % cfg_path)
            except ConfigError as exc:
                print("Ignoring %s as defaults (%s)\n" % (cfg_path, exc))
        try:
            cfg = run_wizard(defaults)
        except WizardAbort as exc:
            _err("Wizard aborted: %s" % exc)
            return EXIT_CONFIG
    text = config_to_json(cfg)
    if cfg_path.exists() and cfg_path.read_text(encoding="utf-8") != text and not args.force:
        if args.defaults:
            _err("%s already exists with different content; not overwriting. Use --force, "
                 "or 'python3 kit.py render --config %s'." % (cfg_path, cfg_path))
            return EXIT_CONFIG
        try:
            if not confirm("Overwrite %s?" % cfg_path, default=True):
                _err("Not overwritten; nothing rendered.")
                return EXIT_CONFIG
        except WizardAbort as exc:
            _err("Aborted: %s" % exc)
            return EXIT_CONFIG
    if cfg_path.parent and not cfg_path.parent.exists():
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(cfg_path, text)
    print("Wrote %s" % cfg_path)
    return _render(cfg, args)


def cmd_render(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        _err("Configuration error: %s" % exc)
        return EXIT_CONFIG
    return _render(cfg, args)


def cmd_example_config(args: argparse.Namespace) -> int:
    sys.stdout.write(config_to_json(default_config()))
    return EXIT_OK


def update_generated_block(path: Path) -> bool:
    """Replace the generated variables block in ``path``; True if it changed."""
    text = path.read_text(encoding="utf-8")
    if VARS_BEGIN not in text or VARS_END not in text:
        raise ValueError("%s has no generated-variables markers" % path)
    head, rest = text.split(VARS_BEGIN, 1)
    _, tail = rest.split(VARS_END, 1)
    new = head + VARS_BEGIN + "\n\n" + variables_markdown() + "\n" + VARS_END + tail
    if new != text:
        write_text_lf(path, new)
        return True
    return False


def cmd_vars(args: argparse.Namespace) -> int:
    if args.update:
        try:
            changed = update_generated_block(Path(args.update))
        except (OSError, ValueError) as exc:
            _err(str(exc))
            return EXIT_CONFIG
        print("%s %s" % (args.update, "updated" if changed else "already up to date"))
        return EXIT_OK
    sys.stdout.write(variables_markdown())
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kit.py", description="AI Coding Tool Validation Kit: configure and render a "
                                   "validation package for AI coding assistants.")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    def add_render_options(p: argparse.ArgumentParser) -> None:
        p.add_argument("--out", default="output", metavar="DIR",
                       help="output directory (default: output)")
        p.add_argument("--docx", action="store_true",
                       help="also convert each .md to .docx with pandoc (if installed)")
        p.add_argument("--templates", default=str(DEFAULT_TEMPLATES_DIR), metavar="DIR",
                       help="templates directory (default: the kit's templates/)")

    p_init = sub.add_parser("init", help="run the wizard, write the config and render")
    p_init.add_argument("--defaults", action="store_true",
                        help="skip the questions and use the default (example) answers")
    p_init.add_argument("--config", default="kit.config.json", metavar="PATH",
                        help="config file to write (default: kit.config.json)")
    p_init.add_argument("--force", action="store_true",
                        help="overwrite an existing config without asking")
    add_render_options(p_init)
    p_init.set_defaults(func=cmd_init)

    p_render = sub.add_parser("render", help="render the package from an existing config")
    p_render.add_argument("--config", required=True, metavar="PATH", help="config file (JSON)")
    add_render_options(p_render)
    p_render.set_defaults(func=cmd_render)

    p_example = sub.add_parser("example-config", help="print the default config as JSON")
    p_example.set_defaults(func=cmd_example_config)

    p_vars = sub.add_parser("vars", help="print the reference of template variables")
    p_vars.add_argument("--update", metavar="FILE",
                        help="rewrite the generated variables block in FILE")
    p_vars.set_defaults(func=cmd_vars)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
