# Changes And News

## 1.2.0 (2026-08-31)

Additive and backward compatible: `dirtt migrate` without the new flag
behaves exactly as it did in 1.1.0.

* **`dirtt migrate --copy --dest TARGET`** performs the same taxonomy
  translation as a move, but as a copy into a separate root. The
  mapping file is unchanged: the map describes the translation, the
  flag decides what happens to the bytes.

  Two things needed it. A move puts a live project at risk, because the
  source is gone the moment the map turns out to be wrong; a copy makes
  a bad map cost a directory instead of a production. And a move cannot
  cross a filesystem at all — a rename between volumes raises `EXDEV` —
  which is exactly the real case, an internal drive to an external one.

  With `--copy` the source is read-only, an existing destination is
  still refused, and orphans are left in the source rather than carried
  into the new tree, so the new taxonomy does not inherit the old one's
  stray paths. The orphan report names everything left behind. `--dest`
  is required with `--copy` and rejected without it; `--prune` is
  rejected with it, since nothing in the source is ever emptied.

  A directory copy uses `rsync -a` when it is on PATH because it is
  markedly faster on large media trees, and falls back to
  `shutil.copytree` otherwise. Both paths preserve symlinks and
  metadata and are asserted to produce identical trees; rsync is an
  optimisation, never a behaviour change.
* Library: `plan_copy_migration(source, dest, mapping)` alongside
  `plan_migration`, and a `copy` action in `execute()`.


## 1.1.0 (2026-08-30)

Additive and backward compatible: every existing template and script
keeps working unchanged.

* **`dirtt migrate`** moves an existing tree from one template's layout
  onto another's, driven by a mapping file. Matching is explicit entry,
  then prefix rule, then identical path. A dry run is the default and
  `--apply` is required to move anything. Unmapped paths are orphans:
  reported and kept, never deleted; only `--prune` removes anything, and
  only an already-empty orphan directory. Case-only renames stage
  through a temporary name, because macOS, SMB and Dropbox are
  case-insensitive and a direct rename there can lose data. Re-running
  after a migration plans nothing.
* **`create --skip-existing-files`** makes re-scaffolding idempotent.
  Re-running a template skipped existing directories but refused to
  overwrite any `<file>`, so a second run failed outright.
* **`dirtt placeholders` now reports every variable the build needs.**
  It only scanned the top-level template's own text, so it missed
  variables used inside `xi:include`d templates and `href`'d content
  files. On a real template set it named two of seven, and `create`
  prompted for those two then failed partway with an undefined
  placeholder. Both commands now use the full union.
* **`<file substitute="false"/>`** copies an `href` source byte for
  byte, so a template set copied into a project as a record keeps its
  own placeholders. A seed file containing a literal `}}` previously
  failed outright. The default is unchanged.
* **A duplicate `id` is now an error** naming the id and both declaring
  templates, tracked across `xi:include`. It previously won last,
  silently pointing an `idref` link at the wrong directory.
* **Scaffold log.** A successful `create` appends one JSON line to
  `lib/dirtt/scaffold.log.jsonl` under the created root recording
  template, run, vars, date and actor. `--actor`, `--template-id` and
  `--run` set the fields; `--no-log` turns it off. A log that cannot be
  written warns and never fails the scaffold.
* `execute()` gained the `move` and `rmdir` actions behind migrate. A
  cross-filesystem move raises rather than silently copying, and an
  `rmdir` only ever removes an already-empty directory.


## 1.0.3 (2026-08-19)

* **The DTD now matches the format dirtt actually accepts.** Its
  `<dirtt>` ATTLIST declared only `basename`/`name`/`version`/`dirname`,
  all `#REQUIRED`, but every real template sets `username`, `group` and
  `perms` on the root, `project.xml` also sets `id` and `xmlns:xi`, and
  templates compose with `xi:include` — which the DTD never declared at
  all. Validating any actual template failed. The root attributes are
  now declared, `xi:include` is declared and allowed in the `dirtt` and
  `dir` content models, and `name`/`version`/`basename`/`dirname` are
  `#IMPLIED` to match the parser. All six packaged templates now pass
  `xmllint --valid`.
* **DTD URLs use `http://`, not `https://`.** libxml2 (xmllint, lxml,
  and most XML editors) is built without TLS and cannot fetch an
  `https://` DTD; it fails with `failed to load external entity` and
  silently skips validation. 1.0.2 introduced that regression while
  fixing the dead hostname. The system identifier is now
  `http://rjmoggach.github.io/python-dirtt/dtds/dirtt.dtd`, which
  GitHub Pages serves directly with no redirect.
* Templates declare `-//STUDIO//DTD dirtt 1.0//EN`.


## 1.0.2 (2026-08-18)

* The `DOCTYPE` in every packaged template, and in `dirtt.dtd` itself,
  pointed at `robmoggach.github.io`, an account name that no longer
  exists, so the DTD URL had been returning 404. All of them now point
  at `https://rjmoggach.github.io/python-dirtt/dtds/dirtt.dtd`, which
  resolves. dirtt itself ignores the `DOCTYPE`, so this only affected
  editors and tools that validate the templates.
* The project site was rebuilt for 1.x; it had been unchanged since
  January 2015.


## 1.0.1 (2026-08-18)

First release published to PyPI from the 1.x line.

* Fixed the packaged `project_shot.xml`: the volumetrics folder used
  `basename="scenes"`, colliding with the scenes folder so no
  `volumetrics/` directory was ever created and its five children landed
  in `scenes/`; and the `images/textures/master` symlink was one level
  short and always dangled. Building all five packaged templates
  together now yields 331 paths with all 54 symlinks resolving.
* Releases publish to PyPI from GitHub Actions.


## 1.0.0 (2026-08-18)

Full modernization for Python 3.10+ — same simple idea, new engine.

* **Breaking:** Python 3.10+ required; Python 2 support removed.
* New three-stage core: templates parse into an immutable dataclass tree
  (`Dir`/`File`/`Link`), the tree plans into an ordered list of `Action`
  records with absolute `pathlib` paths, and the plan executes — no more
  `os.chdir`, no more SAX handler with side effects.
* New `dirtt` CLI (`create`, `list`, `placeholders`, `introspect`)
  replaces `mktree.py`, `mkproject.py`, and `mktemplate.py`. The
  hardcoded uid allow-list is gone.
* `--dry-run` prints the full plan without touching the filesystem.
* JSON templates supported alongside XML; XML dialect unchanged.
* The embedded Paste template engine (`eval`/`exec`-based) is replaced
  with safe `{{name}}` substitution.
* Library errors raise `DirttError`/`TemplateError`/`BuildError` instead
  of printing and calling `sys.exit()`.
* `chown` only runs as root; otherwise skipped with a log message.
* Packaging: `pyproject.toml` (PEP 621) replaces `distutils`; zero
  runtime dependencies; test suite rewritten with pytest.


## 0.2.0

* cleaning out the dashing code
* docs to markdown... lost antiquated docs build system
* fixed URLs and incorrect versions in DTDs
* added DTDs to github pages page so xml checks should work as expected


## 0.1.9b6

* better testing
* checks for uid, gid as without chown/chgrp will fail


## 0.1.9b4

* there's not much else we really need to do although a few glitches here and there
* introspection is working
* need env vars for customized template source dirs
* new templates streamlined and de-dshng'd for the most part


## 0.1.3a1

* mostly working now
* issues all reported on github
* this works
* now need to polish before pypi


## 0.1.1a1

* Initial commit.  Everything is new!



