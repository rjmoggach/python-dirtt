"""Tests for :mod:`dirtt.migrate`: planning a layout-to-layout migration."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from dirtt import migrate
from dirtt.builder import execute
from dirtt.exceptions import BuildError, TemplateError
from dirtt.model import Action

# The real 2015 -> 2026.01 corpus lives beside this repo; the acceptance
# test skips cleanly when it is not checked out.
_CANDIDATES = (
    Path(__file__).resolve().parents[2] / "python-dirtt-templates" / "migrations" / "2015_to_2026.01.json",
    Path("/Users/rob/Code/python-dirtt-templates/migrations/2015_to_2026.01.json"),
)
REAL_MAP = next((path for path in _CANDIDATES if path.is_file()), None)


# -- helpers ---------------------------------------------------------------


def schema(entries: dict[str, str], **extra: object) -> dict[str, object]:
    """A minimal valid mapping document."""
    return {"migration_schema": 1, "map": dict(entries), **extra}


def make_tree(root: Path, dirs: tuple[str, ...] = (), files: tuple[tuple[str, str], ...] = ()) -> None:
    for name in dirs:
        (root / name).mkdir(parents=True, exist_ok=True)
    for name, text in files:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def moves(actions: list[Action], root: Path) -> list[tuple[str, str]]:
    """The ``move`` actions as ``(source, destination)`` root-relative pairs."""
    base = root.resolve()
    return [
        (str(action.path.relative_to(base)), str(Path(action.target or "").relative_to(base)))
        for action in actions
        if action.op == "move"
    ]


def snapshot(root: Path) -> set[str]:
    return {str(path.relative_to(root)) for path in root.rglob("*")}


# -- matching --------------------------------------------------------------


def test_plain_rename_is_a_single_move(tmp_path: Path) -> None:
    make_tree(tmp_path, files=(("work/_DAILIES/day01.txt", "grade"),))
    actions, report = migrate.plan_migration(tmp_path, schema({"work/_DAILIES": "media/dailies"}))
    assert moves(actions, tmp_path) == [("work/_DAILIES", "media/dailies")]
    assert report == []


def test_prefix_rule_replaces_the_prefix(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("library/shoot/hdri",))
    mapping = schema({}, prefix_rules={"library/shoot/": "work/shoot/"})
    actions, report = migrate.plan_migration(tmp_path, mapping)
    assert moves(actions, tmp_path) == [("library/shoot/hdri", "work/shoot/hdri")]
    assert report == []


def test_explicit_map_wins_over_a_prefix_rule(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("library/shoot/scans",))
    mapping = schema({"library/shoot/scans": "media/scans"}, prefix_rules={"library/shoot/": "work/shoot/"})
    actions, _ = migrate.plan_migration(tmp_path, mapping)
    assert moves(actions, tmp_path) == [("library/shoot/scans", "media/scans")]


def test_identical_path_produces_no_action(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("shots/seq010",))
    actions, report = migrate.plan_migration(tmp_path, schema({"shots": "shots"}))
    assert actions == []
    assert report == []


def test_case_only_rename_is_planned_as_two_steps(tmp_path: Path) -> None:
    make_tree(tmp_path, files=(("production/Creative/board.txt", "art"),))
    actions, _ = migrate.plan_migration(tmp_path, schema({"production/Creative": "production/creative"}))
    assert moves(actions, tmp_path) == [
        ("production/Creative", "production/Creative__mig"),
        ("production/Creative__mig", "production/creative"),
    ]


def test_case_only_basename_across_parents_is_also_two_stepped(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("production/Notes",))
    actions, _ = migrate.plan_migration(tmp_path, schema({"production/Notes": "work/production/notes"}))
    assert moves(actions, tmp_path) == [
        ("production/Notes", "production/Notes__mig"),
        ("production/Notes__mig", "work/production/notes"),
    ]


def test_nested_parent_and_child_renames_compose(tmp_path: Path) -> None:
    make_tree(tmp_path, files=(("library/assets/char/hero.txt", "rig"),))
    mapping = schema({"library": "assets", "library/assets/char": "assets/char"})
    actions, _ = migrate.plan_migration(tmp_path, mapping)
    assert moves(actions, tmp_path) == [
        ("library", "assets"),
        ("assets/assets/char", "assets/char"),
    ]


def test_swap_stages_through_a_temporary_name(tmp_path: Path) -> None:
    make_tree(tmp_path, files=(("a/from_a.txt", "a"), ("b/from_b.txt", "b")))
    actions, _ = migrate.plan_migration(tmp_path, schema({"a": "b", "b": "a"}))
    planned = moves(actions, tmp_path)
    assert len(planned) == 3
    staged = planned[0][1]
    assert staged.startswith(".__dirtt_tmp_")
    assert planned == [("a", staged), ("b", "a"), (staged, "b")]

    execute(actions)
    assert (tmp_path / "b" / "from_a.txt").read_text() == "a"
    assert (tmp_path / "a" / "from_b.txt").read_text() == "b"


# -- orphans ---------------------------------------------------------------


def test_orphan_is_reported_but_never_moved_or_deleted(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("library",), files=(("old_stuff/keep.txt", "precious"),))
    actions, report = migrate.plan_migration(tmp_path, schema({"library": "assets"}))
    assert moves(actions, tmp_path) == [("library", "assets")]
    assert not any(action.op == "rmdir" for action in actions)
    assert any("old_stuff" in line for line in report)
    assert all("old_stuff" not in source for source, _ in moves(actions, tmp_path))
    assert (tmp_path / "old_stuff" / "keep.txt").read_text() == "precious"


def test_prune_removes_an_empty_orphan_dir_only(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("library", "empty_orphan"), files=(("full_orphan/keep.txt", "data"),))
    mapping = schema({"library": "assets"})

    actions, _ = migrate.plan_migration(tmp_path, mapping)
    assert not any(action.op == "rmdir" for action in actions)

    actions, report = migrate.plan_migration(tmp_path, mapping, prune=True)
    pruned = [action.path for action in actions if action.op == "rmdir"]
    assert pruned == [(tmp_path / "empty_orphan").resolve()]
    assert any("full_orphan" in line for line in report)
    assert (tmp_path / "full_orphan" / "keep.txt").exists()


# -- validation ------------------------------------------------------------


def test_missing_source_warns_and_is_skipped(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    make_tree(tmp_path, dirs=("library",))
    with caplog.at_level(logging.WARNING, logger="dirtt"):
        actions, _ = migrate.plan_migration(tmp_path, schema({"library": "assets", "gone": "also_gone"}))
    assert moves(actions, tmp_path) == [("library", "assets")]
    assert "migration source does not exist, skipping: gone" in caplog.text


def test_two_sources_onto_one_destination_raise(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("a", "b/x"))
    mapping = schema({"a": "c/x"}, prefix_rules={"b/": "c/"})
    with pytest.raises(BuildError) as excinfo:
        migrate.plan_migration(tmp_path, mapping)
    message = str(excinfo.value)
    assert "c/x" in message and "'a'" in message and "'b/x'" in message


def test_declared_merge_moves_children_into_the_shared_destination(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("production/_Client_IN/20150202-Job",), files=(("dropbox/note.txt", "hi"),))
    mapping = schema({"dropbox": "media/io/in", "production/_Client_IN": "media/io/in"})
    actions, _ = migrate.plan_migration(tmp_path, mapping)
    assert moves(actions, tmp_path) == [
        ("dropbox/note.txt", "media/io/in/note.txt"),
        ("production/_Client_IN/20150202-Job", "media/io/in/20150202-Job"),
    ]


def test_merge_sources_with_colliding_children_raise(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("a/shared", "b/shared"))
    with pytest.raises(BuildError) as excinfo:
        migrate.plan_migration(tmp_path, schema({"a": "c", "b": "c"}))
    message = str(excinfo.value)
    assert "c/shared" in message and "a/shared" in message and "b/shared" in message


def test_existing_destination_that_nothing_vacates_raises(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("a", "b"))
    with pytest.raises(BuildError, match="already exists"):
        migrate.plan_migration(tmp_path, schema({"a": "b"}))


def test_missing_root_raises(tmp_path: Path) -> None:
    with pytest.raises(BuildError, match="does not exist or is not a directory"):
        migrate.plan_migration(tmp_path / "nope", schema({"a": "b"}))


def test_planning_touches_nothing_on_disk(tmp_path: Path) -> None:
    make_tree(tmp_path, dirs=("library/assets/char", "empty_orphan"), files=(("work/_DAILIES/d.txt", "x"),))
    before = snapshot(tmp_path)
    migrate.plan_migration(tmp_path, schema({"library": "assets", "work/_DAILIES": "media/dailies"}), prune=True)
    assert snapshot(tmp_path) == before


# -- idempotence -----------------------------------------------------------


def test_replanning_after_apply_is_a_zero_move_no_op(tmp_path: Path) -> None:
    make_tree(
        tmp_path,
        dirs=("shots/seq010",),
        files=(("library/assets/char/hero.txt", "rig"), ("work/_DAILIES/day01.txt", "grade")),
    )
    mapping = schema(
        {
            "library": "assets",
            "library/assets/char": "assets/char",
            "work/_DAILIES": "media/dailies",
            "shots": "shots",
        }
    )
    actions, _ = migrate.plan_migration(tmp_path, mapping)
    execute(actions)
    assert (tmp_path / "assets/char/hero.txt").read_text() == "rig"
    assert (tmp_path / "media/dailies/day01.txt").read_text() == "grade"

    again, report = migrate.plan_migration(tmp_path, mapping)
    assert [action for action in again if action.op == "move"] == []
    assert report == []


# -- copy planning ---------------------------------------------------------


def roots(tmp_path: Path) -> tuple[Path, Path]:
    """An existing source tree and a destination root beside it."""
    source = tmp_path / "old"
    source.mkdir()
    return source, tmp_path / "new"


def copies(actions: list[Action], source: Path, dest: Path) -> list[tuple[str, str]]:
    """The ``copy`` actions as ``(source, destination)`` relative pairs."""
    origin, landing = source.resolve(), dest.resolve()
    return [
        (str(action.path.relative_to(origin)), str(Path(action.target or "").relative_to(landing)))
        for action in actions
        if action.op == "copy"
    ]


def test_copy_plan_is_flat_and_never_stages_a_case_only_rename(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, files=(("production/Creative/board.txt", "art"),))
    actions, report = migrate.plan_copy_migration(source, dest, schema({"production/Creative": "production/creative"}))
    assert copies(actions, source, dest) == [("production/Creative", "production/creative")]
    assert [action.op for action in actions] == ["copy"]
    assert report == []
    printed = " ".join(action.describe() for action in actions)
    assert migrate.TEMP_SUFFIX not in printed
    assert ".__dirtt_tmp_" not in printed


def test_copy_planning_writes_to_neither_tree(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, dirs=("library/assets/char", "empty_orphan"), files=(("work/_DAILIES/d.txt", "x"),))
    before = snapshot(source)
    migrate.plan_copy_migration(source, dest, schema({"library": "assets", "work/_DAILIES": "media/dailies"}))
    assert snapshot(source) == before
    assert not dest.exists()


def test_copy_orphans_are_reported_and_left_in_the_source(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, files=(("library/hero.txt", "rig"), ("dashboard/notes.txt", "precious")))
    actions, report = migrate.plan_copy_migration(source, dest, schema({"library": "assets"}))
    assert copies(actions, source, dest) == [("library", "assets")]
    assert report == ["orphan: dashboard (not copied; left in the source)"]
    assert all("dashboard" not in origin for origin, _ in copies(actions, source, dest))
    assert (source / "dashboard" / "notes.txt").read_text() == "precious"


def test_copy_carries_a_path_that_is_already_in_the_new_layout(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, dirs=("library",), files=(("shots/seq010/plate.txt", "exr"),))
    mapping = schema({"library": "assets", "shots": "shots"})
    actions, _ = migrate.plan_copy_migration(source, dest, mapping)
    assert copies(actions, source, dest) == [("library", "assets"), ("shots", "shots")]


def test_copy_nested_renames_compose_without_copying_twice(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, files=(("library/assets/char/hero.txt", "rig"), ("library/assets/prop/box.txt", "box")))
    mapping = schema(
        {"library": "assets", "library/assets/char": "assets/char", "library/assets/prop": "assets/prop"}
    )
    actions, report = migrate.plan_copy_migration(source, dest, mapping)
    assert copies(actions, source, dest) == [
        ("library/assets/char", "assets/char"),
        ("library/assets/prop", "assets/prop"),
    ]
    assert report == []
    assert all("assets/assets" not in (action.target or "") for action in actions)


def test_copy_leaves_an_orphan_nested_under_a_mapped_ancestor_behind(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(
        source,
        files=(
            ("library/assets/char/hero.txt", "rig"),
            ("library/assets/cam/keepme.txt", "keep"),
            ("library/library.txt", "stray"),
        ),
    )
    mapping = schema({"library": "assets", "library/assets/char": "assets/char"})
    actions, report = migrate.plan_copy_migration(source, dest, mapping)
    assert copies(actions, source, dest) == [("library/assets/char", "assets/char")]
    assert report == [
        "orphan: library/assets/cam (not copied; left in the source)",
        "orphan: library/library.txt (not copied; left in the source)",
    ]

    execute(actions)
    assert (dest / "assets" / "char" / "hero.txt").read_text() == "rig"
    assert not (dest / "assets" / "assets").exists()  # the old taxonomy never leaks into the new one
    assert list(dest.rglob("keepme.txt")) == []
    assert list(dest.rglob("library.txt")) == []
    # every orphan is still in the source, ready to be re-homed by hand
    assert (source / "library" / "assets" / "cam" / "keepme.txt").read_text() == "keep"
    assert (source / "library" / "library.txt").read_text() == "stray"


def test_copy_keeps_a_clean_mapped_directory_as_one_action(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(
        source,
        files=(
            ("library/assets/char/hero/rig.txt", "rig"),
            ("library/assets/char/hero/model.txt", "model"),
            ("library/assets/char/villain/rig.txt", "rig"),
            ("stray/keepme.txt", "keep"),
        ),
    )
    mapping = schema({"library": "assets", "library/assets/char": "assets/char"})
    actions, report = migrate.plan_copy_migration(source, dest, mapping)
    # a subtree holding no orphan stays one recursive copy, never one action per file
    assert copies(actions, source, dest) == [("library/assets/char", "assets/char")]
    assert len(actions) == 1
    assert report == ["orphan: stray (not copied; left in the source)"]


def test_move_orphans_still_travel_with_their_parent(tmp_path: Path) -> None:
    """The copy fix must not change the in-place migration's semantics."""
    make_tree(tmp_path, files=(("library/assets/char/hero.txt", "rig"), ("library/library.txt", "stray")))
    mapping = schema({"library": "assets", "library/assets/char": "assets/char"})
    actions, report = migrate.plan_migration(tmp_path, mapping)
    assert moves(actions, tmp_path) == [("library", "assets"), ("assets/assets/char", "assets/char")]
    assert report == ["orphan: library/library.txt (kept; travels to assets/library.txt with its parent)"]


