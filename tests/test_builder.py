import logging
import os
import shutil
import stat
from pathlib import Path

import pytest

import dirtt.builder
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


def _make_source_tree(root: Path) -> Path:
    """A small tree with nesting, permissions, and a symlink."""
    src = root / "src"
    (src / "media" / "nested").mkdir(parents=True)
    (src / "top.txt").write_text("top level")
    (src / "media" / "clip.mov").write_bytes(b"\x00\x01binary payload\xff")
    (src / "media" / "nested" / "deep.txt").write_text("deep")
    (src / "media" / "nested").chmod(0o750)
    (src / "top.txt").chmod(0o640)
    os.symlink("media/clip.mov", src / "link-to-clip")
    return src


def _snapshot(root: Path) -> dict:
    """Everything under ``root`` that a faithful copy must reproduce."""
    out: dict = {}
    for path in sorted(root.rglob("*")):
        rel = str(path.relative_to(root))
        if path.is_symlink():
            out[rel] = ("symlink", os.readlink(path))
        elif path.is_dir():
            out[rel] = ("dir", stat.S_IMODE(path.stat().st_mode))
        else:
            info = path.stat()
            out[rel] = ("file", path.read_bytes(), stat.S_IMODE(info.st_mode), int(info.st_mtime))
    return out


def _force_shutil_fallback(monkeypatch) -> None:
    monkeypatch.setattr(dirtt.builder, "_RSYNC_BINARY", "dirtt-no-such-rsync-binary")


def test_copy_directory_tree_reproduces_it_and_leaves_source_intact(tmp_path):
    src = _make_source_tree(tmp_path)
    before = _snapshot(src)
    dest = tmp_path / "dest"
    action = Action("copy", src, target=str(dest))
    performed = execute([action])
    assert performed == [action]
    assert _snapshot(dest) == before
    assert _snapshot(src) == before
    assert src.is_dir()


def test_copy_rsync_and_shutil_fallback_produce_identical_trees(tmp_path, monkeypatch, caplog):
    src = _make_source_tree(tmp_path)
    with_rsync = tmp_path / "with_rsync"
    execute([Action("copy", src, target=str(with_rsync))])

    fallback = tmp_path / "fallback"
    _force_shutil_fallback(monkeypatch)
    with caplog.at_level(logging.WARNING, logger="dirtt"):
        execute([Action("copy", src, target=str(fallback))])

    assert _snapshot(fallback) == _snapshot(with_rsync)
    assert _snapshot(fallback) == _snapshot(src)
    assert any("shutil.copytree" in record.message for record in caplog.records)
    # the destination is a peer of the source, not a nested copy of it
    assert not (with_rsync / "src").exists()
    assert (with_rsync / "top.txt").read_text() == "top level"


@pytest.mark.skipif(shutil.which("rsync") is None, reason="rsync not installed")
def test_copy_uses_rsync_when_available(tmp_path, caplog):
    src = _make_source_tree(tmp_path)
    dest = tmp_path / "dest"
    with caplog.at_level(logging.WARNING, logger="dirtt"):
        execute([Action("copy", src, target=str(dest))])
    assert not any("shutil.copytree" in record.message for record in caplog.records)
    assert _snapshot(dest) == _snapshot(src)


def test_copy_preserves_symlinks_without_dereferencing(tmp_path):
    src = _make_source_tree(tmp_path)
    dest = tmp_path / "dest"
    execute([Action("copy", src, target=str(dest))])
    link = dest / "link-to-clip"
    assert link.is_symlink()
    assert os.readlink(link) == "media/clip.mov"


def test_copy_symlink_source_recreates_the_link(tmp_path):
    (tmp_path / "real.txt").write_text("real")
    link = tmp_path / "link.txt"
    os.symlink("real.txt", link)
    dest = tmp_path / "copied-link"
    execute([Action("copy", link, target=str(dest))])
    assert dest.is_symlink()
    assert os.readlink(dest) == "real.txt"


def test_copy_onto_existing_destination_raises(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("a")
    dest = tmp_path / "dest.txt"
    dest.write_text("b")
    with pytest.raises(BuildError, match="refusing to overwrite"):
        execute([Action("copy", src, target=str(dest))])
    assert dest.read_text() == "b"
    assert src.read_text() == "a"


def test_copy_onto_existing_symlink_destination_raises(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("a")
    dest = tmp_path / "dangling"
    os.symlink("nowhere", dest)
    with pytest.raises(BuildError, match="refusing to overwrite"):
        execute([Action("copy", src, target=str(dest))])


def test_copy_missing_source_skips_without_raising(tmp_path, caplog):
    src = tmp_path / "missing"
    dest = tmp_path / "dest"
    with caplog.at_level(logging.WARNING, logger="dirtt"):
        performed = execute([Action("copy", src, target=str(dest))])
    assert performed == []
    assert not dest.exists()
    assert any("copy source does not exist" in record.message for record in caplog.records)


def test_copy_creates_missing_destination_parent(tmp_path):
    src = _make_source_tree(tmp_path)
    dest = tmp_path / "a" / "b" / "c" / "dest"
    execute([Action("copy", src, target=str(dest))])
    assert (dest / "media" / "nested" / "deep.txt").read_text() == "deep"


def test_copy_single_file_preserves_content_and_metadata(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("payload")
    src.chmod(0o640)
    dest = tmp_path / "newdir" / "dest.txt"
    execute([Action("copy", src, target=str(dest))])
    assert dest.read_text() == "payload"
    assert stat.S_IMODE(dest.stat().st_mode) == 0o640
    assert int(dest.stat().st_mtime) == int(src.stat().st_mtime)
    assert src.read_text() == "payload"


def test_copy_dry_run_performs_no_copy(tmp_path):
    src = _make_source_tree(tmp_path)
    dest = tmp_path / "dest"
    action = Action("copy", src, target=str(dest))
    assert execute([action], dry_run=True) == [action]
    assert not dest.exists()


def test_copy_under_skipped_directory_is_not_performed(tmp_path):
    root = tmp_path / "proj"
    src = root / "src.txt"
    root.mkdir()
    src.write_text("payload")
    dest = tmp_path / "dest.txt"
    actions = [Action("mkdir", root), Action("copy", src, target=str(dest))]
    performed = execute(actions, on_confirm=lambda a: False)
    assert performed == []
    assert not dest.exists()
