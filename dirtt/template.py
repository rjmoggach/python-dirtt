"""Minimal ``{{name}}`` placeholder substitution.

This intentionally replaces the old embedded Paste template engine
(which evaluated arbitrary Python via ``eval``/``exec``). Templates only
ever used plain placeholders, so that is all the language supports now:
``{{name}}`` with optional surrounding whitespace.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from dirtt.exceptions import TemplateError

__all__ = ["substitute", "placeholders"]

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
_BRACE_RE = re.compile(r"\{\{|\}\}")


def _position(text: str, index: int) -> tuple[int, int]:
    """Return (line, column) of ``index`` within ``text``, 1-based."""
    leading = text[: index + 1].splitlines() or [""]
    return (len(leading), len(leading[-1]))


def _check_balance(text: str, name: str | None) -> None:
    """Raise TemplateError on unbalanced ``{{``/``}}`` pairs."""
    depth = 0
    for match in _BRACE_RE.finditer(text):
        if match.group(0) == "{{":
            if depth:
                raise TemplateError("'{{' inside expression", name=name, position=_position(text, match.start()))
            depth = 1
        else:
            if not depth:
                raise TemplateError("'}}' outside expression", name=name, position=_position(text, match.start()))
            depth = 0
    if depth:
        raise TemplateError("no '}}' to finish last expression", name=name, position=_position(text, len(text) - 1))


def substitute(text: str, mapping: Mapping[str, object] | None = None, *, strict: bool = True, name: str | None = None) -> str:
    """Replace every ``{{var}}`` in ``text`` with ``mapping["var"]``.

    With ``strict`` (the default) an unknown placeholder raises
    :class:`TemplateError`; otherwise it is left in place verbatim.
    """
    mapping = mapping or {}
    _check_balance(text, name)

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in mapping:
            value = mapping[key]
            return "" if value is None else str(value)
        if strict:
            raise TemplateError(f"undefined placeholder {key!r}", name=name, position=_position(text, match.start()))
        return match.group(0)

    return _PLACEHOLDER_RE.sub(_replace, text)


def placeholders(text: str, *, name: str | None = None) -> list[str]:
    """Return unique placeholder names in order of first appearance."""
    _check_balance(text, name)
    seen: dict[str, None] = {}
    for match in _PLACEHOLDER_RE.finditer(text):
        seen.setdefault(match.group(1))
    return list(seen)
