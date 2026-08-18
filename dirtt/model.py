"""Immutable data model for directory tree templates.

A template parses into a :class:`Tree` whose root is a :class:`Dir`.
Nothing in this module touches the filesystem; the model is a pure
description that :mod:`dirtt.builder` turns into an ordered plan of
:class:`Action` records.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Literal, Union

__all__ = ["Dir", "File", "Link", "Node", "Tree", "Action"]


@dataclass(frozen=True, slots=True)
class File:
    """A file to create, optionally rendered from a content template (``href``)."""

    basename: str
    href: str | None = None
    content: str | None = None
    perms: int | None = None
    username: str | None = None
    group: str | None = None


@dataclass(frozen=True, slots=True)
class Link:
    """A symlink named ``basename`` pointing at ``ref`` (literal path) or ``idref`` (a Dir id)."""

    basename: str
    ref: str | None = None
    idref: str | None = None
    dirname: str | None = None


@dataclass(frozen=True, slots=True)
class Dir:
    """A directory and its children."""

    basename: str
    children: tuple["Node", ...] = ()
    perms: int | None = None
    username: str | None = None
    group: str | None = None
    id: str | None = None


Node = Union[Dir, File, Link]


@dataclass(frozen=True, slots=True)
class Tree:
    """A parsed template: the root directory plus template-level metadata."""

    root: Dir
    dirname: str
    name: str | None = None
    version: str | None = None
    context: Mapping[str, object] = field(default_factory=dict)
    template_dir: Path | None = None

    def walk(self) -> Iterator[tuple[PurePosixPath, Node]]:
        """Yield ``(relative_path, node)`` pairs depth-first, root included."""

        def _walk(node: Node, prefix: PurePosixPath) -> Iterator[tuple[PurePosixPath, Node]]:
            path = prefix / node.basename
            yield path, node
            if isinstance(node, Dir):
                for child in node.children:
                    yield from _walk(child, path)

        yield from _walk(self.root, PurePosixPath())


@dataclass(frozen=True, slots=True)
class Action:
    """One planned filesystem operation."""

    op: Literal["mkdir", "write", "symlink"]
    path: Path
    target: str | None = None  # symlink: what the link points at
    content: str | None = None  # write: file body
    mode: int | None = None
    username: str | None = None
    group: str | None = None

    def describe(self) -> str:
        mode = f" mode={self.mode:04o}" if self.mode is not None else ""
        owner = f" owner={self.username}:{self.group}" if self.username or self.group else ""
        if self.op == "symlink":
            return f"symlink {self.path} -> {self.target}"
        size = f" ({len(self.content or '')} bytes)" if self.op == "write" else ""
        return f"{self.op} {self.path}{mode}{owner}{size}"
