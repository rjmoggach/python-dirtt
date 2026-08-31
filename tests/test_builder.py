import stat
from pathlib import Path

import pytest

from dirtt.builder import build, execute, plan
from dirtt.exceptions import BuildError
from dirtt.model import Action, Dir, File, Tree
from dirtt.parser import load_template

TEMPLATES = Path(__file__).parent / "templates"


def _write(tmp_path: Path, body: str) -> Path:
    template = tmp_path / "template.xml"
    template.write_text(body)
    return template


FULL_TEMPLATE = (
    '<dirtt dirname="{{root}}" basename="proj" perms="0755">'
    '<dir basename="a" id="dir-a" perms="0750">'
    '<file basename="hello.txt" perms="0640"/>'
    "</dir>"
    '<dir basename="b"/>'
    '<link basename="link-to-a" idref="dir-a"/>'
    "</dirtt>"
)


def test_build_full_tree(tmp_path):
    template = _write(tmp_path, FULL_TEMPLATE)
    actions = build(template, {"root": str(tmp_path)})
    proj = tmp_path / "proj"
    assert (proj / "a").is_dir()
    assert (proj / "b").is_dir()
    assert (proj / "a" / "hello.txt").is_file()
    link = proj / "link-to-a"
    assert link.is_symlink()
    assert Path(link.readlink()) == proj / "a"
    assert stat.S_IMODE((proj / "a").stat().st_mode) == 0o750
    assert stat.S_IMODE((proj / "a" / "hello.txt").stat().st_mode) == 0o640
    assert len(actions) == 5


def test_dry_run_touches_nothing(tmp_path):
    template = _write(tmp_path, FULL_TEMPLATE)
    actions = build(template, {"root": str(tmp_path)}, dry_run=True)
    assert not (tmp_path / "proj").exists()
    ops = [a.op for a in actions]
    assert ops == ["mkdir", "mkdir", "write", "mkdir", "symlink"]
    # links resolve idrefs even in a dry run
    assert actions[-1].target == str(tmp_path / "proj" / "a")


def test_dest_overrides_dirname(tmp_path):
    template = _write(tmp_path, FULL_TEMPLATE.replace("{{root}}", "/nonexistent"))
    build(template, dest=tmp_path)
    assert (tmp_path / "proj" / "a").is_dir()


def test_existing_dir_is_skipped_silently(tmp_path):
    template = _write(tmp_path, FULL_TEMPLATE)
    (tmp_path / "proj").mkdir()
    build(template, {"root": str(tmp_path)})
    assert (tmp_path / "proj" / "a").is_dir()


def test_existing_dir_raises_with_warn(tmp_path):
    template = _write(tmp_path, FULL_TEMPLATE)
    (tmp_path / "proj").mkdir()
    with pytest.raises(BuildError, match="already exists"):
        build(template, {"root": str(tmp_path)}, warn=True)


def test_existing_file_collision_raises(tmp_path):
    template = _write(tmp_path, FULL_TEMPLATE)
    (tmp_path / "proj" / "a").mkdir(parents=True)
    (tmp_path / "proj" / "a" / "hello.txt").write_text("keep me")
    with pytest.raises(BuildError, match="refusing to overwrite"):
        build(template, {"root": str(tmp_path)})
    assert (tmp_path / "proj" / "a" / "hello.txt").read_text() == "keep me"


def test_confirm_skips_subtree(tmp_path):
    template = _write(tmp_path, FULL_TEMPLATE)
    tree = load_template(template, {"root": str(tmp_path)})
    actions = plan(tree)
    skipped = tmp_path / "proj" / "a"
    performed = execute(actions, on_confirm=lambda a: a.path != skipped)
    assert not skipped.exists()
    assert not (skipped / "hello.txt").exists()
    assert (tmp_path / "proj" / "b").is_dir()
    assert all(a.path != skipped for a in performed)


def test_file_href_renders_from_template_dir(tmp_path):
    (tmp_path / "snippet.txt").write_text("project is {{root}}")
    template = _write(
        tmp_path,
        '<dirtt dirname="{{root}}" basename="proj"><file basename="out.txt" href="snippet.txt"/></dirtt>',
    )
    build(template, {"root": str(tmp_path)})
    assert (tmp_path / "proj" / "out.txt").read_text() == f"project is {tmp_path}"


def test_nested_dirs_fixture_builds(tmp_path):
    actions = build(
        TEMPLATES / "test_nested_dirs.xml",
        {"project_root": str(tmp_path), "project_path": "data"},
    )
    assert (tmp_path / "data" / "d1" / "d2" / "d3").is_dir()
    assert len(actions) == 4


def test_substitute_false_copies_verbatim(tmp_path):
    seed = tmp_path / "seed.txt"
    raw = "keep this literal }} and this {{project_code}} unresolved"
    seed.write_text(raw)
    tree = Tree(
        root=Dir(basename="proj", children=(File(basename="out.txt", href=str(seed), substitute=False),)),
        dirname=str(tmp_path),
    )
    actions = plan(tree)
    execute(actions)
    assert (tmp_path / "proj" / "out.txt").read_text() == raw


def test_skip_existing_files_is_clean_noop(tmp_path):
    template = _write(tmp_path, FULL_TEMPLATE)
    first = build(template, {"root": str(tmp_path)}, skip_existing_files=True)
    assert len(first) == 5
    second = build(template, {"root": str(tmp_path)}, skip_existing_files=True)
    assert not any(a.op in ("write", "symlink") for a in second)


def test_skip_existing_files_leaves_content_untouched(tmp_path):
    template = _write(tmp_path, FULL_TEMPLATE)
    build(template, {"root": str(tmp_path)}, skip_existing_files=True)
    target = tmp_path / "proj" / "a" / "hello.txt"
    target.write_text("do not touch me")
    performed = build(template, {"root": str(tmp_path)}, skip_existing_files=True)
    assert target.read_text() == "do not touch me"
    assert not any(a.op == "write" for a in performed)


def test_skip_existing_files_default_false_still_raises(tmp_path):
    template = _write(tmp_path, FULL_TEMPLATE)
    build(template, {"root": str(tmp_path)})
    with pytest.raises(BuildError, match="refusing to overwrite"):
        build(template, {"root": str(tmp_path)})


def test_move_renames_and_creates_missing_destination_parent(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("content")
    dest = tmp_path / "newdir" / "dest.txt"
    action = Action("move", src, target=str(dest))
    performed = execute([action])
    assert dest.read_text() == "content"
    assert not src.exists()
    assert performed == [action]


def test_move_missing_source_skips_without_raising(tmp_path):
    src = tmp_path / "missing.txt"
    dest = tmp_path / "dest.txt"
    action = Action("move", src, target=str(dest))
    performed = execute([action])
    assert performed == []
    assert not dest.exists()


def test_move_onto_existing_destination_raises(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("a")
    dest = tmp_path / "dest.txt"
    dest.write_text("b")
    action = Action("move", src, target=str(dest))
    with pytest.raises(BuildError, match="refusing to overwrite"):
        execute([action])


def test_rmdir_removes_empty_dir(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    action = Action("rmdir", empty)
    performed = execute([action])
    assert not empty.exists()
    assert performed == [action]


def test_rmdir_nonempty_dir_skips_without_raising(tmp_path):
    full = tmp_path / "full"
    full.mkdir()
    (full / "file.txt").write_text("keep")
    action = Action("rmdir", full)
    performed = execute([action])
    assert full.exists()
    assert (full / "file.txt").read_text() == "keep"
    assert performed == []
