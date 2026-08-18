# python-dirtt 2026 Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite python-dirtt for Python 3.10+ as v1.0.0, keeping the simple XML directory-tree-template concept, replacing the SAX/os.chdir engine with an immutable dataclass tree + pathlib builder, adding JSON templates and dry-run, with modern packaging and tests.

**Architecture:** Three clean stages replace the old side-effecting SAX handler: (1) **parse** — XML (ElementTree) or JSON → frozen dataclass tree (`Dir`/`File`/`Link`), with `{{var}}` substitution and `xi:include` handled at parse time; (2) **plan** — walk the tree into an ordered list of `Action` records (mkdir/write/chmod/chown/symlink) with absolute `pathlib.Path`s, no `os.chdir` ever; (3) **execute** — apply actions, or print them for `--dry-run`. One `dirtt` CLI (argparse subcommands) replaces the three old scripts.

**Tech Stack:** Pure stdlib (zero runtime deps): `dataclasses`, `pathlib`, `xml.etree.ElementTree`, `json`, `argparse`, `logging`, `urllib.request`. Dev: `pytest`. Packaging: `pyproject.toml` (setuptools backend, PEP 621), built with `uv build`.

**Spec:** This plan is its own spec (derived from review of the v0.2.0 codebase; user brief: "maintain its simple solution, extend to better data structures, optimize throughout, release").

## Global Constraints

- Python floor: `requires-python = ">=3.10"`.
- Zero runtime dependencies. `pytest` is the only dev dependency.
- XML template format stays backward compatible: elements `dirtt|dir|file|link`, attributes `basename,dirname,name,perms,username,group,href,id,idref,ref`, `xi:include`, `{{placeholder}}` variables.
- Library code never calls `sys.exit()` or `print` — it raises exceptions (`DirttError` hierarchy) and logs via `logging.getLogger("dirtt")`.
- `chown` is only attempted when running as root (`os.geteuid() == 0`); otherwise skipped with a debug log (matches old accidental behavior where root/root defaults skipped chown).
- The Paste template engine (`eval`/`exec` based), `looper.py`, hardcoded `ENABLED_USERS` uid gates, and `distutils` are removed entirely.
- Version 1.0.0; package name on PyPI stays `python-dirtt`; import name stays `dirtt`.
- Old package-data templates (`dirtt/data/`) ship as package data via `[tool.setuptools.package-data]`.

## File Structure

- Create: `pyproject.toml` (replaces `setup.py`, `setup.cfg`, `MANIFEST`, `MANIFEST.in`)
- Rewrite: `dirtt/__init__.py` — version + public API re-exports only
- Create: `dirtt/model.py` — frozen dataclasses `Dir`, `File`, `Link`, `Tree`; `Action` dataclass
- Create: `dirtt/template.py` — `substitute(text, mapping)`, `placeholders(text)` for `{{var}}` syntax
- Create: `dirtt/parser.py` — `load_template(source, context)` → `Tree`; XML + JSON; `xi:include`; http/file URL reads
- Create: `dirtt/builder.py` — `plan(tree)` → `list[Action]`; `execute(actions, ...)`; `build(...)` convenience
- Create: `dirtt/introspect.py` — `introspect(path)` → XML template string (rewrite of `TreeIntrospector`)
- Create: `dirtt/cli.py` — `dirtt create|list|placeholders|introspect`
- Create: `dirtt/exceptions.py` — `DirttError`, `TemplateError`, `BuildError`
- Delete: `dirtt/util/` (all), `dirtt/scripts/` (all), `setup.py`, `setup.cfg`, `MANIFEST`, `MANIFEST.in`, `tests/test0.py`, `tests/run_all.py`
- Rewrite: `tests/` as pytest: `tests/test_template.py`, `tests/test_parser.py`, `tests/test_builder.py`, `tests/test_introspect.py`, `tests/test_cli.py`
- Update: `README.md`, `NEWS.md`
- Keep: `dirtt/data/dirtt.dtd`, `dirtt/data/templates/*`, `tests/templates/*` (fixtures, minor path fixes if needed)

