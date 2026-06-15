"""Tests for the applied-tweaks optimization score (winsvalinn.core.optimization_score)."""

from winsvalinn.core import optimization_score


def test_compute_shape_and_bounds():
    data = optimization_score.compute()
    assert set(data) >= {"score", "applied", "total", "items"}
    assert isinstance(data["score"], int)
    assert 0 <= data["score"] <= 100
    assert isinstance(data["total"], int)
    assert 0 <= data["applied"] <= data["total"]


def test_score_matches_applied_ratio():
    data = optimization_score.compute()
    if data["total"]:
        expected = round(data["applied"] / data["total"] * 100)
        assert data["score"] == expected
    else:
        assert data["score"] == 0


def test_items_have_expected_fields():
    for item in optimization_score.compute()["items"]:
        assert {"id", "label", "applied"} <= set(item)
        assert isinstance(item["applied"], bool)


def test_breakdown_can_be_omitted():
    assert "items" not in optimization_score.compute(include_breakdown=False)
