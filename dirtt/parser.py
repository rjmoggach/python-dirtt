"""Parse XML or JSON directory tree templates into a :class:`~dirtt.model.Tree`.

The XML dialect is unchanged from dirtt 0.x: ``dirtt``, ``dir``,
``file`` and ``link`` elements, ``xi:include`` for composition, and
``{{placeholder}}`` variables substituted before parsing. A JSON mirror
of the same schema is also accepted (see README).
"""

from __future__ import annotations

import json
import logging
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from xml.etree import ElementTree

from dirtt.exceptions import TemplateError
from dirtt.model import Dir, File, Link, Node, Tree
from dirtt.template import placeholders, substitute

__all__ = ["load_template", "read_source", "template_placeholders", "TEMPLATES_DIR"]

logger = logging.getLogger("dirtt")

TEMPLATES_DIR = Path(__file__).resolve().parent / "data" / "templates"

_XI_INCLUDE_TAGS = ("{http://www.w3.org/2001/XInclude}include", "xi:include", "include")


def read_source(source: str | Path) -> str:
    """Read template text from a filesystem path or an http(s)/file URL."""
    ref = str(source)
    if ref.startswith(("http://", "https://", "file://")):
        with urllib.request.urlopen(ref) as response:  # noqa: S310 - user-supplied template location
            return response.read().decode("utf-8")
    path = Path(ref)
    if not path.is_file():
        raise TemplateError(f"template {ref!r} does not exist or is not a file")
    return path.read_text(encoding="utf-8")


def _source_dir(source: str | Path) -> Path | None:
    ref = str(source)
    if ref.startswith(("http://", "https://")):
        return None
    if ref.startswith("file://"):
        ref = ref[len("file://") :]
    return Path(ref).resolve().parent


def _parse_perms(value: str | None, name: str) -> int | None:
    if value is None:
        return None
    try:
        return int(value, 8)
    except ValueError:
        raise TemplateError(f"invalid perms {value!r} (expected octal like '02755')", name=name) from None


def _parse_substitute(value: object | None, name: str, basename: str) -> bool:
    """Read the ``substitute`` opt-out on a file entry; absent means True."""
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "false"):
        return text == "true"
    raise TemplateError(f"invalid substitute {value!r} on file {basename!r} (expected 'true' or 'false')", name=name)


def _resolve_include(href: str, base_dir: Path | None) -> str:
    if href.startswith(("http://", "https://", "file://")):
        return href
    if Path(href).is_absolute() or base_dir is None:
        return href
    return str(base_dir / href)


def _resolve_content(href: str, base_dir: Path | None) -> str | None:
    """Locate a file content template the way the builder does, or None."""
    if href.startswith(("http://", "https://", "file://")) or Path(href).is_absolute():
        return href
    for base in (*([base_dir] if base_dir else []), TEMPLATES_DIR):
        candidate = base / href
        if candidate.is_file():
            return str(candidate)
    return None


