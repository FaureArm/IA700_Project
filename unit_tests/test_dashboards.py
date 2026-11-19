"""Unit tests for the dashboards module."""

from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest

from ia700_project import dashboards
from ia700_project.models import ComparisonSelection, TravelSelection


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
    mock_st.expander.return_value.__enter__.return_value = MagicMock()
    mock_st.expander.return_value.__exit__.return_value = False

    monkeypatch.setattr(dashboards, "st", mock_st)
    mock_st.created_columns = created_columns

    return mock_st


@pytest.fixture
def travel_selection():
    """Create a sample travel selection."""
    return TravelSelection(
        departure="Paris",
        arrival="Lyon",
        travel_start=date(2025, 1, 10),
        travel_end=date(2025, 1, 15),
    )


@pytest.fixture
def comparison_selection():
    """Create a sample comparison selection."""
    return ComparisonSelection(
        entity="Liaisons",
        metric="Taux de retard à l’arrivée",
        top_n=10,
        min_volume=100,
    )


@pytest.fixture
def sample_data():
    """Create a sample cleaned dataset."""
    return pd.DataFrame(
        {
            "gare_depart": ["Paris"],
            "gare_arrivee": ["Lyon"],
            "date": [pd.Timestamp("2025-01-01")],
        }
    )


# ---------------------------------------------------------------------
# Overview dashboard
# ---------------------------------------------------------------------


def test_render_overview_dashboard(mock_streamlit, monkeypatch, sample_data):
    """Test the overview dashboard entry point."""
    summary = pd.DataFrame(
        [{"route_count": 1, "station_count": 2, "latest_month": "2025-01"}]
    )
    compute = MagicMock(return_value=summary)
    metrics = MagicMock()
    network_map = MagicMock()

    monkeypatch.setattr(dashboards, "compute_overview_summary", compute)
    monkeypatch.setattr(dashboards, "render_overview_metrics", metrics)
    monkeypatch.setattr(dashboards, "render_network_map", network_map)

    dashboards.render_overview_dashboard(sample_data)

    compute.assert_called_once_with(sample_data)
    metrics.assert_called_once_with(summary)
    network_map.assert_called_once_with()


def test_render_network_map(mock_streamlit, monkeypatch, sample_data):
    """Test the network map section."""
    map_renderer = MagicMock()
    monkeypatch.setattr(dashboards, "render_tgv_map", map_renderer)

    dashboards.render_network_map()

    mock_streamlit.subheader.assert_called_once_with("Le réseau en un regard")
    map_renderer.assert_called_once_with()


@pytest.mark.parametrize(
    "summary",
    [None, pd.DataFrame()],
)
def test_render_overview_metrics_without_data(mock_streamlit, summary):
    """Test overview metrics when no usable data is available."""
    dashboards.render_overview_metrics(summary)

    mock_streamlit.caption.assert_called_once_with(
        "Aucune donnée exploitable pour les indicateurs du réseau."
    )

    columns = mock_streamlit.created_columns[0]

    columns[0].metric.assert_called_once_with("Liaisons couvertes", "—")
    columns[1].metric.assert_called_once_with("Gares représentées", "—")


def test_render_overview_metrics_with_data(mock_streamlit):
    """Test overview metrics with a valid summary."""
    summary = pd.DataFrame(
        [
            {
                "route_count": 1234,
                "station_count": 56,
                "latest_month": "2025-01",
            }
        ]
    )

    dashboards.render_overview_metrics(summary)

    columns = mock_streamlit.created_columns[0]

    columns[0].metric.assert_called_once_with("Liaisons couvertes", "1 234")
    columns[1].metric.assert_called_once_with("Gares représentées", "56")

    mock_streamlit.caption.assert_not_called()


# ---------------------------------------------------------------------
# Exploration dashboard
# ---------------------------------------------------------------------


def test_render_travel_summary(mock_streamlit, travel_selection):
    """Test the display of travel information."""
    dashboards.render_travel_summary(travel_selection)

    mock_streamlit.subheader.assert_called_once_with("Paris → Lyon")
    mock_streamlit.write.assert_called_once_with(
        "Voyage du 10/01/2025 au 15/01/2025"
    )


