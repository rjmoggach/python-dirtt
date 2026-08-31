"""Plan the migration of an existing tree from one layout to another.

A migration is described by a JSON *mapping file*: explicit ``map``
entries, optional ``prefix_rules``, and metadata. :func:`load_map` reads
and validates one; :func:`plan_migration` reads the tree on disk and
returns an ordered ``list[Action]`` plus a human-readable orphan report.

Planning is pure: it only *reads* the tree, never writes. The caller
decides whether to hand the actions to :func:`dirtt.builder.execute`,
so a dry run is the default by construction.

Matching, first match wins, each source matching at most once:

1. an explicit ``map`` entry (root-relative paths),
2. a ``prefix_rules`` entry (the matching prefix is replaced),
3. the path is already part of the new layout (a target, or an
   ancestor/descendant of one) - matched, no action.

Anything else is an *orphan*: reported, kept, never deleted. The only
removal ever planned is an ``rmdir`` of an already-empty orphan
directory, and only when ``prune=True``.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

from dirtt.exceptions import BuildError, TemplateError
from dirtt.model import Action

__all__ = ["load_map", "plan_migration", "SCHEMA_VERSION", "TEMP_SUFFIX"]

logger = logging.getLogger("dirtt")

#: The only ``migration_schema`` this module understands.
SCHEMA_VERSION = 1

#: Suffix of the intermediate name used by a two-step case-only rename.
TEMP_SUFFIX = "__mig"

_STAGE_PREFIX = ".__dirtt_tmp_"

_RESERVED_KEYS = frozenset(
    {
        "migration_schema",
        "from",
        "to",
        "updated",
        "rules",
        "case_only_renames",
        "prefix_rules",
        "map",
        "orphans_expected",
        "notes",
    }
)


# -- mapping files ---------------------------------------------------------


def _norm(path: object, *, what: str) -> str:
    """Normalize a root-relative path: posix separators, no leading or
    trailing slash, no ``..``."""
    if not isinstance(path, str):
        raise TemplateError(f"{what} must be a string, got {type(path).__name__}: {path!r}")
    parts = [p for p in path.replace("\\", "/").split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise TemplateError(f"{what} {path!r} escapes the tree root")
    if not parts:
        raise TemplateError(f"{what} {path!r} is empty")
    return "/".join(parts)


def _coerce(data: Mapping[str, object], *, name: str) -> Mapping[str, object]:
    """Accept both the schema form and a legacy flat ``{old: new}`` map."""
    if "map" not in data and "migration_schema" not in data:
        if data and all(isinstance(value, str) for value in data.values()):
            logger.debug("%s has no migration_schema; reading it as a flat legacy map", name)
            return {"migration_schema": SCHEMA_VERSION, "map": dict(data)}
        raise TemplateError(f"migration map {name} has no 'migration_schema' key")
    if "migration_schema" not in data:
        raise TemplateError(f"migration map {name} has no 'migration_schema' key")
    version = data["migration_schema"]
    if version != SCHEMA_VERSION:
        raise TemplateError(f"unsupported migration_schema {version!r} in {name} (expected {SCHEMA_VERSION})")
    return data


def load_map(source: str | Path) -> Mapping[str, object]:
    """Read and validate a migration mapping file.

    ``migration_schema`` must be ``1``. Unknown top-level keys are
    metadata and are kept as-is. A legacy flat ``{"old": "new"}`` object
    with no schema key is accepted and wrapped.
    """
    path = Path(source).expanduser()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TemplateError(f"migration map {source!r} could not be read: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TemplateError(f"migration map {source!r} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise TemplateError(f"migration map {source!r} must be a JSON object, got {type(data).__name__}")
    mapping = _coerce(data, name=str(source))
    _rules(mapping, name=str(source))  # fail early on bad map/prefix_rules
    return mapping


def _rules(mapping: Mapping[str, object], *, name: str = "mapping") -> tuple[dict[str, str], dict[str, str], set[str]]:
    """Return ``(map entries, prefix rules, known targets)``, normalized."""
    if not isinstance(mapping, Mapping):
        raise TemplateError(f"migration mapping must be a mapping, got {type(mapping).__name__}")
    mapping = _coerce(mapping, name=name)

    def _pairs(key: str) -> dict[str, str]:
        raw = mapping.get(key, {})
        if not isinstance(raw, Mapping):
            raise TemplateError(f"{key!r} in {name} must be an object of old -> new paths")
        return {str(k): v for k, v in raw.items()}  # type: ignore[misc]

    entries: dict[str, str] = {}
    for key, value in _pairs("map").items():
        entries[_norm(key, what=f"map key in {name}")] = _norm(value, what=f"map value in {name}")

    prefixes: dict[str, str] = {}
    for key, value in _pairs("prefix_rules").items():
        source = _norm(key, what=f"prefix_rules key in {name}")
        prefixes[source + "/"] = _norm(value, what=f"prefix_rules value in {name}") + "/"

    targets = set(entries.values()) | {value.rstrip("/") for value in prefixes.values()}
    return entries, prefixes, targets


# -- path helpers ----------------------------------------------------------


def _is_ancestor(ancestor: str, path: str) -> bool:
    """True when ``ancestor`` is a strict parent directory of ``path``."""
    return path.startswith(ancestor + "/")


def _overlaps(one: str, other: str) -> bool:
    return one == other or _is_ancestor(one, other) or _is_ancestor(other, one)


def _rebase(path: str, old: str, new: str) -> str:
    """``path`` as it reads once ``old`` has been renamed to ``new``."""
    if path == old:
        return new
    if _is_ancestor(old, path):
        return new + path[len(old) :]
    return path


def _is_case_only(source: str, target: str) -> bool:
    """True when the rename differs only by letter case, which a
    case-insensitive volume (macOS, SMB, Dropbox) can silently collapse."""
    if source == target:
        return False
    if source.lower() == target.lower():
        return True
    src_base, dst_base = source.rsplit("/", 1)[-1], target.rsplit("/", 1)[-1]
    return src_base != dst_base and src_base.lower() == dst_base.lower()


# -- scanning --------------------------------------------------------------


def _classify(rel: str, entries: Mapping[str, str], prefixes: Mapping[str, str], targets: set[str]) -> tuple[str, str]:
    """Return ``(kind, target)`` where kind is map/prefix/identical/orphan."""
    if rel in entries:
        return "map", entries[rel]
    for key in sorted(prefixes, key=len, reverse=True):
        if rel.startswith(key):
            return "prefix", prefixes[key] + rel[len(key) :]
    if any(rel == target or _is_ancestor(target, rel) or _is_ancestor(rel, target) for target in targets):
        return "identical", rel
    return "orphan", rel


def _scan(
    root: Path, entries: Mapping[str, str], prefixes: Mapping[str, str], targets: set[str]
) -> tuple[list[tuple[str, str]], list[str]]:
    """Walk the tree and return ``(moves, orphans)`` as root-relative paths."""
    moves: list[tuple[str, str]] = []
    orphans: list[str] = []

    def _keys_under(rel: str) -> bool:
        prefix = rel + "/"
        return any(key.startswith(prefix) for key in entries) or any(key.startswith(prefix) for key in prefixes)

    def _walk(directory: Path, rel_dir: str) -> None:
        try:
            children = sorted(directory.iterdir(), key=lambda child: child.name)
        except OSError as exc:  # unreadable directory: report, never fail the plan
            logger.warning("cannot read %s: %s", directory, exc)
            return
        for child in children:
            rel = f"{rel_dir}/{child.name}" if rel_dir else child.name
            is_dir = child.is_dir() and not child.is_symlink()
            kind, target = _classify(rel, entries, prefixes, targets)
            if kind in ("map", "prefix"):
                if target != rel:
                    moves.append((rel, target))
                if is_dir and _keys_under(rel):
                    _walk(child, rel)
            elif kind == "identical":
                if is_dir and _keys_under(rel):
                    _walk(child, rel)
            elif is_dir and _keys_under(rel):
                _walk(child, rel)  # holds mapped children: a container, not an orphan
            else:
                orphans.append(rel)

    _walk(root, "")
    return moves, orphans


# -- planning --------------------------------------------------------------


def _expand(root: Path, moves: list[tuple[str, str]], merge_dests: set[str]) -> list[tuple[str, str]]:
    """Turn a move onto a shared destination into per-child moves.

    Several sources declaring one destination is a deliberate *merge*
    (2015's ``_Client_IN``/``_Vendor_IN`` both become ``media/io/in``).
    The source directory itself is left behind - emptied, never deleted.
    """
    expanded: list[tuple[str, str]] = []
    for source, dest in moves:
        if dest not in merge_dests:
            expanded.append((source, dest))
            continue
        base = root / source
        if not base.is_dir():
            logger.warning("merge source is not a directory, skipping: %s", source)
            continue
        logger.info("merging contents of %s into %s", source, dest)
        for child in sorted(base.iterdir(), key=lambda path: path.name):
            expanded.append((f"{source}/{child.name}", f"{dest}/{child.name}"))
    return expanded


def _validate(root: Path, moves: list[tuple[str, str]]) -> None:
    """Reject collisions before a single action is returned."""
    claimed: dict[str, str] = {}
    for source, dest in moves:
        if dest in claimed:
            raise BuildError(f"migration maps two sources onto {dest}: {claimed[dest]!r} and {source!r}")
        claimed[dest] = source
    sources = {source for source, _ in moves}
    # Case-insensitive too: on macOS/SMB a case-only rename's destination
    # "already exists" only because its own source is still sitting there.
    lowered = {source.lower() for source in sources}
    for source, dest in moves:
        target = root / dest
        if not (target.exists() or target.is_symlink()):
            continue
        if dest in sources or dest.lower() in lowered:
            continue  # it moves away first
        if any(_is_ancestor(other, dest) for other in sources) or any(
            _is_ancestor(other, dest.lower()) for other in lowered
        ):
            continue  # an ancestor moves away first
        raise BuildError(f"cannot move {source} to {dest}: {dest} already exists and nothing moves it away")


def _unique_temp(candidate: str, root: Path, taken: set[str]) -> str:
    name, count = candidate, 1
    while name in taken or (root / name).exists() or (root / name).is_symlink():
        name = f"{candidate}_{count}"
        count += 1
    return name


def _schedule(root: Path, moves: list[tuple[str, str]], orphans: list[str]) -> tuple[list[Action], list[str]]:
    """Order the moves so nested renames compose, and return the actions
    together with the orphans' final locations."""
    pending = [
        list(move)
        for move in sorted(moves, key=lambda move: (move[0].count("/"), move[1].count("/"), move[0]))
    ]
    current = list(orphans)
    actions: list[Action] = []
    taken = {dest for _, dest in moves}
    stage = 0

    def _emit(source: str, dest: str) -> None:
        actions.append(Action("move", root / source, target=str(root / dest)))
        for entry in pending:
            entry[0] = _rebase(entry[0], source, dest)
        for index, orphan in enumerate(current):
            current[index] = _rebase(orphan, source, dest)

    def _ready(index: int) -> bool:
        source, dest = pending[index]
        for other, other_dest in (entry for position, entry in enumerate(pending) if position != index):
            if _is_ancestor(other, source):  # an ancestor moves first, then we recompute
                return False
            if _is_ancestor(other_dest, dest):  # its destination is our parent: create it first
                return False
            if _overlaps(other, dest):  # our destination is still occupied
                return False
        return True

    guard = 2 * len(pending) + 8
    while pending:
        guard -= 1
        if guard < 0:  # pragma: no cover - defensive; staging always makes progress
            raise BuildError("migration plan could not be ordered; the mapping has a cycle")
        index = next((position for position in range(len(pending)) if _ready(position)), None)
        if index is None:
            source, dest = pending[0]
            temp = _unique_temp(f"{_STAGE_PREFIX}{stage}", root, taken)
            stage += 1
            taken.add(temp)
            logger.debug("staging %s through %s to free %s", source, temp, dest)
            _emit(source, temp)
            continue
        source, dest = pending.pop(index)
        if source == dest:
            continue  # an ancestor already put it in the right place
        if _is_case_only(source, dest):
            temp = _unique_temp(f"{source}{TEMP_SUFFIX}", root, taken)
            taken.add(temp)
            logger.debug("case-only rename %s -> %s staged through %s", source, dest, temp)
            _emit(source, temp)
            _emit(temp, dest)
        else:
            _emit(source, dest)
    return actions, current


def plan_migration(
    root: str | Path,
    mapping: Mapping[str, object],
    *,
    prune: bool = False,
) -> tuple[list[Action], list[str]]:
    """Plan the migration of the tree at ``root`` under ``mapping``.

    Returns ``(actions, orphan_report)``: an ordered action list (moves,
    plus ``rmdir`` of empty orphan directories when ``prune``) and the
    report lines for everything the mapping does not account for. The
    orphans are deliberately kept out of the actions so a caller can
    print them without executing anything.

    Nothing is written here; a source declared by the mapping but absent
    on disk is warned about and skipped.
    """
    tree_root = Path(root).expanduser().resolve()
    if not tree_root.is_dir():
        raise BuildError(f"migration root {tree_root} does not exist or is not a directory")

    entries, prefixes, targets = _rules(mapping)
    for key in sorted(entries):
        path = tree_root / key
        if not (path.exists() or path.is_symlink()):
            logger.warning("migration source does not exist, skipping: %s", key)

    moves, orphans = _scan(tree_root, entries, prefixes, targets)
    merge_dests = {dest for dest, count in Counter(entries.values()).items() if count > 1}
    moves = _expand(tree_root, moves, merge_dests)
    _validate(tree_root, moves)
    actions, final = _schedule(tree_root, moves, orphans)

    report: list[str] = []
    for original, now in zip(orphans, final):
        path = tree_root / now
        empty = path.is_dir() and not any(path.iterdir())
        if prune and empty:
            actions.append(Action("rmdir", path))
            report.append(f"orphan: {original} (empty; removed by --prune)")
        elif original == now:
            report.append(f"orphan: {original} (kept in place)")
        else:
            report.append(f"orphan: {original} (kept; travels to {now} with its parent)")
    return actions, report
