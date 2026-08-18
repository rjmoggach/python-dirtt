from pathlib import Path

import pytest

from dirtt.exceptions import BuildError
from dirtt.introspect import introspect
from dirtt.model import Dir, File, Link
from dirtt.parser import load_template


def _make_tree(base: Path) -> Path:
    root = base / "sample"
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "src" / "main.py").write_text("print('hi')\n")
    (root / "latest").symlink_to(root / "src")
    return root


def test_introspect_round_trip(tmp_path):
    root = _make_tree(tmp_path)
    xml = introspect(root)

    out = tmp_path / "sample.xml"
    out.write_text(xml)
    tree = load_template(out)

    assert tree.root.basename == "sample"
    assert tree.dirname == str(tmp_path)
    names = {node.basename: node for node in tree.root.children}
    assert isinstance(names["src"], Dir)
    assert isinstance(names["docs"], Dir)
    assert isinstance(names["latest"], Link)
    assert names["latest"].idref  # internal symlink became an idref
    src = names["src"]
    assert any(isinstance(c, File) and c.basename == "main.py" for c in src.children)


def test_introspect_external_symlink_keeps_ref(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    external = tmp_path / "outside"
    external.mkdir()
    (root / "ext").symlink_to(external)
    xml = introspect(root)
    assert f'ref="{external}"' in xml


def test_introspect_rejects_non_directory(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("x")
    with pytest.raises(BuildError, match="is not a directory"):
        introspect(target)
