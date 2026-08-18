import json
from pathlib import Path

import pytest

from dirtt.exceptions import TemplateError
from dirtt.model import Dir, File, Link
from dirtt.parser import load_template, template_placeholders

TEMPLATES = Path(__file__).parent / "templates"


def test_parse_simple_xml():
    tree = load_template(TEMPLATES / "default_test_project.xml", {"project_root": "/tmp/x", "project_path": "data"})
    assert tree.root.basename == "data"
    assert tree.dirname == "/tmp/x"
    assert tree.name == "Project Tree"
    assert tree.root.perms == 0o2755
    assert tree.root.username == "pipeline"
    assert tree.root.group == "artist"


def test_parse_nested_dirs():
    tree = load_template(TEMPLATES / "test_nested_dirs.xml", {"project_root": "/tmp/x", "project_path": "data"})
    d1 = tree.root.children[0]
    assert isinstance(d1, Dir) and d1.basename == "d1"
    d2 = d1.children[0]
    d3 = d2.children[0]
    assert d2.basename == "d2" and d3.basename == "d3"
    assert d3.children == ()


def test_missing_context_raises():
    with pytest.raises(TemplateError, match="undefined placeholder"):
        load_template(TEMPLATES / "default_test_project.xml", {})


def test_basename_inferred_from_dirname(tmp_path):
    template = tmp_path / "t.xml"
    template.write_text('<dirtt name="t" version="1" dirname="/tmp/foo/bar"/>')
    tree = load_template(template)
    assert tree.root.basename == "bar"
    assert tree.dirname == "/tmp/foo"


def test_files_and_links(tmp_path):
    template = tmp_path / "t.xml"
    template.write_text(
        '<dirtt dirname="{{root}}" basename="proj">'
        '<dir basename="a" id="dir-a"/>'
        '<file basename="readme.txt" perms="0644"/>'
        '<link basename="shortcut" idref="dir-a"/>'
        "</dirtt>"
    )
    tree = load_template(template, {"root": str(tmp_path)})
    kinds = [type(node).__name__ for node in tree.root.children]
    assert kinds == ["Dir", "File", "Link"]
    file_node = tree.root.children[1]
    assert isinstance(file_node, File) and file_node.perms == 0o644
    link = tree.root.children[2]
    assert isinstance(link, Link) and link.idref == "dir-a"


def test_invalid_perms_raises(tmp_path):
    template = tmp_path / "t.xml"
    template.write_text('<dirtt dirname="/tmp" basename="x"><dir basename="a" perms="banana"/></dirtt>')
    with pytest.raises(TemplateError, match="invalid perms"):
        load_template(template)


def test_xi_include(tmp_path):
    (tmp_path / "child.xml").write_text(
        '<dirtt dirname="/ignored" basename="ignored"><dir basename="included"/></dirtt>'
    )
    template = tmp_path / "parent.xml"
    template.write_text(
        '<dirtt dirname="/tmp" basename="proj" xmlns:xi="http://www.w3.org/2001/XInclude">'
        '<dir basename="sub"><xi:include href="child.xml"/></dir>'
        "</dirtt>"
    )
    tree = load_template(template)
    sub = tree.root.children[0]
    assert isinstance(sub, Dir)
    assert [c.basename for c in sub.children] == ["included"]


def test_include_cycle_raises(tmp_path):
    a = tmp_path / "a.xml"
    b = tmp_path / "b.xml"
    a.write_text('<dirtt dirname="/tmp" basename="a"><include href="b.xml"/></dirtt>')
    b.write_text('<dirtt dirname="/tmp" basename="b"><include href="a.xml"/></dirtt>')
    with pytest.raises(TemplateError, match="cycle"):
        load_template(a)


def test_parse_json(tmp_path):
    template = tmp_path / "t.json"
    template.write_text(
        json.dumps(
            {
                "name": "JSON Tree",
                "dirname": "{{root}}",
                "basename": "proj",
                "perms": "02755",
                "children": [
                    {"type": "dir", "basename": "src", "children": [{"type": "file", "basename": "main.py"}]},
                    {"type": "file", "basename": "notes.txt", "content": "hello {{root}}"},
                    {"type": "link", "basename": "latest", "ref": "src"},
                ],
            }
        )
    )
    tree = load_template(template, {"root": "/tmp/jsontest"})
    assert tree.name == "JSON Tree"
    assert tree.root.perms == 0o2755
    src, notes, latest = tree.root.children
    assert isinstance(src, Dir) and isinstance(src.children[0], File)
    assert isinstance(notes, File) and notes.content == "hello /tmp/jsontest"
    assert isinstance(latest, Link) and latest.ref == "src"


def test_nonexistent_template_raises():
    with pytest.raises(TemplateError, match="does not exist"):
        load_template("/nonexistent/never/t.xml")


def test_template_placeholders():
    names = template_placeholders(TEMPLATES / "default_test_project.xml")
    assert names == ["project_root", "project_path"]