def test_render_summary_metrics(
    mock_streamlit,
    monkeypatch,
    sample_data,
    travel_selection,
):
    """Test the display of summary metrics."""
    monkeypatch.setattr(
        dashboards,
        "scheduled_trains_count",
        MagicMock(return_value=1234),
    )
    monkeypatch.setattr(
        dashboards,
        "cancellation_rate",
        MagicMock(return_value=2.5),
    )
    monkeypatch.setattr(
        dashboards,
        "delay_rate",
        MagicMock(return_value=12.25),
    )
    monkeypatch.setattr(
        dashboards,
        "avg_delay_length",
        MagicMock(return_value=18.5),
    )

    dashboards.render_summary_metrics(sample_data, travel_selection)

    mock_streamlit.subheader.assert_called_once_with(
        "Que montre l’historique ?"
    )

    columns = mock_streamlit.created_columns[0]

    expected_metrics = [
        ("Circulations prévues", "1 234"),
        ("Taux d’annulation", "2.50 %"),
        ("Taux de retard à l’arrivée", "12.25 %"),
        ("Retard moyen à l’arrivée", "18.5 min"),
    ]

    for column, expected in zip(columns, expected_metrics, strict=True):
        column.metric.assert_called_once_with(*expected)


def test_render_summary_metrics_with_missing_values(
    mock_streamlit,
    monkeypatch,
    sample_data,
    travel_selection,
):
    """Test summary metrics when indicators are unavailable."""
    for function_name in (
        "scheduled_trains_count",
        "cancellation_rate",
        "delay_rate",
        "avg_delay_length",
    ):
        monkeypatch.setattr(
            dashboards,
            function_name,
            MagicMock(return_value=None),
        )

    dashboards.render_summary_metrics(sample_data, travel_selection)

    columns = mock_streamlit.created_columns[0]

    expected_labels = [
        "Circulations prévues",
        "Taux d’annulation",
        "Taux de retard à l’arrivée",
        "Retard moyen à l’arrivée",
    ]

    for column, label in zip(columns, expected_labels, strict=True):
        column.metric.assert_called_once_with(label, "Indisponible")


@pytest.mark.parametrize(
    "history",
    [None, pd.DataFrame()],
)
def test_render_exploration_time_evolution_without_data(
    mock_streamlit, history
):
    """Test monthly evolution when no data is available."""
    dashboards.render_exploration_time_evolution(history)

    mock_streamlit.subheader.assert_called_once_with("Évolution dans le temps")
    mock_streamlit.info.assert_called_once_with(
        "Aucun historique mensuel disponible pour cette liaison."
    )
    mock_streamlit.line_chart.assert_not_called()


def test_render_exploration_time_evolution_with_data(mock_streamlit):
    """Test monthly evolution with valid data."""
    history = pd.DataFrame(
        {
            "month": [pd.Timestamp("2025-01-01")],
            "cancellation_rate_pct": [2.0],
            "arrival_delay_rate_pct": [10.0],
            "mean_arrival_delay_minutes": [15.0],
        }
    )

    dashboards.render_exploration_time_evolution(history)

    assert mock_streamlit.line_chart.call_count == 2

    first_chart = mock_streamlit.line_chart.call_args_list[0]
    assert list(first_chart.args[0].columns) == [
        "Annulations",
        "Retards à l’arrivée",
    ]

    second_chart = mock_streamlit.line_chart.call_args_list[1]
    assert list(second_chart.args[0].columns) == ["Retard moyen à l’arrivée"]


@pytest.mark.parametrize(
    "causes",
    [None, pd.DataFrame()],
)
def test_render_delay_causes_without_data(mock_streamlit, causes):
    """Test delay causes when no data is available."""
    dashboards.render_delay_causes(causes)

    mock_streamlit.subheader.assert_called_once_with("Causes des retards")
    mock_streamlit.info.assert_called_once_with(
        "Aucune répartition des causes disponible."
    )
    mock_streamlit.dataframe.assert_not_called()


