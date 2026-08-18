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
dirtt list                     # show the packaged example templates
dirtt placeholders -t TEMPLATE # show the variables a template requires
dirtt introspect PATH [-o FILE]# generate a template from a real tree
```

`create` prompts interactively for any `{{placeholder}}` you don't pass
with `--var`. `--dry-run` prints each planned action (`mkdir`, `write`,
`symlink`) instead of performing it. `-i/--interactive` confirms each
directory; answering no skips that directory and everything inside it.
`-w/--warn` fails instead of continuing when a directory already exists.

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

## Development

```console
git clone https://github.com/rjmoggach/python-dirtt
cd python-dirtt
uv run --group dev pytest
```

Contributions welcome — code, tests, docs, bug reports, ideas.
