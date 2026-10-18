"""Strict, mustache-like template engine (Python 3.9+ standard library only).

Supported syntax (nothing else):

* ``{{name}}`` / ``{{a.b.c}}`` -- variable substitution. Booleans render as
  ``yes`` / ``no``; numbers via ``str()``; lists, dicts and ``None`` are errors.
* ``{{.}}`` -- the current item (only inside a section that pushed a scalar,
  e.g. a loop over a list of strings).
* ``{{#name}} ... {{/name}}`` -- section. Rendered when the value is truthy.
  A list renders the block once per item with the item pushed on the context
  stack; a dict (or any other truthy value) is pushed and rendered once.
* ``{{^name}} ... {{/name}}`` -- inverted section, rendered once when the value
  is falsy (``False``, ``None``, ``""``, ``0``, empty list/dict).

Rules:

* Names are looked up from the top of the context stack downwards (the
  innermost section item first, the global context last). Dotted names
  resolve the first part through the stack, the rest inside that value.
* STRICT: an unknown variable or section name is a :class:`RenderError`, also
  inside blocks that are not rendered for the current data (a static check
  walks every branch before rendering). Unbalanced tags, malformed tags and
  any other tag syntax (comments, partials, triple braces...) are errors.
* Standalone lines: a line that contains only section tags (``#``, ``^``,
  ``/``) and whitespace is removed entirely, newline included, so section
  tags on their own lines never leave blank lines behind.
* After rendering, whitespace-only lines are emptied, runs of 3+ blank lines
  are collapsed to 2, the output ends with exactly one newline, and any
  leftover ``{{`` is an error.
"""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

__all__ = ["RenderError", "Template", "parse", "render", "render_file"]

_TAG_RE = re.compile(r"\{\{(.*?)\}\}")
_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
_SECTION_SIGILS = ("#", "^", "/")
_SUPPORTED = "only {{name}}, {{.}}, {{#name}}, {{^name}} and {{/name}} are supported"


class RenderError(Exception):
    """Template or rendering error, always carrying the template path."""

    def __init__(self, message: str, template: str = "<string>",
                 line: Optional[int] = None, name: Optional[str] = None) -> None:
        self.message = message
        self.template = template
        self.line = line
        self.name = name
        location = template if line is None else "%s:%d" % (template, line)
        super().__init__("%s: %s" % (location, message))


# --------------------------------------------------------------------------
# Parse tree
# --------------------------------------------------------------------------

class _Text:
    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        self.text = text


class _Var:
    __slots__ = ("name", "line")

    def __init__(self, name: str, line: int) -> None:
        self.name = name
        self.line = line


class _Section:
    __slots__ = ("name", "inverted", "line", "children")

    def __init__(self, name: str, inverted: bool, line: int) -> None:
        self.name = name
        self.inverted = inverted
        self.line = line
        self.children: List[Any] = []


Node = Union[_Text, _Var, _Section]


def _parse_tag(inner: str, line: int, path: str):
    content = inner.strip()
    if not content:
        raise RenderError("empty tag '{{%s}}'" % inner, path, line)
    sigil = ""
    if content[0] in _SECTION_SIGILS:
        sigil = content[0]
        name = content[1:].strip()
    elif not (content[0].isalpha() or content[0] in "_."):
        raise RenderError("unsupported tag syntax '{{%s}}' (%s)" % (inner, _SUPPORTED),
                          path, line)
    else:
        name = content
    if name == ".":
        if sigil:
            raise RenderError("'.' cannot be used as a section name in '{{%s}}'" % inner,
                              path, line, ".")
    elif not _NAME_RE.match(name):
        raise RenderError("invalid name in tag '{{%s}}' (%s)" % (inner, _SUPPORTED),
                          path, line, name or None)
    return ("tag", sigil, name, line)


def _check_text(segment: str, line: int, path: str) -> None:
    if "{{" in segment:
        raise RenderError("malformed or unclosed tag near %r (tags must open and close "
                          "on the same line)" % segment[segment.index("{{"):][:40], path, line)


def _tokenize(text: str, path: str) -> list:
    tokens: list = []
    lines = text.replace("\r\n", "\n").split("\n")
    last = len(lines) - 1
    for idx, raw in enumerate(lines):
        lineno = idx + 1
        pieces: list = []
        pos = 0
        for match in _TAG_RE.finditer(raw):
            segment = raw[pos:match.start()]
            _check_text(segment, lineno, path)
            if segment:
                pieces.append(("text", segment))
            pieces.append(_parse_tag(match.group(1), lineno, path))
            pos = match.end()
        tail = raw[pos:]
        _check_text(tail, lineno, path)
        if tail:
            pieces.append(("text", tail))
        tags = [p for p in pieces if p[0] == "tag"]
        standalone = bool(tags) and all(t[1] in _SECTION_SIGILS for t in tags) and all(
            p[1].strip() == "" for p in pieces if p[0] == "text")
        if standalone:
            tokens.extend(tags)  # drop the whole line, newline included
        else:
            tokens.extend(pieces)
            if idx != last:
                tokens.append(("text", "\n"))
    return tokens


