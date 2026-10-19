"""Render the validation package: templates/<profile>/*.md.tmpl -> output/.

The template set is chosen by the profile (``lite`` or ``full``):
``templates/lite/`` or ``templates/full/``.

* ``00-<name>.md.tmpl``  -> ``<out>/00-shared/<name>.md`` (context stack [global])
* ``NN-<name>.md.tmpl``  -> ``<out>/<TOOL_ID>/NN-<name>.md`` once per tool
  (context stack [global, tool])

Everything is rendered in memory first; files are written only if every
template rendered without error.

Without ``force``, :func:`render_package` refuses (:class:`RenderRefused`)
to render the lite profile when the answers contain a hard stop (L1, L2, L8,
L9; :func:`kit.config.lite_blockers`), and to write into a directory that
holds per-tool documents of the other profile (whose shared documents have the
same names and would be overwritten).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .config import (PROFILE_KEYS, ConfigError, derive, effective_profile, lite_blockers,
                     validate_config)
from .render import RenderError, Template

TEMPLATE_SUFFIX = ".md.tmpl"
SHARED_PREFIX = "00-"
SHARED_DIR = "00-shared"
TEMPLATES_ROOT = Path(__file__).resolve().parent.parent / "templates"

PathLike = Union[str, Path]


class RenderRefused(Exception):
    """Rendering was refused for a reason that ``force`` overrides."""


def profile_templates_dir(profile: str, root: PathLike = TEMPLATES_ROOT) -> Path:
    """``<root>/<profile>/``, e.g. the kit's ``templates/lite/``."""
    if profile not in PROFILE_KEYS:
        raise ValueError("unknown profile %r; allowed: %s" % (profile, ", ".join(PROFILE_KEYS)))
    return Path(root) / profile


def resolve_templates_dir(templates_dir: Optional[PathLike], profile: str) -> Path:
    """Template directory for ``profile``.

    ``None`` selects the kit's ``templates/<profile>/``. A directory that has a
    ``<profile>/`` subdirectory (a copy of the kit's ``templates/``) selects
    that subdirectory; any other directory is used as it is.
    """
    if templates_dir is None:
        return profile_templates_dir(profile)
    path = Path(templates_dir)
    sub = path / profile
    return sub if sub.is_dir() else path


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
               today: Optional[str] = None,
               profile: Optional[str] = None,
               config_file: Optional[str] = None) -> List[Tuple[str, str]]:
    """Render every template; returns [(relative output path, text)].

    ``profile`` overrides the config's profile in the template context. No
    refusal checks here (see :func:`render_package`).
    """
    ctx = derive(cfg, today=today, profile=profile, config_file=config_file)
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


def other_profile_files(out_dir: PathLike, profile: str) -> List[str]:
    """Per-tool documents of the other profile found under ``out_dir`` (relative paths)."""
    out = Path(out_dir)
    if not out.is_dir():
        return []
    mine = {output_name(p) for p in discover_templates(profile_templates_dir(profile))
            if not is_shared(p)}
    others = set()
    for other in PROFILE_KEYS:
        if other != profile:
            others |= {output_name(p) for p in discover_templates(profile_templates_dir(other))
                       if not is_shared(p)}
    others -= mine
    return sorted(str(p.relative_to(out)).replace("\\", "/") for p in out.glob("*/*.md")
                  if p.is_file() and p.name in others)


def render_package(cfg: Dict[str, Any], templates_dir: Optional[PathLike], out_dir: PathLike,
                   today: Optional[str] = None, profile: Optional[str] = None,
                   force: bool = False, config_file: Optional[str] = None) -> List[Path]:
    """Render all templates and write them under ``out_dir``; returns written paths.

    ``profile`` overrides the config's ``profile``. ``templates_dir`` ``None``
    selects the kit's ``templates/<profile>/`` (see :func:`resolve_templates_dir`).
    Raises :class:`RenderRefused` unless ``force`` for a lite render with a hard
    stop, or an output directory holding the other profile's documents.
    """
    errors = validate_config(cfg)
    if errors:
        raise ConfigError(errors)
    profile = effective_profile(cfg, profile)
    if not force:
        blockers = lite_blockers(cfg) if profile == "lite" else []
        if blockers:
            raise RenderRefused(
                "the lite profile is not valid for these answers (hard stop):\n  - %s\n"
                "Render the full profile (--profile full --out output-full), or pass --force "
                "to render lite marked NOT VALID FOR RELEASE." % "\n  - ".join(blockers))
        clash = other_profile_files(out_dir, profile)
        if clash:
            raise RenderRefused(
                "%s holds documents of the other profile (%s%s); its shared documents would "
                "be overwritten. Render each profile into its own directory (--out), or pass "
                "--force." % (out_dir, ", ".join(clash[:3]), ", ..." if len(clash) > 3 else ""))
    tdir = resolve_templates_dir(templates_dir, profile)
    results = render_all(cfg, load_templates(tdir), today=today, profile=profile,
                         config_file=config_file)
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
