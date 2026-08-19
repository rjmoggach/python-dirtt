# Changes And News

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