def test_copy_explicit_map_wins_over_a_prefix_rule(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, dirs=("library/shoot/scans",))
    mapping = schema({"library/shoot/scans": "media/scans"}, prefix_rules={"library/shoot/": "work/shoot/"})
    actions, _ = migrate.plan_copy_migration(source, dest, mapping)
    assert copies(actions, source, dest) == [("library/shoot/scans", "media/scans")]


def test_copy_declared_merge_copies_children_into_the_shared_destination(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, dirs=("production/_Client_IN/20150202-Job",), files=(("dropbox/note.txt", "hi"),))
    mapping = schema({"dropbox": "media/io/in", "production/_Client_IN": "media/io/in"})
    actions, _ = migrate.plan_copy_migration(source, dest, mapping)
    assert copies(actions, source, dest) == [
        ("production/_Client_IN/20150202-Job", "media/io/in/20150202-Job"),
        ("dropbox/note.txt", "media/io/in/note.txt"),
    ]


def test_copy_merge_sources_with_colliding_children_raise(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, dirs=("a/shared", "b/shared"))
    with pytest.raises(BuildError) as excinfo:
        migrate.plan_copy_migration(source, dest, schema({"a": "c", "b": "c"}))
    message = str(excinfo.value)
    assert "c/shared" in message and "a/shared" in message and "b/shared" in message


