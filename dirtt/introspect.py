"""Generate a dirtt XML template from an existing directory tree.

The inverse of :mod:`dirtt.builder`: point it at a real tree and get a
template you can re-run elsewhere. Symlinks that point inside the tree
become ``idref`` links to the target directory's generated id; symlinks
that leave the tree keep their literal target as ``ref``.
"""

from __future__ import annotations

import grp
import logging
import os
import pwd
import stat
from pathlib import Path
from xml.etree import ElementTree

from dirtt.exceptions import BuildError

__all__ = ["introspect"]

logger = logging.getLogger("dirtt")


def _owner_names(path: Path) -> tuple[str | None, str | None]:
    info = path.lstat()
    try:
        username = pwd.getpwuid(info.st_uid).pw_name
    except KeyError:
        username = None
    try:
        group = grp.getgrgid(info.st_gid).gr_name
    except KeyError:
        group = None
    return username, group


def _stat_attrs(element: ElementTree.Element, path: Path) -> None:
    element.set("basename", path.name)
    element.set("name", path.name)
    element.set("perms", format(stat.S_IMODE(path.lstat().st_mode), "#05o"))
    username, group = _owner_names(path)
    if username:
        element.set("username", username)
    if group:
        element.set("group", group)


def introspect(source: str | Path, *, include_files: bool = True) -> str:
    """Return a dirtt XML template describing the tree at ``source``."""
    base = Path(source).resolve()
    if not base.is_dir():
        raise BuildError(f"{source!r} is not a directory")

    root = ElementTree.Element("dirtt")
    _stat_attrs(root, base)
    root.set("dirname", str(base.parent))
    root.set("version", "1.0")

    elements: dict[Path, ElementTree.Element] = {base: root}
    pending_links: list[tuple[Path, Path]] = []  # (link path, resolved target)
    id_count = 0

    def _element_for(path: Path) -> ElementTree.Element:
        parent = elements[path.parent]
        if path.is_symlink():
            pending_links.append((path, Path(os.path.realpath(path))))
            return parent  # links are appended in a second pass
        tag = "dir" if path.is_dir() else "file"
        element = ElementTree.SubElement(parent, tag)
        _stat_attrs(element, path)
        if path.is_dir():
            elements[path] = element
        return element

    for current, dirnames, filenames in os.walk(base):
        current_path = Path(current)
        for name in sorted(dirnames):
            _element_for(current_path / name)
        if include_files:
            for name in sorted(filenames):
                _element_for(current_path / name)
        # don't descend into symlinked dirs (os.walk skips them by default)

    for link_path, target in pending_links:
        parent = elements.get(link_path.parent)
        if parent is None:
            continue
        link = ElementTree.SubElement(parent, "link")
        link.set("basename", link_path.name)
        link.set("name", link_path.name)
        if target in elements:
            target_element = elements[target]
            if not target_element.get("id"):
                id_count += 1
                target_element.set("id", f"ref_{id_count}")
            link.set("idref", target_element.get("id", ""))
        else:
            link.set("ref", str(target))

    ElementTree.indent(root)
    body = ElementTree.tostring(root, encoding="unicode")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{body}\n'
