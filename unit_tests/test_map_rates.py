"""Unit tests for the map rates module."""

import pandas as pd
import pytest

from ia700_project import map_rates


@pytest.fixture
def sample_rows() -> pd.DataFrame:
    """Create sample traffic data for several routes."""
    return pd.DataFrame(
        [
            # Two rows for the same route, to test aggregation.
            ("Paris", "Lyon", 60, 5, 11),
            ("Paris", "Lyon", 40, 5, 9),
            # All trains are cancelled.
            ("Lille", "Nice", 50, 50, 5),
            # No planned trains.
            ("Bordeaux", "Toulouse", 0, 0, 0),
        ],
        columns=[
            "gare_depart",
            "gare_arrivee",
            "nb_train_prevu",
            "nb_annulation",
            "nb_train_retard_arrivee",
        ],
    )


def test_aggregate_map_rates_calculates_correct_rates(
    sample_rows: pd.DataFrame,
) -> None:
    """Check that rates are correctly calculated for each route."""
    result = map_rates.aggregate_map_rates(sample_rows)

    assert result[("Paris", "Lyon")]["cancellation"] == pytest.approx(0.10)
    assert result[("Paris", "Lyon")]["disruption"] == pytest.approx(0.30)
    assert result[("Paris", "Lyon")]["delay"] == pytest.approx(20 / 90)


def test_aggregate_map_rates_handles_fully_cancelled_route(
    sample_rows: pd.DataFrame,
) -> None:
    """Check that delay rates are omitted when all trains are cancelled."""
    result = map_rates.aggregate_map_rates(sample_rows)

    assert result[("Lille", "Nice")]["cancellation"] == pytest.approx(1.0)
    assert "disruption" not in result[("Lille", "Nice")]
    assert "delay" not in result[("Lille", "Nice")]


def test_aggregate_map_rates_ignores_routes_without_planned_trains(
    sample_rows: pd.DataFrame,
) -> None:
    """Check that routes with no planned trains are excluded."""
    result = map_rates.aggregate_map_rates(sample_rows)

    assert ("Bordeaux", "Toulouse") not in result


def test_aggregate_map_rates_returns_empty_dict_for_empty_dataframe() -> None:
    """Check that an empty DataFrame produces an empty result."""
    rows = pd.DataFrame(
        columns=[
            "gare_depart",
            "gare_arrivee",
            "nb_train_prevu",
            "nb_annulation",
            "nb_train_retard_arrivee",
        ]
    )

    result = map_rates.aggregate_map_rates(rows)

    assert result == {}


def test_aggregate_map_rates_keeps_cancellation_when_delay_is_invalid() -> (
    None
):
    """Check that valid cancellations are kept when delay data is invalid."""
    rows = pd.DataFrame(
        [
            ("Paris", "Lyon", 100, 10, 95),
        ],
        columns=[
            "gare_depart",
            "gare_arrivee",
            "nb_train_prevu",
            "nb_annulation",
            "nb_train_retard_arrivee",
        ],
    )

    result = map_rates.aggregate_map_rates(rows)

    assert result[("Paris", "Lyon")]["cancellation"] == pytest.approx(0.10)
    assert "disruption" not in result[("Paris", "Lyon")]
    assert "delay" not in result[("Paris", "Lyon")]


def test_aggregate_map_rates_ignores_invalid_cancellation_rows() -> None:
    """Check that rows with invalid cancellation counts are excluded."""
    rows = pd.DataFrame(
        [
            ("Paris", "Lyon", 100, 10, 20),
            ("Paris", "Lyon", 100, 110, 20),
            ("Paris", "Lyon", 100, -1, 20),
        ],
        columns=[
            "gare_depart",
            "gare_arrivee",
            "nb_train_prevu",
            "nb_annulation",
            "nb_train_retard_arrivee",
        ],
    )

    result = map_rates.aggregate_map_rates(rows)

    assert result[("Paris", "Lyon")]["cancellation"] == pytest.approx(0.10)
    assert result[("Paris", "Lyon")]["disruption"] == pytest.approx(0.30)
    assert result[("Paris", "Lyon")]["delay"] == pytest.approx(20 / 90)


def test_load_map_rates_returns_rates_from_provided_data(
    sample_rows: pd.DataFrame,
) -> None:
    """Check that load_map_rates computes rates from the provided DataFrame."""
    result = map_rates.load_map_rates(sample_rows)

    assert result[("Paris", "Lyon")]["cancellation"] == pytest.approx(0.10)
    assert result[("Paris", "Lyon")]["disruption"] == pytest.approx(0.30)
    assert result[("Paris", "Lyon")]["delay"] == pytest.approx(20 / 90)
