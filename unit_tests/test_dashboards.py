"""Unit tests for the dashboards module."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pandas as pd
import pytest

from ia700_project import dashboards


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Mock Streamlit components used by the dashboards."""
    mock_st = MagicMock()
    created_columns = []

    def create_columns(number):
        columns = [MagicMock() for _ in range(number)]
        created_columns.append(columns)
        return columns

    mock_st.columns.side_effect = create_columns
    mock_st.expander.return_value = MagicMock()
    mock_st.created_columns = created_columns

    monkeypatch.setattr(dashboards, "st", mock_st)

    return mock_st


@pytest.fixture
def travel_selection():
    """Create a sample travel selection."""
    return SimpleNamespace(
        departure="Paris",
        arrival="Lyon",
        travel_start=datetime(2025, 1, 10),
        travel_end=datetime(2025, 1, 15),
    )


@pytest.fixture
def comparison_selection():
    """Create a sample comparison selection."""
    return SimpleNamespace(
        entity="Liaison",
        metric="Taux de retard",
        top_n=10,
        min_volume=100,
    )


def test_render_travel_summary(mock_streamlit, travel_selection):
    """Test the display of travel information."""
    dashboards.render_travel_summary(travel_selection)

    mock_streamlit.subheader.assert_called_once_with("Paris → Lyon")
    mock_streamlit.write.assert_called_once_with(
        "Voyage du 10/01/2025 au 15/01/2025"
    )


def test_render_ranking(mock_streamlit, comparison_selection):
    """Test the ranking dashboard information."""
    dashboards.render_ranking(comparison_selection)

    mock_streamlit.subheader.assert_called_once_with("Classement · Liaison")
    mock_streamlit.caption.assert_called_once_with(
        "Taux de retard · 10 résultats maximum · "
        "minimum 100 circulations prévues"
    )
    mock_streamlit.info.assert_called_once()


def test_render_comparison_time_evolution(
    mock_streamlit,
    comparison_selection,
):
    """Test the comparison time evolution section."""
    dashboards.render_comparison_time_evolution(comparison_selection)

    mock_streamlit.subheader.assert_called_once_with("Comparer les évolutions")
    mock_streamlit.info.assert_called_once()


def test_render_summary_metrics(mock_streamlit):
    """Test the display of summary metrics."""
    dashboards.render_summary_metrics()

    mock_streamlit.subheader.assert_called_once_with(
        "Que montre l’historique ?"
    )
    mock_streamlit.columns.assert_called_once_with(4)

    columns = mock_streamlit.created_columns[-1]

    expected_metrics = [
        ("Circulations étudiées", "—"),
        ("Taux d’annulation", "—"),
        ("Taux de retard à l’arrivée", "—"),
        ("Retard moyen à l’arrivée", "—"),
    ]

    for column, expected in zip(columns, expected_metrics, strict=False):
        column.metric.assert_called_once_with(*expected)


def test_render_exploration_time_evolution(mock_streamlit):
    """Test the exploration time evolution section."""
    dashboards.render_exploration_time_evolution()

    mock_streamlit.subheader.assert_called_once_with("Évolution dans le temps")
    mock_streamlit.info.assert_called_once()


def test_render_delay_causes(mock_streamlit):
    """Test the delay causes section."""
    dashboards.render_delay_causes()

    mock_streamlit.subheader.assert_called_once_with("Causes des retards")
    mock_streamlit.info.assert_called_once()


def test_render_exploration_dashboard(mock_streamlit, travel_selection):
    """Test the complete exploration dashboard."""
    dashboards.render_exploration_dashboard(travel_selection)

    mock_streamlit.subheader.assert_any_call("Paris → Lyon")
    assert mock_streamlit.info.called
    mock_streamlit.expander.assert_called_once_with("Comprendre les résultats")


def test_render_comparison_dashboard(
    mock_streamlit,
    comparison_selection,
):
    """Test the complete comparison dashboard."""
    dashboards.render_comparison_dashboard(comparison_selection)

    mock_streamlit.subheader.assert_has_calls(
        [
            call("Classement · Liaison"),
            call("Comparer les évolutions"),
        ]
    )

    mock_streamlit.expander.assert_called_once_with(
        "Comment lire cette comparaison ?"
    )


@pytest.mark.parametrize(
    ("dataframe", "expected_values"),
    [
        (None, ("-", "-", "-")),
        (pd.DataFrame(), ("-", "-", "-")),
        (pd.DataFrame({"example": [1]}), (0, 0, 0)),
    ],
)
def test_render_overview_metrics(
    mock_streamlit,
    dataframe,
    expected_values,
):
    """Test overview metrics with empty and non-empty data."""
    dashboards.render_overview_metrics(dataframe)

    columns = mock_streamlit.created_columns[-1]

    expected_labels = [
        "Liaisons couvertes",
        "Gares représentées",
        "Dernier mois disponible",
    ]

    for column, label, value in zip(
        columns,
        expected_labels,
        expected_values,
        strict=False,
    ):
        column.metric.assert_called_once_with(label, value)


def test_render_overview_metrics_handles_type_error(mock_streamlit):
    """Test fallback values when Streamlit metrics raise TypeError."""
    columns = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]

    for column in columns:
        column.metric.side_effect = [TypeError, None]

    mock_streamlit.columns.side_effect = [
        columns,
        columns,
    ]

    dashboards.render_overview_metrics()

    for column, label in zip(
        columns,
        [
            "Liaisons couvertes",
            "Gares représentées",
            "Dernier mois disponible",
        ],
        strict=False,
    ):
        assert column.metric.call_count == 2
        column.metric.assert_called_with(label, "—")


def test_render_network_map(mock_streamlit, monkeypatch):
    """Test the network map section."""
    mock_map = MagicMock()
    monkeypatch.setattr(dashboards, "render_tgv_map", mock_map)

    dashboards.render_network_map()

    mock_streamlit.subheader.assert_called_once_with("Le réseau en un regard")
    mock_map.assert_called_once()


def test_render_overview_dashboard(mock_streamlit, monkeypatch):
    """Test the main overview dashboard entry point."""
    mock_metrics = MagicMock()
    mock_map = MagicMock()

    monkeypatch.setattr(
        dashboards,
        "render_overview_metrics",
        mock_metrics,
    )
    monkeypatch.setattr(
        dashboards,
        "render_network_map",
        mock_map,
    )

    dashboards.render_overview_dashboard()

    mock_metrics.assert_called_once_with(None)
    mock_map.assert_called_once()