def parse(text: str, path: str = "<string>") -> List[Node]:
    """Parse template text into a node tree; raises RenderError on bad syntax."""
    root: List[Node] = []
    stack: List[tuple] = [(None, root)]
    for token in _tokenize(text, path):
        children = stack[-1][1]
        if token[0] == "text":
            if children and isinstance(children[-1], _Text):
                children[-1].text += token[1]
            else:
                children.append(_Text(token[1]))
            continue
        _, sigil, name, line = token
        if sigil in ("#", "^"):
            node = _Section(name, sigil == "^", line)
            children.append(node)
            stack.append((node, node.children))
        elif sigil == "/":
            if len(stack) == 1:
                raise RenderError("closing tag '{{/%s}}' has no matching opening tag" % name,
                                  path, line, name)
            open_node = stack[-1][0]
            if open_node.name != name:
                raise RenderError(
                    "closing tag '{{/%s}}' does not match open section '{{%s%s}}' "
                    "(opened at line %d)" % (name, "^" if open_node.inverted else "#",
                                             open_node.name, open_node.line),
                    path, line, name)
            stack.pop()
        else:
            children.append(_Var(name, line))
    if len(stack) > 1:
        open_node = stack[-1][0]
        raise RenderError("section '{{%s%s}}' is never closed" % (
            "^" if open_node.inverted else "#", open_node.name),
            path, open_node.line, open_node.name)
    return root


# --------------------------------------------------------------------------
# Static check: every name in every branch must resolve
# --------------------------------------------------------------------------

_ANY = ("any",)        # unknown shape (e.g. items of an empty list): accept anything
_SCALAR = ("scalar",)


def _merge_schemas(schemas: List[tuple]) -> tuple:
    if not schemas:
        return _ANY
    kinds = {s[0] for s in schemas}
    if kinds == {"dict"}:
        keys: Dict[str, List[tuple]] = {}
        for s in schemas:
            for k, v in s[1].items():
                keys.setdefault(k, []).append(v)
        return ("dict", {k: _merge_schemas(v) for k, v in keys.items()})
    if kinds == {"list"}:
        return ("list", _merge_schemas([s[1] for s in schemas]))
    if kinds == {"scalar"}:
        return _SCALAR
    return _ANY


