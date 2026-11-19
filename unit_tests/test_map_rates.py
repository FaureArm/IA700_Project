"""Unit tests for the map rates module."""

import pandas as pd
import pytest

from ia700_project import map_rates
from ia700_project.constants import ARRIVAL, CANCELLED, DEPARTURE, PLANNED


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
            DEPARTURE,
            ARRIVAL,
            PLANNED,
            CANCELLED,
            map_rates.ARRIVAL_DELAY_COUNT,
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
    """Check that the delay rate is omitted when all trains are cancelled."""
    result = map_rates.aggregate_map_rates(sample_rows)

    assert result[("Lille", "Nice")]["cancellation"] == pytest.approx(1.0)
    assert result[("Lille", "Nice")]["disruption"] == pytest.approx(1.1)
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
            DEPARTURE,
            ARRIVAL,
            PLANNED,
            CANCELLED,
            map_rates.ARRIVAL_DELAY_COUNT,
        ]
    )

    result = map_rates.aggregate_map_rates(rows)

    assert result == {}


def test_load_map_rates_reads_csv_and_returns_rates(
    sample_rows: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """Check that the CSV is read and the calculated rates are returned."""
    csv_path = str(tmp_path / "rates.csv")
    modified_at = 123456789

    def mock_read_csv(*args, **kwargs) -> pd.DataFrame:
        """Return the sample data instead of reading a real CSV."""
        return sample_rows

    monkeypatch.setattr(map_rates.pd, "read_csv", mock_read_csv)

    result = map_rates.load_map_rates(csv_path, modified_at)

    assert result[("Paris", "Lyon")]["cancellation"] == pytest.approx(0.10)
    assert result[("Paris", "Lyon")]["disruption"] == pytest.approx(0.30)
    assert result[("Lille", "Nice")]["cancellation"] == pytest.approx(1.0)


def test_load_map_rates_passes_correct_csv_parameters(
    sample_rows: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """Check that the CSV reader receives the expected parameters."""
    csv_path = str(tmp_path / "rates.csv")
    modified_at = 987654321
    calls = []

    def mock_read_csv(*args, **kwargs) -> pd.DataFrame:
        """Record CSV reader arguments and return sample data."""
        calls.append((args, kwargs))
        return sample_rows

    monkeypatch.setattr(map_rates.pd, "read_csv", mock_read_csv)

    map_rates.load_map_rates(csv_path, modified_at)

    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args == (csv_path,)
    assert kwargs["sep"] == ";"
    assert kwargs["usecols"] == [
        DEPARTURE,
        ARRIVAL,
        PLANNED,
        CANCELLED,
        map_rates.ARRIVAL_DELAY_COUNT,
    ]
