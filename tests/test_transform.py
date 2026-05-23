"""Tests for patchwork.transform."""

import pytest

from patchwork.transform import (
    TransformError,
    apply_transforms,
    parse_transforms,
)


# ---------------------------------------------------------------------------
# parse_transforms
# ---------------------------------------------------------------------------

def test_parse_transforms_none_returns_empty_list():
    assert parse_transforms(None) == []


def test_parse_transforms_empty_list_returns_empty_list():
    assert parse_transforms([]) == []


def test_parse_transforms_not_a_list_raises():
    with pytest.raises(TransformError, match="must be a list"):
        parse_transforms({"type": "wrap"})


def test_parse_transforms_item_not_a_mapping_raises():
    with pytest.raises(TransformError, match="must be a mapping"):
        parse_transforms(["wrap"])


def test_parse_transforms_unknown_type_raises():
    with pytest.raises(TransformError, match="unknown type"):
        parse_transforms([{"type": "explode"}])


def test_parse_transforms_missing_type_raises():
    with pytest.raises(TransformError, match="unknown type"):
        parse_transforms([{"keys": ["id"]}])


def test_parse_transforms_valid_returns_list():
    raw = [{"type": "wrap"}, {"type": "uppercase"}]
    result = parse_transforms(raw)
    assert len(result) == 2
    assert result[0]["type"] == "wrap"
    assert result[1]["type"] == "uppercase"


# ---------------------------------------------------------------------------
# apply_transforms – uppercase
# ---------------------------------------------------------------------------

def test_uppercase_string():
    assert apply_transforms("hello", [{"type": "uppercase"}]) == "HELLO"


def test_uppercase_dict_values():
    body = {"msg": "hi", "code": 1}
    result = apply_transforms(body, [{"type": "uppercase"}])
    assert result == {"msg": "HI", "code": 1}


def test_uppercase_nested():
    body = {"a": {"b": "deep"}}
    result = apply_transforms(body, [{"type": "uppercase"}])
    assert result == {"a": {"b": "DEEP"}}


# ---------------------------------------------------------------------------
# apply_transforms – lowercase
# ---------------------------------------------------------------------------

def test_lowercase_string():
    assert apply_transforms("WORLD", [{"type": "lowercase"}]) == "world"


# ---------------------------------------------------------------------------
# apply_transforms – wrap
# ---------------------------------------------------------------------------

def test_wrap_dict():
    body = {"id": 1}
    assert apply_transforms(body, [{"type": "wrap"}]) == {"data": {"id": 1}}


def test_wrap_list():
    body = [1, 2, 3]
    assert apply_transforms(body, [{"type": "wrap"}]) == {"data": [1, 2, 3]}


# ---------------------------------------------------------------------------
# apply_transforms – omit_keys
# ---------------------------------------------------------------------------

def test_omit_keys_removes_specified_keys():
    body = {"id": 1, "secret": "x", "name": "Alice"}
    result = apply_transforms(body, [{"type": "omit_keys", "keys": ["secret"]}])
    assert result == {"id": 1, "name": "Alice"}


def test_omit_keys_non_dict_body_unchanged():
    body = [1, 2, 3]
    result = apply_transforms(body, [{"type": "omit_keys", "keys": ["id"]}])
    assert result == [1, 2, 3]


# ---------------------------------------------------------------------------
# apply_transforms – pipeline
# ---------------------------------------------------------------------------

def test_pipeline_wrap_then_uppercase():
    body = {"msg": "hello"}
    transforms = [{"type": "wrap"}, {"type": "uppercase"}]
    result = apply_transforms(body, transforms)
    assert result == {"data": {"msg": "HELLO"}}


def test_empty_transforms_returns_body_unchanged():
    body = {"x": 1}
    assert apply_transforms(body, []) is body