def test_copy_two_undeclared_sources_onto_one_destination_raise(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, dirs=("a", "b/x"))
    mapping = schema({"a": "c/x"}, prefix_rules={"b/": "c/"})
    with pytest.raises(BuildError) as excinfo:
        migrate.plan_copy_migration(source, dest, mapping)
    message = str(excinfo.value)
    assert "c/x" in message and "'a'" in message and "'b/x'" in message


def test_copy_never_overwrites_an_existing_destination(tmp_path: Path) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, dirs=("library",))
    make_tree(dest, dirs=("assets", "unrelated"))
    with pytest.raises(BuildError, match="already exists"):
        migrate.plan_copy_migration(source, dest, schema({"library": "assets"}))

    # an unrelated occupant of the destination root is not a collision
    actions, _ = migrate.plan_copy_migration(source, dest, schema({"library": "renders"}))
    assert copies(actions, source, dest) == [("library", "renders")]


def test_copy_roots_may_not_contain_one_another(tmp_path: Path) -> None:
    source, _ = roots(tmp_path)
    make_tree(source, dirs=("library",))
    mapping = schema({"library": "assets"})
    for bad in (source / "inside", tmp_path, source):
        with pytest.raises(BuildError, match="neither may contain the other") as excinfo:
            migrate.plan_copy_migration(source, bad, mapping)
        assert str(source.resolve()) in str(excinfo.value)


