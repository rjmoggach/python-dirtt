# python-dirtt — Directory Tree Templater

**Dirtt** generates directory and file structures from simple XML or JSON
templates that describe repeatedly used filesystem layouts — project
scaffolds, VFX show structures, or any tree you build more than once.

Write the layout once as a template, then stamp it out anywhere with
variables filled in:

```console
$ dirtt create -t project.xml --var project_root=/jobs --var project_path=commercial_spot
created tree: 81 actions
```

- Zero runtime dependencies — pure Python standard library
- Python 3.10+
- Templates in XML (the classic dirtt dialect, unchanged since 0.x) or JSON
- `--dry-run` prints the full plan without touching the filesystem
- Introspection: point dirtt at an existing tree and get a template back

(c) 2011–2026 [Robert Moggach](https://github.com/rjmoggach) and contributors.
Licensed under the [MIT license](LICENSE.md).

## Install

```console
pip install python-dirtt
```

## Command line

```console
dirtt create -t TEMPLATE [--var KEY=VALUE ...] [--dest DIR] [--dry-run] [-i] [-w] [-v]
                         [--skip-existing-files] [--actor WHO] [--no-log]
dirtt list                     # show the packaged example templates
dirtt placeholders -t TEMPLATE # show the variables a template requires
dirtt introspect PATH [-o FILE]# generate a template from a real tree
dirtt migrate PATH --map MAP.json [--apply] [--prune]
```

`create` prompts interactively for any `{{placeholder}}` you don't pass
with `--var`. `--dry-run` prints each planned action (`mkdir`, `write`,
`symlink`) instead of performing it. `-i/--interactive` confirms each
directory; answering no skips that directory and everything inside it.
`-w/--warn` fails instead of continuing when a directory already exists.
`--skip-existing-files` leaves existing files and symlinks alone instead
of failing, which makes re-running a template over a tree that already
exists a clean no-op.

`placeholders` reports every variable the build needs, including those
used only inside `xi:include`d templates and `href`'d content files, and
`create` prompts for that same full set.

After a successful `create`, dirtt appends one JSON line to
`lib/dirtt/scaffold.log.jsonl` under the created root recording what was
built, with what variables, when and by whom:

```json
{"actor":"rm","date":"20260830","run":"project","template":"studio_project@2026.01","vars":{"project_code":"ABC"}}
```

The template id and run name are derived from the template's path and
can be pinned with `--template-id` and `--run`; `--actor` defaults to
`$USER`, and `--no-log` turns the log off. A log that cannot be written
warns and never fails the scaffold.

## Library

```python
from dirtt import build

# create the tree
build("project.xml", {"project_root": "/jobs", "project_path": "myproject"})

# or preview first
for action in build("project.xml", context, dry_run=True):
    print(action.describe())
```

The stages are also available separately:

```python
from dirtt import load_template, plan, execute, introspect

tree = load_template("project.xml", context)   # frozen dataclass Tree
actions = plan(tree, dest="/somewhere/else")   # ordered list[Action], absolute paths
execute(actions)                               # apply (or dry_run=True)

xml = introspect("/jobs/existing_project")     # tree -> template
```

Errors raise `dirtt.DirttError` subclasses (`TemplateError`,
`BuildError`); the library never prints or exits.

## XML templates

The dialect is unchanged from dirtt 0.x:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<dirtt name="Project Tree" version="1.0"
       dirname="{{project_root}}" basename="{{project_path}}"
       username="pipeline" group="artist" perms="02755"
       xmlns:xi="http://www.w3.org/2001/XInclude">
  <dir basename="src" perms="02755">
    <file basename="README.md" href="readme_snippet.md" perms="0644"/>
  </dir>
  <dir basename="renders" id="renders-dir"/>
  <link basename="latest" idref="renders-dir"/>
  <xi:include href="shared_structure.xml"/>
</dirtt>
```

- `dirtt` — the root directory: `dirname` (parent path) + `basename`
  (directory name). If `basename` is omitted it is split off `dirname`.
- `dir` — a directory; nests `dir`, `file`, and `link` elements.
- `file` — a file; `href` names a content template (resolved next to
  the tree template, then in the packaged templates) rendered with the
  same `{{variables}}`; without `href` the file is created empty.
- `link` — a symlink; `ref` is a literal target path, `idref` points at
  the `id` of a `dir` in the same tree. Links are created last.
- `xi:include` — splice another template's children in place;
  `href` may be relative, absolute, or an `http(s)://` URL.
- `perms` is octal text (`"02775"`); `username`/`group` are applied
  with `chown` only when running as root, and skipped otherwise.
- `substitute="false"` on a `file` copies its `href` source byte for
  byte, leaving any `{{placeholders}}` in it intact. Use it when the
  file being copied is itself a template.
- An `id` must be unique across a template and everything it includes;
  a duplicate is an error rather than a silently mis-pointed `idref`.

## JSON templates

The same schema as JSON — children are tagged with `"type"`:

```json
{
  "name": "Project Tree",
  "dirname": "{{project_root}}",
  "basename": "{{project_path}}",
  "perms": "02755",
  "children": [
    { "type": "dir", "basename": "src", "children": [
      { "type": "file", "basename": "notes.txt", "content": "for {{project_path}}" }
    ]},
    { "type": "dir", "basename": "renders", "id": "renders-dir" },
    { "type": "link", "basename": "latest", "idref": "renders-dir" },
    { "include": "shared_structure.json" }
  ]
}
```

Files may carry inline `"content"` (JSON only) or an `"href"` like XML.

## Migrating from 0.2.x

| 0.2.x | 1.0 |
| --- | --- |
| `mktree.py --template ... --interactive` | `dirtt create -t ... -i` |
| `mktemplate.py -p PATH` | `dirtt introspect PATH` |
| `mkproject.py` | `dirtt create` with your studio's template |
| `DirectoryTreeHandler(verbose, template, kwargs).run()` | `build(template, kwargs)` |
| `dirtt.util.template` (Paste engine, `eval`-based) | `{{name}}` placeholders only |
| Python 2, distutils | Python 3.10+, pyproject.toml |

Your existing XML templates work as-is. The old template engine's
`{{if}}`/`{{for}}`/`{{py:}}` constructs were never used by tree
templates and are no longer supported.

## Migrating a tree between template versions

When a layout changes, `dirtt migrate` moves an existing tree onto the
new one rather than leaving you to `mv` by hand:

```console
dirtt migrate /jobs/myproject --map migrations/2015_to_2026.json   # dry run
dirtt migrate /jobs/myproject --map migrations/2015_to_2026.json --apply
```

Or copy into a new root instead of moving in place, which leaves the
original project working and lets a bad map cost a directory rather than
a production:

```console
dirtt migrate /jobs/myproject --map MAP.json --copy --dest /volumes/new/myproject --apply
```

`--copy` also migrates across filesystems, which a move cannot do at all
(a rename between volumes fails with `EXDEV`). The same mapping file
drives both: the map describes the taxonomy translation, the flag
decides what happens to the bytes. With `--copy` the source is read-only
and orphans are left in it rather than carried into the new tree.

A mapping file pairs old paths with new ones, and may add `prefix_rules`
for whole subtrees. Matching is: explicit entry, then prefix rule, then
an identical path (unchanged paths need no mapping).

It is deliberately cautious, because it moves real data:

- **Dry run is the default.** `--apply` is required to move anything.
- **Nothing is ever deleted.** A path the mapping does not account for
  is an orphan: reported and left where it is. Only `--prune` removes
  anything, and only an orphaned directory that is already empty.
- **Case-only renames are staged** through a temporary name, because
  macOS, SMB and Dropbox are case-insensitive and a direct rename there
  can lose the directory.
- **It is idempotent.** Re-running after a successful migration plans
  nothing, because every path now matches itself.
- **`--copy` never writes to the source**, and `--prune` is rejected
  with it, since nothing in the source is emptied.

## Development

```console
git clone https://github.com/rjmoggach/python-dirtt
cd python-dirtt
uv run --group dev pytest
```

Contributions welcome — code, tests, docs, bug reports, ideas.
