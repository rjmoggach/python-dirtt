from pathlib import Path

import pytest

from dirtt.cli import main

TEMPLATE_BODY = (
    '<dirtt dirname="{{root}}" basename="proj">'
    '<dir basename="a"/><file basename="f.txt"/>'
    "</dirtt>"
)


@pytest.fixture
def template(tmp_path):
    path = tmp_path / "t.xml"
    path.write_text(TEMPLATE_BODY)
    return path


def test_create(template, tmp_path, capsys):
    code = main(["create", "-t", str(template), "--var", f"root={tmp_path}"])
    assert code == 0
    assert (tmp_path / "proj" / "a").is_dir()
    assert (tmp_path / "proj" / "f.txt").is_file()
    assert "created tree: 3 actions" in capsys.readouterr().out


def test_create_dry_run(template, tmp_path, capsys):
    code = main(["create", "-t", str(template), "--var", f"root={tmp_path}", "--dry-run"])
    assert code == 0
    assert not (tmp_path / "proj").exists()
    out = capsys.readouterr().out
    assert "mkdir" in out and "write" in out and "nothing created" in out


def test_create_missing_var_non_tty_exits(template, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    with pytest.raises(SystemExit, match="missing template variable"):
        main(["create", "-t", str(template)])


def test_create_error_returns_1(tmp_path, capsys):
    code = main(["create", "-t", str(tmp_path / "missing.xml")])
    assert code == 1
    assert "error:" in capsys.readouterr().err


def test_placeholders(template, capsys):
    assert main(["placeholders", "-t", str(template)]) == 0
    assert capsys.readouterr().out.split() == ["root"]


def test_list(capsys):
    assert main(["list"]) == 0
    assert "project.xml" in capsys.readouterr().out


def test_introspect_to_file(tmp_path, capsys):
    (tmp_path / "tree" / "sub").mkdir(parents=True)
    out = tmp_path / "out.xml"
    assert main(["introspect", str(tmp_path / "tree"), "-o", str(out)]) == 0
    text = out.read_text()
    assert "<dirtt" in text and 'basename="sub"' in text


def test_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    import dirtt
    assert dirtt.__version__ in capsys.readouterr().out
