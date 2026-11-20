"""Unit tests for the models module."""

from dataclasses import FrozenInstanceError
from datetime import date

import pandas as pd
import pytest

from ia700_project.models import (
    ComparisonSelection,
    LoadedData,
    TravelSelection,
)


def test_travel_selection_creation():
    """Test TravelSelection initialization."""
    selection = TravelSelection(
        departure="Paris",
        arrival="Lyon",
        travel_start=date(2026, 11, 20),
        travel_end=date(2026, 11, 22),
    )

    assert selection.departure == "Paris"
    assert selection.arrival == "Lyon"
    assert selection.travel_start == date(2026, 11, 20)
    assert selection.travel_end == date(2026, 11, 22)


def test_travel_selection_is_frozen():
    """Test that TravelSelection cannot be modified."""
    selection = TravelSelection(
        departure="Paris",
        arrival="Lyon",
        travel_start=date(2026, 11, 20),
        travel_end=date(2026, 11, 22),
    )

    with pytest.raises(FrozenInstanceError):
        selection.departure = "Marseille"


def test_loaded_data_initialization():
    """Test LoadedData initialization."""
    data = pd.DataFrame({"value": [1, 2, 3]})
    loaded = LoadedData(data, excluded_rows=2, source="test.csv")

    assert loaded.data_.equals(data)
    assert loaded.excluded_rows_ == 2
    assert loaded.source_ == "test.csv"


def test_loaded_data_total_rows():
    """Test total row count including excluded rows."""
    data = pd.DataFrame({"value": [1, 2, 3]})
    loaded = LoadedData(data, excluded_rows=2, source="test.csv")

    assert loaded.total_rows() == 5


def test_loaded_data_total_included_rows():
    """Test included row count."""
    data = pd.DataFrame({"value": [1, 2, 3]})
    loaded = LoadedData(data, excluded_rows=2, source="test.csv")

    assert loaded.total_included_rows() == 3


def test_comparison_selection_creation():
    """Test ComparisonSelection initialization."""
    selection = ComparisonSelection(
        entity="Paris",
        metric="delay_rate",
        top_n=10,
        min_volume=100,
    )

    assert selection.entity == "Paris"
    assert selection.metric == "delay_rate"
    assert selection.top_n == 10
    assert selection.min_volume == 100


def test_comparison_selection_is_frozen():
    """Test that ComparisonSelection cannot be modified."""
    selection = ComparisonSelection(
        entity="Paris",
        metric="delay_rate",
        top_n=10,
        min_volume=100,
    )

    with pytest.raises(FrozenInstanceError):
        selection.top_n = 5