class _Parser:
    def __init__(
        self,
        context: Mapping[str, object],
        strict: bool,
        seen: tuple[str, ...],
        ids: dict[str, str],
        *,
        is_root_template: bool,
    ):
        self.context = dict(context)
        self.strict = strict
        self.seen = seen
        # id value -> name of the template that declared it, shared across includes.
        self.ids = ids
        self.is_root_template = is_root_template

    def _register_id(self, value: str | None, source: str | Path) -> None:
        """Claim an author-written id, rejecting one another template already claimed."""
        if not value:
            return
        name = str(source)
        previous = self.ids.get(value)
        if previous is not None:
            raise TemplateError(f"duplicate id {value!r} (already defined in {previous})", name=name)
        self.ids[value] = name

    # -- XML ---------------------------------------------------------------

    def parse_xml(self, text: str, source: str | Path) -> Tree:
        name = str(source)
        try:
            root = ElementTree.fromstring(text)
        except ElementTree.ParseError as exc:
            raise TemplateError(f"invalid XML: {exc}", name=name) from exc
        if root.tag != "dirtt":
            raise TemplateError(f"root element must be <dirtt>, got <{root.tag}>", name=name)

        dirname = root.get("dirname")
        basename = root.get("basename")
        if not dirname and not basename:
            raise TemplateError("<dirtt> requires a 'dirname' and/or 'basename' attribute", name=name)
        if not basename:
            dirname, _, basename = str(dirname).rstrip("/").rpartition("/")
            dirname = dirname or "/"

        # An included root is discarded (only its children are grafted), so
        # only the outermost template's own id can collide with anything.
        if self.is_root_template:
            self._register_id(root.get("id"), source)
        root_children = tuple(self._xml_children(root, source))
        root_dir = Dir(
            basename=str(basename),
            children=root_children,
            perms=_parse_perms(root.get("perms"), name),
            username=root.get("username"),
            group=root.get("group"),
            id=root.get("id", "root-dir"),
        )
        return Tree(
            root=root_dir,
            dirname=str(dirname or "."),
            name=root.get("name"),
            version=root.get("version"),
            context=dict(self.context),
            template_dir=_source_dir(source),
        )

    def _xml_children(self, element: ElementTree.Element, source: str | Path) -> list[Node]:
        name = str(source)
        children: list[Node] = []
        for child in element:
            if child.tag == "dir":
                basename = child.get("basename")
                if not basename:
                    logger.warning("skipping <dir> with no basename in %s", name)
                    continue
                self._register_id(child.get("id"), source)
                children.append(
                    Dir(
                        basename=basename,
                        children=tuple(self._xml_children(child, source)),
                        perms=_parse_perms(child.get("perms"), name),
                        username=child.get("username"),
                        group=child.get("group"),
                        id=child.get("id"),
                    )
                )
            elif child.tag == "file":
                basename = child.get("basename")
                if not basename:
                    logger.warning("skipping <file> with no basename in %s", name)
                    continue
                self._register_id(child.get("id"), source)
                children.append(
                    File(
                        basename=basename,
                        href=child.get("href"),
                        perms=_parse_perms(child.get("perms"), name),
                        username=child.get("username"),
                        group=child.get("group"),
                        substitute=_parse_substitute(child.get("substitute"), name, basename),
                    )
                )
            elif child.tag == "link":
                basename = child.get("basename")
                ref, idref = child.get("ref"), child.get("idref")
                if not basename or not (ref or idref):
                    logger.warning("skipping <link> missing basename or ref/idref in %s", name)
                    continue
                self._register_id(child.get("id"), source)
                children.append(Link(basename=basename, ref=ref, idref=idref, dirname=child.get("dirname")))
            elif child.tag in _XI_INCLUDE_TAGS:
                href = child.get("href")
                if not href:
                    logger.warning("skipping include with no href in %s", name)
                    continue
                include_ref = _resolve_include(href, _source_dir(source))
                included = _load(include_ref, self.context, strict=self.strict, seen=self.seen, ids=self.ids)
                # Graft the included template's root *children* into place;
                # the included root dir itself maps onto the current element.
                children.extend(included.root.children)
            else:
                logger.warning("ignoring unknown element <%s> in %s", child.tag, name)
        return children

    # -- JSON --------------------------------------------------------------

    def parse_json(self, text: str, source: str | Path) -> Tree:
        name = str(source)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise TemplateError(f"invalid JSON: {exc}", name=name) from exc
        if not isinstance(data, dict):
            raise TemplateError("top-level JSON value must be an object", name=name)

        dirname = data.get("dirname")
        basename = data.get("basename")
        if not dirname and not basename:
            raise TemplateError("template requires a 'dirname' and/or 'basename' key", name=name)
        if not basename:
            dirname, _, basename = str(dirname).rstrip("/").rpartition("/")
            dirname = dirname or "/"

        if self.is_root_template:
            self._register_id(data.get("id"), source)
        root_children = tuple(self._json_children(data.get("children", []), source))
        root_dir = Dir(
            basename=str(basename),
            children=root_children,
            perms=_parse_perms(data.get("perms"), name),
            username=data.get("username"),
            group=data.get("group"),
            id=data.get("id", "root-dir"),
        )
        return Tree(
            root=root_dir,
            dirname=str(dirname or "."),
            name=data.get("name"),
            version=data.get("version"),
            context=dict(self.context),
            template_dir=_source_dir(source),
        )

    def _json_children(self, items: object, source: str | Path) -> list[Node]:
        name = str(source)
        if not isinstance(items, list):
            raise TemplateError("'children' must be a list", name=name)
        children: list[Node] = []
        for item in items:
            if not isinstance(item, dict):
                raise TemplateError(f"child entries must be objects, got {type(item).__name__}", name=name)
            kind = item.get("type", "dir")
            if "include" in item:
                include_ref = _resolve_include(str(item["include"]), _source_dir(source))
                included = _load(include_ref, self.context, strict=self.strict, seen=self.seen, ids=self.ids)
                children.extend(included.root.children)
                continue
            basename = item.get("basename")
            if not basename:
                logger.warning("skipping %r entry with no basename in %s", kind, name)
                continue
            if kind in ("dir", "file", "link"):
                self._register_id(item.get("id"), source)
            if kind == "dir":
                children.append(
                    Dir(
                        basename=basename,
                        children=tuple(self._json_children(item.get("children", []), source)),
                        perms=_parse_perms(item.get("perms"), name),
                        username=item.get("username"),
                        group=item.get("group"),
                        id=item.get("id"),
                    )
                )
            elif kind == "file":
                children.append(
                    File(
                        basename=basename,
                        href=item.get("href"),
                        content=item.get("content"),
                        perms=_parse_perms(item.get("perms"), name),
                        username=item.get("username"),
                        group=item.get("group"),
                        substitute=_parse_substitute(item.get("substitute"), name, str(basename)),
                    )
                )
            elif kind == "link":
                children.append(
                    Link(basename=basename, ref=item.get("ref"), idref=item.get("idref"), dirname=item.get("dirname"))
                )
            else:
                logger.warning("ignoring unknown entry type %r in %s", kind, name)
        return children