def test_render_delay_causes_with_data(mock_streamlit):
    """Test delay causes with valid data."""
    causes = pd.DataFrame(
        {
            "cause": ["Signalisation"],
            "percentage": [12.0],
        }
    )

    dashboards.render_delay_causes(causes)

    mock_streamlit.dataframe.assert_called_once_with(
        causes,
        hide_index=True,
        column_config={
            "cause": mock_streamlit.column_config.TextColumn.return_value,
            "percentage": (
                mock_streamlit.column_config.NumberColumn.return_value
            ),
        },
    )
    mock_streamlit.column_config.TextColumn.assert_called_once_with(
        "Cause du retard", width="large"
    )
    mock_streamlit.column_config.NumberColumn.assert_called_once_with(
        "Part des retards (%)", format="%.2f"
    )


def test_render_exploration_dashboard(
    mock_streamlit,
    monkeypatch,
    sample_data,
    travel_selection,
):
    """Test the complete exploration dashboard."""
    monthly = pd.DataFrame({"month": [pd.Timestamp("2025-01-01")]})
    causes = pd.DataFrame({"cause": ["Signalisation"]})

    summary_renderer = MagicMock()
    time_renderer = MagicMock()
    causes_renderer = MagicMock()

    time_function = MagicMock(return_value=monthly)
    causes_function = MagicMock(return_value=causes)

    monkeypatch.setattr(dashboards, "render_summary_metrics", summary_renderer)
    monkeypatch.setattr(dashboards, "time_chart", time_function)
    monkeypatch.setattr(dashboards, "cause_of_delays_ranking", causes_function)
    monkeypatch.setattr(
        dashboards, "render_exploration_time_evolution", time_renderer
    )
    monkeypatch.setattr(dashboards, "render_delay_causes", causes_renderer)

    dashboards.render_exploration_dashboard(sample_data, travel_selection)

    mock_streamlit.subheader.assert_any_call("Paris → Lyon")

    summary_renderer.assert_called_once_with(sample_data, travel_selection)
    time_function.assert_called_once_with(sample_data, travel_selection)
    causes_function.assert_called_once_with(sample_data, travel_selection)

    time_renderer.assert_called_once_with(monthly)
    causes_renderer.assert_called_once_with(causes)

    mock_streamlit.expander.assert_called_once_with("Comprendre les résultats")


# ---------------------------------------------------------------------
# Comparison dashboard
# ---------------------------------------------------------------------


def test_render_ranking_with_none(mock_streamlit, comparison_selection):
    """Test ranking when data is unavailable."""
    dashboards.render_ranking(None, comparison_selection)

    mock_streamlit.subheader.assert_called_once_with("Classement · Liaisons")
    mock_streamlit.info.assert_called_once_with("Aucunes données disponibles.")
    mock_streamlit.dataframe.assert_not_called()


def test_render_ranking_with_empty_data(mock_streamlit, comparison_selection):
    """Test ranking when no results match the selection."""
    dashboards.render_ranking(pd.DataFrame(), comparison_selection)

    mock_streamlit.info.assert_called_once_with(
        "Aucun résultat ne correspond aux critères sélectionnés."
    )
    mock_streamlit.dataframe.assert_not_called()


def test_render_ranking_with_data(mock_streamlit, comparison_selection):
    """Test ranking with valid results."""
    ranking_data = pd.DataFrame(
        {
            "rank": [1],
            "entity": ["Paris → Lyon"],
            "value": [10],
            "scheduled_train_count": [100],
        }
    )

    dashboards.render_ranking(ranking_data, comparison_selection)

    mock_streamlit.subheader.assert_called_once_with("Classement · Liaisons")
    mock_streamlit.caption.assert_called_once_with(
        "Taux de retard à l’arrivée · 10 résultats maximum · "
        "minimum 100 circulations prévues"
    )
    mock_streamlit.dataframe.assert_called_once_with(
        ranking_data,
        hide_index=True,
        column_config={
            "rank": mock_streamlit.column_config.NumberColumn.return_value,
            "entity": mock_streamlit.column_config.TextColumn.return_value,
            "value": mock_streamlit.column_config.NumberColumn.return_value,
            "scheduled_train_count": (
                mock_streamlit.column_config.NumberColumn.return_value
            ),
        },
    )
    mock_streamlit.column_config.TextColumn.assert_called_once_with(
        "Liaison", width="large"
    )
    mock_streamlit.column_config.NumberColumn.assert_any_call(
        "Taux de retard à l’arrivée (%)", format="%.2f"
    )


