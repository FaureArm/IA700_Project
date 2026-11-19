"""Unit tests for the data module."""

import pandas as pd

from ia700_project import data


def test_load_data_calls_clean_dataset(monkeypatch) -> None:
    """Check that load_data delegates dataset cleaning."""
    expected = pd.DataFrame(
        {
            "gare_depart": ["Paris"],
            "gare_arrivee": ["Lyon"],
        }
    )
    captured = {}

    def fake_clean_dataset(path):
        captured["path"] = path
        return expected

    monkeypatch.setattr(
        data,
        "clean_dataset",
        fake_clean_dataset,
    )

    result = data.load_data("test.csv", 123)

    assert captured["path"] == "test.csv"
    pd.testing.assert_frame_equal(result, expected)


def test_data_path_points_to_csv() -> None:
    """Check that DATA_PATH points to the expected CSV filename."""
    assert data.DATA_PATH.name == "regularite-mensuelle-tgv-aqst.csv"
    assert data.DATA_PATH.parent.name == "data"