def _load(
    source: str | Path,
    context: Mapping[str, object],
    *,
    strict: bool,
    seen: tuple[str, ...],
    ids: dict[str, str] | None = None,
) -> Tree:
    ref = str(source)
    if ref in seen:
        chain = " -> ".join((*seen, ref))
        raise TemplateError(f"template include cycle: {chain}")
    text = read_source(source)
    text = substitute(text, context, strict=strict, name=ref)
    parser = _Parser(context, strict, (*seen, ref), {} if ids is None else ids, is_root_template=not seen)
    stripped = text.lstrip()
    if stripped.startswith("{") or ref.endswith(".json"):
        return parser.parse_json(text, source)
    return parser.parse_xml(text, source)


def load_template(source: str | Path, context: Mapping[str, object] | None = None, *, strict: bool = True) -> Tree:
    """Load, substitute and parse a template from a path or URL.

    ``context`` supplies values for ``{{placeholders}}``. With ``strict``
    (the default) missing placeholder values raise :class:`TemplateError`.
    """
    return _load(source, context or {}, strict=strict, seen=())


def template_placeholders(source: str | Path) -> list[str]:
    """Return every placeholder name needed to build a template.

    The union, in order of first appearance, of the template's own text,
    every ``include`` it pulls in (recursively) and every ``href`` file
    content template it renders. Files marked ``substitute="false"``
    contribute nothing, and a target that cannot be located or read is
    logged and skipped: inspection must never fail where a build would not.
    """
    found: dict[str, None] = {}
    _collect_placeholders(source, found, set(), required=True)
    return list(found)


def _collect_placeholders(
    source: str | Path, found: dict[str, None], visited: set[str], *, required: bool = False
) -> None:
    """Add one template's placeholders to ``found``, then follow its targets."""
    ref = str(source)
    if ref in visited:
        return
    visited.add(ref)
    try:
        text = read_source(source)
        for placeholder in placeholders(text, name=ref):
            found.setdefault(placeholder)
        # Substitute leniently: the values are exactly what we are discovering,
        # so unknown {{vars}} stay in place and the tree still parses.
        targets = _declared_targets(substitute(text, {}, strict=False, name=ref), ref)
    except TemplateError as exc:
        if required:
            raise
        logger.warning("skipping template %s: %s", ref, exc)
        return

    base_dir = _source_dir(source)
    for kind, href in targets:
        if "{{" in href:
            logger.warning("cannot follow %s %r in %s: unresolved placeholder in the path", kind, href, ref)
            continue
        if kind == "include":
            _collect_placeholders(_resolve_include(href, base_dir), found, visited)
            continue
        target = _resolve_content(href, base_dir)
        if target is None:
            logger.warning("file template %r declared in %s not found", href, ref)
            continue
        _collect_content_placeholders(target, found, visited)


def _collect_content_placeholders(source: str | Path, found: dict[str, None], visited: set[str]) -> None:
    """Add a file content template's placeholders to ``found``."""
    ref = str(source)
    if ref in visited:
        return
    visited.add(ref)
    try:
        for placeholder in placeholders(read_source(source), name=ref):
            found.setdefault(placeholder)
    except TemplateError as exc:
        logger.warning("skipping file template %s: %s", ref, exc)


def _declared_targets(text: str, name: str) -> list[tuple[str, str]]:
    """Return ``('include' | 'file', href)`` pairs a template declares, in document order."""
    targets: list[tuple[str, str]] = []
    stripped = text.lstrip()
    if stripped.startswith("{") or name.endswith(".json"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise TemplateError(f"invalid JSON: {exc}", name=name) from exc
        _json_targets(data, targets, name)
        return targets
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        raise TemplateError(f"invalid XML: {exc}", name=name) from exc
    for element in root.iter():
        href = element.get("href")
        if not href:
            continue
        if element.tag in _XI_INCLUDE_TAGS:
            targets.append(("include", href))
        elif element.tag == "file":
            basename = element.get("basename", "?")
            if _parse_substitute(element.get("substitute"), name, basename):
                targets.append(("file", href))
    return targets


def _json_targets(data: object, targets: list[tuple[str, str]], name: str) -> None:
    if isinstance(data, list):
        for item in data:
            _json_targets(item, targets, name)
        return
    if not isinstance(data, dict):
        return
    include = data.get("include")
    if include:
        targets.append(("include", str(include)))
    href = data.get("href")
    if href and data.get("type") == "file":
        basename = str(data.get("basename", "?"))
        if _parse_substitute(data.get("substitute"), name, basename):
            targets.append(("file", str(href)))
    _json_targets(data.get("children", []), targets, name)
