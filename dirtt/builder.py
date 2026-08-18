"""Turn a parsed :class:`~dirtt.model.Tree` into filesystem changes.

Two stages, both side-effect free until the last moment:

* :func:`plan` walks the tree and returns an ordered ``list[Action]``
  with absolute paths — no ``os.chdir``, ever.
* :func:`execute` applies those actions (or just returns them for a
  dry run).

:func:`build` is the one-shot convenience combining parse + plan +
execute, and is the main public entry point of the library.
"""

from __future__ import annotations

import grp
import logging
import os
import pwd
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from dirtt.exceptions import BuildError
from dirtt.model import Action, Dir, File, Link, Tree
from dirtt.parser import TEMPLATES_DIR, load_template, read_source
from dirtt.template import substitute

__all__ = ["plan", "execute", "build"]

logger = logging.getLogger("dirtt")


def _resolve_href(href: str, template_dir: Path | None, template_dirs: Sequence[Path]) -> str:
    """Locate a file content template next to the tree template, in any
    caller-supplied directory, or in the packaged templates."""
    if href.startswith(("http://", "https://", "file://")) or Path(href).is_absolute():
        return href
    search: list[Path] = [*([template_dir] if template_dir else []), *template_dirs, TEMPLATES_DIR]
    for base in search:
        candidate = base / href
        if candidate.is_file():
            return str(candidate)
    raise BuildError(f"file template {href!r} not found in {[str(p) for p in search]}")


def plan(tree: Tree, *, dest: str | Path | None = None, template_dirs: Sequence[Path] = ()) -> list[Action]:
    """Return the ordered actions needed to realize ``tree``.

    ``dest`` overrides the template's own ``dirname`` as the parent
    directory of the root. Links are planned last (after every directory
    exists), matching dirtt 0.x behavior.
    """
    parent = Path(dest) if dest is not None else Path(tree.dirname)
    parent = parent.expanduser()
    root_path = (parent / tree.root.basename).resolve()

    actions: list[Action] = []
    links: list[Action] = []
    id_map: dict[str, Path] = {}

    def _walk(node: Dir | File | Link, directory: Path) -> None:
        if isinstance(node, Dir):
            path = directory / node.basename
            if node.id:
                id_map[node.id] = path
            actions.append(Action("mkdir", path, mode=node.perms, username=node.username, group=node.group))
            for child in node.children:
                _walk(child, path)
        elif isinstance(node, File):
            path = directory / node.basename
            content = node.content or ""
            if node.href:
                source = _resolve_href(node.href, tree.template_dir, template_dirs)
                content = substitute(read_source(source), tree.context, name=source)
            actions.append(Action("write", path, content=content, mode=node.perms, username=node.username, group=node.group))
        else:  # Link
            link_dir = Path(node.dirname) if node.dirname else directory
            links.append(Action("symlink", link_dir / node.basename, target=node.idref or node.ref))

    if tree.root.id:
        id_map[tree.root.id] = root_path
    actions.append(Action("mkdir", root_path, mode=tree.root.perms, username=tree.root.username, group=tree.root.group))
    for child in tree.root.children:
        _walk(child, root_path)

    resolved_links: list[Action] = []
    for link in links:
        target = link.target
        if target in id_map:
            target = str(id_map[target])
        resolved_links.append(Action("symlink", link.path, target=target))
    return actions + resolved_links


def _apply_ownership(path: Path, action: Action) -> None:
    """chmod always (when requested); chown only when running as root."""
    if action.mode is not None:
        os.chmod(path, action.mode)
    if not (action.username or action.group):
        return
    if os.geteuid() != 0:
        logger.debug("not root; skipping chown %s:%s on %s", action.username, action.group, path)
        return
    uid = gid = -1
    try:
        if action.username:
            uid = pwd.getpwnam(action.username).pw_uid
        if action.group:
            gid = grp.getgrnam(action.group).gr_gid
    except KeyError as exc:
        logger.warning("unknown owner for %s: %s", path, exc)
        return
    os.chown(path, uid, gid)


def execute(
    actions: Sequence[Action],
    *,
    dry_run: bool = False,
    warn: bool = False,
    on_confirm: Callable[[Action], bool] | None = None,
) -> list[Action]:
    """Apply ``actions`` in order and return the ones performed.

    ``dry_run`` performs nothing and returns everything. ``warn`` turns
    an already-existing directory into a :class:`BuildError` instead of a
    silent skip. ``on_confirm`` (used for interactive mode) is called per
    mkdir; returning False skips that directory and everything inside it.
    """
    if dry_run:
        return list(actions)

    performed: list[Action] = []
    skipped_roots: list[Path] = []

    def _under_skipped(path: Path) -> bool:
        return any(root == path or root in path.parents for root in skipped_roots)

    for action in actions:
        if _under_skipped(action.path):
            logger.debug("skipping %s (inside skipped directory)", action.path)
            continue
        if action.op == "mkdir":
            if on_confirm is not None and not on_confirm(action):
                skipped_roots.append(action.path)
                logger.debug("skipped by request: %s", action.path)
                continue
            if action.path.is_dir():
                if warn:
                    raise BuildError(f"directory already exists: {action.path}")
                logger.debug("directory exists, continuing: %s", action.path)
            elif action.path.exists():
                raise BuildError(f"a non-directory exists at {action.path}")
            else:
                action.path.mkdir(parents=True)
            _apply_ownership(action.path, action)
        elif action.op == "write":
            if action.path.exists():
                raise BuildError(f"refusing to overwrite existing path: {action.path}")
            action.path.write_text(action.content or "", encoding="utf-8")
            _apply_ownership(action.path, action)
        elif action.op == "symlink":
            if action.path.exists() or action.path.is_symlink():
                raise BuildError(f"refusing to overwrite existing path: {action.path}")
            if action.target is None:
                raise BuildError(f"symlink {action.path} has no target")
            action.path.symlink_to(action.target)
        logger.debug("%s", action.describe())
        performed.append(action)
    return performed


def build(
    source: str | Path,
    context: Mapping[str, object] | None = None,
    *,
    dest: str | Path | None = None,
    dry_run: bool = False,
    warn: bool = False,
    on_confirm: Callable[[Action], bool] | None = None,
    template_dirs: Sequence[Path] = (),
) -> list[Action]:
    """Parse a template, plan it, and execute the plan. Returns the actions."""
    tree = load_template(source, context)
    actions = plan(tree, dest=dest, template_dirs=template_dirs)
    return execute(actions, dry_run=dry_run, warn=warn, on_confirm=on_confirm)
