"""Tests for patchwork.template."""

import pytest
from patchwork.template import (
    TemplateError,
    build_template_context,
    render_template,
    render_value,
)


@pytest.fixture
def ctx():
    return build_template_context(
        method="GET",
        path="/users/42",
        headers={"content-type": "application/json"},
        params={"id": "42"},
    )


def test_render_template_plain_string(ctx):
    assert render_template("hello world", ctx) == "hello world"


def test_render_template_method(ctx):
    assert render_template("{{ request.method }}", ctx) == "GET"


def test_render_template_path(ctx):
    assert render_template("path={{ request.path }}", ctx) == "path=/users/42"


def test_render_template_nested_header(ctx):
    result = render_template("type={{ request.headers.content-type }}", ctx)
    # dotted resolution stops at non-dict; key not found → unchanged
    assert "{{" in result


def test_render_template_unknown_key_unchanged(ctx):
    result = render_template("{{ unknown.key }}", ctx)
    assert result == "{{ unknown.key }}"


def test_render_template_non_string_raises(ctx):
    with pytest.raises(TemplateError):
        render_template(123, ctx)


def test_render_value_dict(ctx):
    template = {"message": "method={{ request.method }}", "static": 42}
    result = render_value(template, ctx)
    assert result == {"message": "method=GET", "static": 42}


def test_render_value_list(ctx):
    template = ["{{ request.method }}", "{{ request.path }}"]
    result = render_value(template, ctx)
    assert result == ["GET", "/users/42"]


def test_render_value_nested(ctx):
    template = {"data": {"items": ["{{ request.method }}", "ok"]}}
    result = render_value(template, ctx)
    assert result == {"data": {"items": ["GET", "ok"]}}


def test_render_value_non_string_passthrough(ctx):
    assert render_value(99, ctx) == 99
    assert render_value(True, ctx) is True
    assert render_value(None, ctx) is None


def test_build_template_context_structure():
    ctx = build_template_context("post", "/items", {}, {"x": "1"})
    assert ctx["request"]["method"] == "POST"
    assert ctx["request"]["path"] == "/items"
    assert ctx["request"]["params"] == {"x": "1"}


def test_multiple_placeholders(ctx):
    tmpl = "{{ request.method }} {{ request.path }}"
    assert render_template(tmpl, ctx) == "GET /users/42"


def test_whitespace_variants(ctx):
    assert render_template("{{request.method}}", ctx) == "GET"
    assert render_template("{{  request.method  }}", ctx) == "GET"
