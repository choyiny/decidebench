import math

from decidebench.pareto import pareto_front


def test_dominated_points_are_dropped():
    pts = {"cheap": (1, 0.90), "mid": (2, 0.97), "dear": (80, 0.99), "worse": (3, 0.95)}
    assert pareto_front(pts) == {"cheap", "mid", "dear"}


def test_identical_points_are_both_kept():
    assert pareto_front({"a": (1, 0.9), "b": (1, 0.9)}) == {"a", "b"}


def test_equal_cost_higher_accuracy_dominates():
    assert pareto_front({"a": (0, 0.2), "b": (0, 0.4), "c": (5, 0.9)}) == {"b", "c"}


def test_nan_points_are_excluded_and_never_dominate():
    assert pareto_front({"a": (math.nan, 0.99), "b": (5, 0.9)}) == {"b"}
