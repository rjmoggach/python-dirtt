import pytest

from dirtt.exceptions import TemplateError
from dirtt.template import placeholders, substitute


def test_substitute_basic():
    assert substitute("root: {{root}}", {"root": "/jobs"}) == "root: /jobs"


def test_substitute_whitespace_tolerant():
    assert substitute("{{ name }} and {{name}}", {"name": "x"}) == "x and x"


def test_substitute_non_string_values():
    assert substitute("{{n}}", {"n": 3}) == "3"
    assert substitute("{{n}}", {"n": None}) == ""


def test_substitute_missing_strict_raises():
    with pytest.raises(TemplateError, match="undefined placeholder 'missing'"):
        substitute("{{missing}}", {})


def test_substitute_missing_lenient_leaves_literal():
    assert substitute("{{missing}}", {}, strict=False) == "{{missing}}"


def test_substitute_unbalanced_raises():
    with pytest.raises(TemplateError, match="no '}}'"):
        substitute("hey {{", {})
    with pytest.raises(TemplateError, match="outside expression"):
        substitute("hey }}", {})
    with pytest.raises(TemplateError, match="inside expression"):
        substitute("hey {{ {{", {})


def test_placeholders_order_and_dedupe():
    text = "{{b}} {{a}} {{b}} {{ c }}"
    assert placeholders(text) == ["b", "a", "c"]


def test_placeholders_empty():
    assert placeholders("no vars here") == []
