from pathlib import Path

from decidebench.pin import render


def test_pins_regenerate_the_committed_regression_test_exactly():
    path = Path(__file__).parent / "test_regression_v1.py"
    assert render(path.read_text()) == path.read_text()


def test_v2_pins_regenerate_exactly():
    from decidebench.paths import V2_DATA_DIR, V2_RESULTS_DIR

    path = Path(__file__).parent / "test_regression_v2.py"
    assert render(path.read_text(), V2_DATA_DIR, V2_RESULTS_DIR) == path.read_text()