def test_render_comparison_time_evolution_with_none(
    mock_streamlit, comparison_selection
):
    """Test comparison evolution when data is unavailable."""
    dashboards.render_comparison_time_evolution(None, comparison_selection)

    mock_streamlit.info.assert_called_once_with("Aucunes données disponibles.")
    mock_streamlit.line_chart.assert_not_called()


def test_render_comparison_time_evolution_with_empty_data(
    mock_streamlit, comparison_selection
):
    """Test comparison evolution with an empty dataframe."""
    dashboards.render_comparison_time_evolution(
        pd.DataFrame(), comparison_selection
    )

    mock_streamlit.info.assert_called_once_with(
        "Aucun historique disponible pour cette comparaison."
    )


@pytest.mark.parametrize(
    ("metric", "expected_unit"),
    [
        ("Retard moyen à l’arrivée", "Minutes"),
        ("Taux de retard", "Taux (%)"),
    ],
)
def test_render_comparison_time_evolution_with_data(
    mock_streamlit,
    comparison_selection,
    metric,
    expected_unit,
):
    """Test comparison chart with valid data."""
    selection = ComparisonSelection(
        entity=comparison_selection.entity,
        metric=metric,
        top_n=comparison_selection.top_n,
        min_volume=comparison_selection.min_volume,
    )

    history = pd.DataFrame(
        {
            "month": [
                pd.Timestamp("2025-01-01"),
                pd.Timestamp("2025-02-01"),
            ],
            "entity": ["Paris → Lyon", "Paris → Lyon"],
            "value": [10.0, 12.0],
        }
    )

    dashboards.render_comparison_time_evolution(history, selection)

    mock_streamlit.line_chart.assert_called_once()

    assert (
        mock_streamlit.line_chart.call_args.kwargs["y_label"] == expected_unit
    )


def test_render_comparison_dashboard_with_empty_ranking(
    mock_streamlit,
    monkeypatch,
    sample_data,
    comparison_selection,
):
    """Test comparison dashboard when ranking is empty."""
    ranking_function = MagicMock(return_value=pd.DataFrame())
    ranking_renderer = MagicMock()
    evolution_renderer = MagicMock()
    comparison_chart = MagicMock()

    monkeypatch.setattr(dashboards, "ranking", ranking_function)
    monkeypatch.setattr(dashboards, "render_ranking", ranking_renderer)
    monkeypatch.setattr(
        dashboards,
        "render_comparison_time_evolution",
        evolution_renderer,
    )
    monkeypatch.setattr(dashboards, "comparison_time_chart", comparison_chart)

    dashboards.render_comparison_dashboard(sample_data, comparison_selection)

    ranking_function.assert_called_once_with(sample_data, comparison_selection)
    ranking_renderer.assert_called_once_with(
        ranking_function.return_value, comparison_selection
    )
    comparison_chart.assert_not_called()
    evolution_renderer.assert_called_once_with(
        ranking_function.return_value, comparison_selection
    )

    mock_streamlit.expander.assert_called_once_with(
        "Comment lire cette comparaison ?"
    )


def test_render_comparison_dashboard_with_ranking(
    mock_streamlit,
    monkeypatch,
    sample_data,
    comparison_selection,
):
    """Test comparison dashboard when ranking contains results."""
    ranking_data = pd.DataFrame(
        {
            "entity": ["Paris → Lyon"],
            "value": [10],
        }
    )
    history = pd.DataFrame({"month": [pd.Timestamp("2025-01-01")]})

    ranking_function = MagicMock(return_value=ranking_data)
    chart_function = MagicMock(return_value=history)
    evolution_renderer = MagicMock()

    monkeypatch.setattr(dashboards, "ranking", ranking_function)
    monkeypatch.setattr(dashboards, "render_ranking", MagicMock())
    monkeypatch.setattr(dashboards, "comparison_time_chart", chart_function)
    monkeypatch.setattr(
        dashboards,
        "render_comparison_time_evolution",
        evolution_renderer,
    )

    dashboards.render_comparison_dashboard(sample_data, comparison_selection)

    chart_function.assert_called_once_with(
        sample_data, comparison_selection, ranking_data
    )
    evolution_renderer.assert_called_once_with(history, comparison_selection)