def test_copy_missing_source_warns_and_is_skipped(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    source, dest = roots(tmp_path)
    make_tree(source, dirs=("library",))
    with caplog.at_level(logging.WARNING, logger="dirtt"):
        actions, _ = migrate.plan_copy_migration(source, dest, schema({"library": "assets", "gone": "also_gone"}))
    assert copies(actions, source, dest) == [("library", "assets")]
    assert "migration source does not exist, skipping: gone" in caplog.text


def test_copy_missing_source_root_raises(tmp_path: Path) -> None:
    with pytest.raises(BuildError, match="does not exist or is not a directory"):
        migrate.plan_copy_migration(tmp_path / "nope", tmp_path / "new", schema({"a": "b"}))


# -- mapping files ---------------------------------------------------------


def test_load_map_reads_the_schema_and_ignores_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "m.json"
    path.write_text(
        json.dumps({"migration_schema": 1, "from": "a", "notes": {"x": "y"}, "map": {"a": "b"}}),
        encoding="utf-8",
    )
    mapping = migrate.load_map(path)
    assert mapping["map"] == {"a": "b"}
    assert mapping["notes"] == {"x": "y"}


def test_load_map_rejects_another_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "m.json"
    path.write_text(json.dumps({"migration_schema": 2, "map": {}}), encoding="utf-8")
    with pytest.raises(TemplateError, match="unsupported migration_schema 2"):
        migrate.load_map(path)


def test_load_map_accepts_a_legacy_flat_map(tmp_path: Path) -> None:
    path = tmp_path / "flat.json"
    path.write_text(json.dumps({"work/_DAILIES": "work/dailies"}), encoding="utf-8")
    mapping = migrate.load_map(path)
    assert mapping["migration_schema"] == 1
    assert mapping["map"] == {"work/_DAILIES": "work/dailies"}


def test_load_map_rejects_bad_json_and_bad_types(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{nope", encoding="utf-8")
    with pytest.raises(TemplateError, match="not valid JSON"):
        migrate.load_map(broken)

    listy = tmp_path / "list.json"
    listy.write_text("[]", encoding="utf-8")
    with pytest.raises(TemplateError, match="must be a JSON object"):
        migrate.load_map(listy)

    typed = tmp_path / "typed.json"
    typed.write_text(json.dumps({"migration_schema": 1, "map": {"a": 3}}), encoding="utf-8")
    with pytest.raises(TemplateError, match="must be a string"):
        migrate.load_map(typed)

    escaping = tmp_path / "escape.json"
    escaping.write_text(json.dumps({"migration_schema": 1, "map": {"../a": "b"}}), encoding="utf-8")
    with pytest.raises(TemplateError, match="escapes the tree root"):
        migrate.load_map(escaping)


def test_load_map_reports_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(TemplateError, match="could not be read"):
        migrate.load_map(tmp_path / "absent.json")


# -- acceptance ------------------------------------------------------------


@pytest.mark.skipif(REAL_MAP is None, reason="python-dirtt-templates corpus not checked out")
def test_real_2015_to_2026_map_plans_a_full_tree(tmp_path: Path) -> None:
    assert REAL_MAP is not None
    document = json.loads(REAL_MAP.read_text(encoding="utf-8"))
    mapping = migrate.load_map(REAL_MAP)

    for source in document["map"]:
        (tmp_path / source).mkdir(parents=True, exist_ok=True)
    make_tree(
        tmp_path,
        dirs=("dropbox/20150101-ClientA", "production/_Client_IN/20150202-Job", "production/scratch"),
        files=(("legacy_backup/old.txt", "keep me"),),
    )

    actions, report = migrate.plan_migration(tmp_path, mapping)

    assert not any(action.op == "rmdir" for action in actions)
    assert all(action.op == "move" for action in actions)
    assert any("legacy_backup" in line for line in report)
    assert any("production/scratch" in line for line in report)

    planned = moves(actions, tmp_path)
    assert ("library", "assets") in planned
    for source in document["case_only_renames"]["paths"]:
        staged = f"{source}{migrate.TEMP_SUFFIX}"
        destination = document["map"][source]
        assert (source, staged) in planned, f"{source} was not staged through a temporary name"
        assert (staged, destination) in planned
        assert planned.index((source, staged)) < planned.index((staged, destination))

    # nothing is deleted and nothing was written while planning
    assert (tmp_path / "legacy_backup" / "old.txt").read_text() == "keep me"


@pytest.mark.skipif(REAL_MAP is None, reason="python-dirtt-templates corpus not checked out")
def test_real_2015_to_2026_map_copies_no_orphan_bytes(tmp_path: Path) -> None:
    assert REAL_MAP is not None
    document = json.loads(REAL_MAP.read_text(encoding="utf-8"))
    mapping = migrate.load_map(REAL_MAP)

    source, dest = roots(tmp_path)
    for key in document["map"]:
        directory = source / key
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{directory.name}.txt").write_text("mapped", encoding="utf-8")
    make_tree(
        source,
        files=(
            ("library/assets/cam/keepme.txt", "keep"),
            ("library/library.txt", "stray"),
            ("some_random_dir/keepme.txt", "keep"),
        ),
    )

    actions, report = migrate.plan_copy_migration(source, dest, mapping)
    assert all(action.op == "copy" for action in actions)
    assert report == [
        "orphan: library/assets/cam (not copied; left in the source)",
        "orphan: library/library.txt (not copied; left in the source)",
        "orphan: some_random_dir (not copied; left in the source)",
    ]
    assert len(actions) < 100, "de-nesting must not explode into one action per file"

    execute(actions)
    assert (dest / "assets" / "char" / "char.txt").read_text() == "mapped"
    assert (dest / "work" / "shoot" / "hdri" / "hdri.txt").read_text() == "mapped"
    assert not (dest / "assets" / "assets").exists()
    assert not (dest / "some_random_dir").exists()
    assert list(dest.rglob("keepme.txt")) == []
    assert list(dest.rglob("library.txt")) == []
    # the source keeps every orphan and every byte it started with
    assert (source / "library" / "assets" / "cam" / "keepme.txt").read_text() == "keep"
    assert (source / "library" / "library.txt").read_text() == "stray"
    assert (source / "some_random_dir" / "keepme.txt").read_text() == "keep"
