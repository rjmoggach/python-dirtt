# Changes And News

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