---

### Task 1: Packaging skeleton + version

**Files:** Create `pyproject.toml`, rewrite `dirtt/__init__.py`, create `dirtt/exceptions.py`; delete `setup.py`, `setup.cfg`, `MANIFEST`, `MANIFEST.in`.

**Interfaces produced:** `dirtt.__version__ == "1.0.0"`; exceptions `DirttError(Exception)`, `TemplateError(DirttError)`, `BuildError(DirttError)`.

- [ ] `pyproject.toml`: PEP 621 metadata (name `python-dirtt`, dynamic version from `dirtt.__version__`, MIT, `requires-python >=3.10`, classifiers 3.10–3.14, urls, `[project.scripts] dirtt = "dirtt.cli:main"`, package-data for `dirtt/data`), `[dependency-groups] dev = ["pytest"]`.
- [ ] `dirtt/__init__.py` reduced to version + re-exports (filled as modules land).
- [ ] Delete legacy packaging files. Commit.

### Task 2: Template substitution (`dirtt/template.py`)

**Interfaces produced:**
- `substitute(text: str, mapping: Mapping[str, object], *, strict: bool = True) -> str` — replaces `{{name}}` (whitespace tolerant: `{{ name }}`); unknown name raises `TemplateError` when strict else leaves literal.
- `placeholders(text: str) -> list[str]` — unique names in order of first appearance.

- [ ] Write `tests/test_template.py` (substitution, whitespace, missing-var strict/lenient, placeholder listing/order/dedupe, `{{`/`}}` imbalance raises `TemplateError` with line/col). Implement with a single compiled regex `\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}`. Run, pass, commit.

### Task 3: Model (`dirtt/model.py`)

**Interfaces produced:**

```python
@dataclass(frozen=True, slots=True)
class File:  basename: str; href: str | None = None; content: str | None = None; perms: int | None = None; username: str | None = None; group: str | None = None
@dataclass(frozen=True, slots=True)
class Link:  basename: str; ref: str | None = None; idref: str | None = None; dirname: str | None = None
@dataclass(frozen=True, slots=True)
class Dir:   basename: str; children: tuple[Node, ...] = (); perms: int | None = None; username: str | None = None; group: str | None = None; id: str | None = None
Node = Dir | File | Link
@dataclass(frozen=True, slots=True)
class Tree:  root: Dir; dirname: Path; name: str | None = None; version: str | None = None
@dataclass(frozen=True, slots=True)
class Action: op: Literal["mkdir","write","symlink","chmod","chown"]; path: Path; ...  # target/content/mode/uid_gid fields
```

- [ ] Tests: construction, frozen-ness, `Tree.walk()` yielding `(Path, Node)` pairs depth-first. Implement. Commit.

### Task 4: Parser (`dirtt/parser.py`)

**Interfaces produced:**
- `load_template(source: str | Path, context: Mapping[str, object] | None = None, *, strict: bool = True) -> Tree` — accepts filesystem path, `file://` or `http(s)://` URL; substitutes `{{vars}}`; parses XML (or JSON if content/suffix indicates); resolves `xi:include` recursively relative to the including template (cycle detection raises `TemplateError`); perms parsed as octal string → int.
- `read_source(source) -> str` (path or URL).
- JSON schema: top-level object `{"name","dirname","basename","perms","username","group","children":[...]}`, children objects tagged with `"type": "dir"|"file"|"link"` and same field names as XML attributes; `"include"` key maps to xi:include.

- [ ] Tests against `tests/templates/*.xml` fixtures + new JSON fixture: root attrs, nesting, perms octal, xi:include inline expansion, include cycle raises, unknown element ignored-with-warning, missing context var raises `TemplateError`. Implement (namespace-tolerant tag matching for `{http://www.w3.org/2001/XInclude}include`). Commit.

### Task 5: Builder (`dirtt/builder.py`)