def _infer_schema(value: Any) -> tuple:
    if isinstance(value, dict):
        return ("dict", {k: _infer_schema(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return ("list", _merge_schemas([_infer_schema(v) for v in value]))
    return _SCALAR


def _suggest(name: str, candidates: Iterable[str]) -> str:
    close = difflib.get_close_matches(name, sorted(set(candidates)), n=1, cutoff=0.75)
    return " (did you mean '%s'?)" % close[0] if close else ""


# --------------------------------------------------------------------------
# Template
# --------------------------------------------------------------------------

Stack = Union[Dict[str, Any], Sequence[Any]]


def _as_stack(stack: Stack) -> List[Any]:
    if isinstance(stack, dict):
        return [stack]
    frames = list(stack)
    if not frames:
        raise ValueError("context stack must contain at least one frame")
    return frames


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, tuple, dict)):
        return len(value) > 0
    return bool(value)


def _tidy(text: str) -> str:
    out: List[str] = []
    blank_run = 0
    for line in text.split("\n"):
        if line.strip() == "":
            blank_run += 1
            if blank_run <= 2:
                out.append("")
        else:
            blank_run = 0
            out.append(line)
    result = "\n".join(out).rstrip("\n")
    return result + "\n" if result.strip() else ""


class Template:
    """A parsed template. ``render(stack)`` takes a dict or a list of frames
    (bottom first, e.g. ``[global_ctx, tool_ctx]``)."""

    def __init__(self, text: str, path: Union[str, Path] = "<string>") -> None:
        self.path = str(path)
        self.nodes = parse(text, self.path)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "Template":
        with open(path, "r", encoding="utf-8") as handle:
            return cls(handle.read(), path)

    # -- errors ------------------------------------------------------------
    def _error(self, message: str, line: Optional[int], name: Optional[str]) -> RenderError:
        return RenderError(message, self.path, line, name)

    # -- static check ------------------------------------------------------
    def check(self, stack: Stack) -> None:
        """Verify that every name used in any branch resolves against the shape
        of ``stack`` (inferred from its data). Raises RenderError."""
        self._check_nodes(self.nodes, [_infer_schema(f) for f in _as_stack(stack)])

    def _resolve_schema(self, frames: List[tuple], name: str, line: int, kind: str) -> tuple:
        top = frames[-1]
        if name == ".":
            if top is _ANY or top == _SCALAR:
                return top
            raise self._error("'{{.}}' used where the current item is not a scalar "
                              "(use it only inside a loop over a list of strings)", line, ".")
        parts = name.split(".")
        found: Optional[tuple] = None
        for frame in reversed(frames):
            if frame is _ANY:
                return _ANY
            if frame[0] == "dict" and parts[0] in frame[1]:
                found = frame[1][parts[0]]
                break
        if found is None:
            known = [k for f in frames if f[0] == "dict" for k in f[1]]
            raise self._error("unknown %s '%s'%s" % (kind, name, _suggest(parts[0], known)),
                              line, name)
        for i, part in enumerate(parts[1:], start=1):
            if found is _ANY:
                return _ANY
            if found[0] == "dict" and part in found[1]:
                found = found[1][part]
            else:
                raise self._error("unknown %s '%s' ('%s' has no key '%s')" % (
                    kind, name, ".".join(parts[:i]), part), line, name)
        return found

    def _check_nodes(self, nodes: List[Node], frames: List[tuple]) -> None:
        for node in nodes:
            if isinstance(node, _Text):
                continue
            if isinstance(node, _Var):
                schema = self._resolve_schema(frames, node.name, node.line, "variable")
                if schema is not _ANY and schema[0] in ("dict", "list"):
                    raise self._error("variable '%s' is a %s and cannot be output; use a "
                                      "section '{{#%s}}...{{/%s}}'" % (
                                          node.name, schema[0], node.name, node.name),
                                      node.line, node.name)
                continue
            schema = self._resolve_schema(frames, node.name, node.line, "section")
            if node.inverted:
                self._check_nodes(node.children, frames)
            elif schema is _ANY:
                self._check_nodes(node.children, frames + [_ANY])
            elif schema[0] == "list":
                self._check_nodes(node.children, frames + [schema[1]])
            else:
                self._check_nodes(node.children, frames + [schema])

    # -- rendering ---------------------------------------------------------
    def _lookup(self, stack: List[Any], name: str, line: int, kind: str) -> Any:
        if name == ".":
            top = stack[-1]
            if len(stack) == 1 or isinstance(top, (dict, list, tuple)) or top is None:
                raise self._error("'{{.}}' used where the current item is not a scalar "
                                  "(use it only inside a loop over a list of strings)",
                                  line, ".")
            return top
        parts = name.split(".")
        for frame in reversed(stack):
            if isinstance(frame, dict) and parts[0] in frame:
                value = frame[parts[0]]
                break
        else:
            known = [k for f in stack if isinstance(f, dict) for k in f]
            raise self._error("unknown %s '%s'%s" % (kind, name, _suggest(parts[0], known)),
                              line, name)
        for i, part in enumerate(parts[1:], start=1):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                raise self._error("unknown %s '%s' ('%s' has no key '%s')" % (
                    kind, name, ".".join(parts[:i]), part), line, name)
        return value

    def _format(self, value: Any, node: _Var) -> str:
        if isinstance(value, bool):
            return "yes" if value else "no"
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            return str(value)
        if value is None:
            raise self._error("variable '%s' is null" % node.name, node.line, node.name)
        raise self._error("variable '%s' is a %s and cannot be output; use a section "
                          "'{{#%s}}...{{/%s}}'" % (node.name, type(value).__name__,
                                                   node.name, node.name),
                          node.line, node.name)

    def _render_nodes(self, nodes: List[Node], stack: List[Any], out: List[str]) -> None:
        for node in nodes:
            if isinstance(node, _Text):
                out.append(node.text)
            elif isinstance(node, _Var):
                out.append(self._format(self._lookup(stack, node.name, node.line, "variable"),
                                        node))
            else:
                value = self._lookup(stack, node.name, node.line, "section")
                if node.inverted:
                    if not _truthy(value):
                        self._render_nodes(node.children, stack, out)
                elif isinstance(value, (list, tuple)):
                    for item in value:
                        self._render_nodes(node.children, stack + [item], out)
                elif _truthy(value):
                    self._render_nodes(node.children, stack + [value], out)

    def render(self, stack: Stack, check: bool = True) -> str:
        frames = _as_stack(stack)
        if check:
            self.check(frames)
        out: List[str] = []
        self._render_nodes(self.nodes, frames, out)
        text = _tidy("".join(out))
        if "{{" in text:
            lineno = text[:text.index("{{")].count("\n") + 1
            snippet = text.splitlines()[lineno - 1].strip()[:80]
            raise RenderError("leftover '{{' in rendered output at output line %d: %r "
                              "(a value or literal text contains '{{')" % (lineno, snippet),
                              self.path)
        return text


def render(text: str, stack: Stack, path: Union[str, Path] = "<string>") -> str:
    """Parse and render ``text`` in one go."""
    return Template(text, path).render(stack)


def render_file(path: Union[str, Path], stack: Stack) -> str:
    """Read, parse and render the template at ``path``."""
    return Template.from_file(path).render(stack)
