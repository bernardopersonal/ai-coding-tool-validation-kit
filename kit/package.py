"""Render the validation package: templates/*.md.tmpl -> output/.

* ``00-<name>.md.tmpl``  -> ``<out>/00-shared/<name>.md`` (context stack [global])
* ``NN-<name>.md.tmpl``  -> ``<out>/<TOOL_ID>/NN-<name>.md`` once per tool
  (context stack [global, tool])

Everything is rendered in memory first; files are written only if every
template rendered without error.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .config import derive
from .render import RenderError, Template

TEMPLATE_SUFFIX = ".md.tmpl"
SHARED_PREFIX = "00-"
SHARED_DIR = "00-shared"
DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

PathLike = Union[str, Path]


def discover_templates(templates_dir: PathLike) -> List[Path]:
    """All ``*.md.tmpl`` files in ``templates_dir``, sorted by name."""
    return sorted(p for p in Path(templates_dir).glob("*" + TEMPLATE_SUFFIX) if p.is_file())


def is_shared(template: PathLike) -> bool:
    return Path(template).name.startswith(SHARED_PREFIX)


def output_name(template: PathLike) -> str:
    name = Path(template).name[: -len(".tmpl")]
    return name[len(SHARED_PREFIX):] if is_shared(template) else name


def load_templates(templates_dir: PathLike) -> List[Template]:
    paths = discover_templates(templates_dir)
    if not paths:
        raise RenderError("no *%s templates found" % TEMPLATE_SUFFIX, str(templates_dir))
    return [Template.from_file(p) for p in paths]


def render_all(cfg: Dict[str, Any], templates: List[Template],
               today: Optional[str] = None) -> List[Tuple[str, str]]:
    """Render every template; returns [(relative output path, text)]."""
    ctx = derive(cfg, today=today)
    results: List[Tuple[str, str]] = []
    for tpl in templates:
        name = output_name(tpl.path)
        if is_shared(tpl.path):
            results.append(("%s/%s" % (SHARED_DIR, name), tpl.render([ctx])))
        else:
            for tool in ctx["tools_list"]:
                results.append(("%s/%s" % (tool["tool_id"], name), tpl.render([ctx, tool])))
    return results


def write_text_lf(path: PathLike, text: str) -> None:
    """Write UTF-8 text with LF line endings (Path.write_text(newline=) is 3.10+)."""
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def render_package(cfg: Dict[str, Any], templates_dir: PathLike, out_dir: PathLike,
                   today: Optional[str] = None) -> List[Path]:
    """Render all templates and write them under ``out_dir``; returns written paths."""
    results = render_all(cfg, load_templates(templates_dir), today=today)
    out = Path(out_dir)
    written: List[Path] = []
    for rel, text in results:
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        write_text_lf(target, text)
        written.append(target)
    return written


def convert_to_docx(md_files: List[Path], print_fn: Callable[..., None] = print) -> int:
    """Convert each .md to .docx next to it with pandoc. Returns the number of
    failures. If pandoc is not installed, prints a notice and returns 0."""
    pandoc = shutil.which("pandoc")
    if not pandoc:
        print_fn("Notice: pandoc not found on PATH; skipping .docx conversion "
                 "(the Markdown files are complete).")
        return 0
    failures = 0
    for md in md_files:
        docx = md.with_suffix(".docx")
        proc = subprocess.run([pandoc, str(md), "-f", "markdown", "-o", str(docx)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)
        if proc.returncode != 0:
            failures += 1
            print_fn("Warning: pandoc failed for %s: %s" % (md, proc.stderr.strip()))
    return failures