**Interfaces produced:**
- `plan(tree: Tree, *, dest: Path | None = None, template_dirs: Sequence[Path] = ()) -> list[Action]` — absolute paths; `dirname/basename` root resolution matching old semantics (basename inferred from dirname when absent); file `href` content resolved from `template_dirs` then packaged `dirtt/data/templates`, substituted with tree context captured at parse time (context stored on `Tree`); link `idref` resolved via collected `Dir.id` map, `ref` used verbatim; links ordered last (old behavior).
- `execute(actions, *, dry_run=False, force=False, on_confirm: Callable[[Action], bool] | None = None, warn=False) -> list[Action]` — returns performed actions; existing dir → skip (or `BuildError` when `warn`); existing file/link → `BuildError` (no `sys.exit`); chown only as root.
- `build(source, context=None, *, dest=None, dry_run=False, ...) -> list[Action]` — parse + plan + execute one-shot; the new public front door.

- [ ] Tests in `tmp_path`: full tree build from fixture (dirs/files/links exist, modes applied), dry-run touches nothing and returns full action list, existing-file collision raises, interactive callback skipping a dir skips its subtree, idref symlink points at registered dir. Implement. Commit.

### Task 6: Introspection (`dirtt/introspect.py`)

**Interfaces produced:** `introspect(path: str | Path, *, relative_perms: bool = True) -> str` — walks a real tree, emits pretty-printed XML template (dir/file/link with basename/perms/username/group; symlinks inside the tree become `idref` links, outside become `ref`).

- [ ] Tests: build a small tree in `tmp_path` (incl. a symlink), introspect, re-parse output with `load_template`, assert round-trip structure. Implement with `ElementTree` + `indent()`. Commit.

### Task 7: CLI (`dirtt/cli.py`)

**Interfaces produced:** `main(argv=None) -> int`; subcommands:
- `dirtt create -t TEMPLATE [--var k=v ...] [--dest DIR] [--dry-run] [--interactive] [--warn] [-v]` — prompts for any unfilled placeholders (input()) unless `--dry-run` with all vars given.
- `dirtt list` — packaged template paths.
- `dirtt placeholders -t TEMPLATE` — prints required vars.
- `dirtt introspect PATH [-o FILE]`.

- [ ] Tests drive `main([...])` directly with capsys/tmp_path (create with vars, dry-run output lines, list, placeholders, introspect to file). Implement; wire `[project.scripts]`. Commit.

### Task 8: Public API, data templates, docs

- [ ] `dirtt/__init__.py`: re-export `build`, `plan`, `execute`, `load_template`, `introspect`, `substitute`, `placeholders`, model classes, exceptions; `__version__`.
- [ ] Delete `dirtt/util/`, `dirtt/scripts/`, `tests/test0.py`, `tests/run_all.py`, old test modules.
- [ ] Fix packaged example templates if parser flags issues (e.g. duplicated `basename="sequences"` in `project.xml` incoming dir → `basename="incoming"`).
- [ ] Rewrite `README.md` (concept, install `pip install python-dirtt`, CLI + library examples, XML and JSON template reference, migration notes from 0.2.x). Update `NEWS.md` with 1.0.0 entry. Commit.

### Task 9: Verification + release

- [ ] Full `pytest` run green; `uv build` produces sdist+wheel; `uv run --with dist/*.whl --no-project -- dirtt --help` sanity check from the wheel.
- [ ] Commit, tag `v1.0.0`, push branch + tag, `gh release create v1.0.0` with notes and dist artifacts.
- [ ] PyPI upload requires the maintainer's token — name the exact command (`uv publish`) as the single remaining manual step.

## Self-Review

- Spec coverage: simple solution kept (same template format, one small CLI); better data structures (frozen dataclass tree, Action plan); optimizations (no chdir, single-pass parse, regex substitution replacing eval-based engine, links resolved from id map); release included. ✓
- All legacy modules have a disposition (rewritten or deleted). ✓
- Type/signature names consistent across tasks (`load_template`, `plan`, `execute`, `build`, `Action`, `Tree`). ✓
