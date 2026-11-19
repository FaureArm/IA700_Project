"""Unit tests for the indicators module."""

import pandas as pd

from ia700_project.indicators import compute_overview_summary


def test_compute_overview_summary_returns_empty_dataframe():
    """Return an empty dataframe with the expected columns for empty data."""
    data = pd.DataFrame(columns=["gare_depart", "gare_arrivee", "date"])

    result = compute_overview_summary(data)

    assert result.empty
    assert list(result.columns) == [
        "route_count",
        "station_count",
        "latest_month",
    ]


def test_compute_overview_summary_counts_routes_and_stations():
    """The function should count unique routes and stations."""
    data = pd.DataFrame(
        {
            "gare_depart": [
                "PARIS LYON",
                "PARIS LYON",
                "LYON PART DIEU",
                "MARSEILLE",
            ],
            "gare_arrivee": [
                "LYON PART DIEU",
                "LYON PART DIEU",
                "PARIS LYON",
                "PARIS LYON",
            ],
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-02-01",
                    "2025-03-01",
                    "2025-04-01",
                ]
            ),
        }
    )

    result = compute_overview_summary(data)

    assert result.loc[0, "route_count"] == 3
    assert result.loc[0, "station_count"] == 3
    assert result.loc[0, "latest_month"] == pd.Timestamp("2025-04-01")


def test_compute_overview_summary_ignores_incomplete_routes():
    """Routes with missing departure or arrival should not be counted."""
    data = pd.DataFrame(
        {
            "gare_depart": ["PARIS LYON", None, "MARSEILLE"],
            "gare_arrivee": ["LYON PART DIEU", "PARIS LYON", None],
            "date": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
        }
    )

    result = compute_overview_summary(data)

    assert result.loc[0, "route_count"] == 1
    assert result.loc[0, "station_count"] == 3


def test_compute_overview_summary_counts_reverse_routes_separately():
    """A route in the reverse direction should count as a distinct route."""
    data = pd.DataFrame(
        {
            "gare_depart": ["PARIS LYON", "LYON PART DIEU"],
            "gare_arrivee": ["LYON PART DIEU", "PARIS LYON"],
            "date": pd.to_datetime(["2025-01-01", "2025-02-01"]),
        }
    )

    result = compute_overview_summary(data)

    assert result.loc[0, "route_count"] == 2
    assert result.loc[0, "station_count"] == 2
