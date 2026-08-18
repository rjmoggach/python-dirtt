"""The ``dirtt`` command line interface.

Subcommands::

    dirtt create -t TEMPLATE [--var k=v ...] [--dest DIR] [--dry-run] [-i] [-w] [-v]
    dirtt list
    dirtt placeholders -t TEMPLATE
    dirtt introspect PATH [-o FILE]

Replaces the 0.x ``mktree.py``/``mkproject.py``/``mktemplate.py`` scripts.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import dirtt
from dirtt.builder import build
from dirtt.exceptions import DirttError
from dirtt.introspect import introspect
from dirtt.model import Action
from dirtt.parser import TEMPLATES_DIR, read_source
from dirtt.template import placeholders

logger = logging.getLogger("dirtt")


def _parse_vars(pairs: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise SystemExit(f"error: --var expects KEY=VALUE, got {pair!r}")
        result[key] = value
    return result


def _cmd_create(args: argparse.Namespace) -> int:
    context = _parse_vars(args.var)
    needed = [name for name in placeholders(read_source(args.template)) if name not in context]
    for name in needed:
        if not sys.stdin.isatty() and not args.dry_run:
            raise SystemExit(f"error: missing template variable {name!r} (pass --var {name}=...)")
        context[name] = input(f"{name}> ")

    on_confirm = None
    if args.interactive:
        def on_confirm(action: Action) -> bool:
            return input(f"Create directory {action.path} (yes/no)? ").strip().lower() in ("y", "yes")

    actions = build(
        args.template,
        context,
        dest=args.dest,
        dry_run=args.dry_run,
        warn=args.warn,
        on_confirm=on_confirm,
    )
    if args.dry_run:
        for action in actions:
            print(action.describe())
        print(f"dry run: {len(actions)} actions, nothing created")
    else:
        print(f"created tree: {len(actions)} actions")
    return 0


def _cmd_list(_args: argparse.Namespace) -> int:
    print(f"Packaged templates in {TEMPLATES_DIR}:")
    for path in sorted(TEMPLATES_DIR.iterdir()):
        print(f"  {path}")
    return 0


def _cmd_placeholders(args: argparse.Namespace) -> int:
    for name in placeholders(read_source(args.template)):
        print(name)
    return 0


def _cmd_introspect(args: argparse.Namespace) -> int:
    xml = introspect(args.path)
    if args.output:
        Path(args.output).write_text(xml, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(xml, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dirtt", description="Directory Tree Templater")
    parser.add_argument("--version", action="version", version=f"%(prog)s {dirtt.__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="create a directory tree from a template")
    p_create.add_argument("-t", "--template", required=True, help="path or URL of an XML/JSON template")
    p_create.add_argument("--var", action="append", default=[], metavar="KEY=VALUE", help="template variable (repeatable)")
    p_create.add_argument("--dest", help="parent directory (overrides the template's dirname)")
    p_create.add_argument("-n", "--dry-run", action="store_true", help="print the plan without creating anything")
    p_create.add_argument("-i", "--interactive", action="store_true", help="confirm each directory")
    p_create.add_argument("-w", "--warn", action="store_true", help="fail if a directory already exists")
    p_create.add_argument("-v", "--verbose", action="store_true")
    p_create.set_defaults(func=_cmd_create)

    p_list = sub.add_parser("list", help="list packaged example templates")
    p_list.set_defaults(func=_cmd_list)

    p_ph = sub.add_parser("placeholders", help="show the variables a template requires")
    p_ph.add_argument("-t", "--template", required=True)
    p_ph.set_defaults(func=_cmd_placeholders)

    p_intro = sub.add_parser("introspect", help="generate a template from an existing tree")
    p_intro.add_argument("path")
    p_intro.add_argument("-o", "--output", help="write the template to a file instead of stdout")
    p_intro.set_defaults(func=_cmd_introspect)

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        return args.func(args)
    except DirttError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
