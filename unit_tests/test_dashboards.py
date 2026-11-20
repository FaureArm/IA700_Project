"""Unit tests for the Streamlit dashboards."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import pytest

from ia700_project import dashboards


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Mock Streamlit and keep track of the columns returned."""
    mock_st = MagicMock()
    columns_by_count = {}

    def make_columns(count, **kwargs):
        columns = [MagicMock() for _ in range(count)]
        columns_by_count[count] = columns
        return columns

    mock_st.columns.side_effect = make_columns
    mock_st._columns_by_count = columns_by_count

    monkeypatch.setattr(dashboards, "st", mock_st)
    return mock_st


@pytest.fixture
def sample_data():
    """Return a small sample DataFrame."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-02-01"]),
            "gare_depart": ["Paris", "Lyon"],
            "gare_arrivee": ["Lyon", "Paris"],
        }
    )


@pytest.fixture
def travel_selection():
    """Return a travel selection compatible with the dashboard."""
    return SimpleNamespace(
        departure="Paris",
        arrival="Lyon",
        travel_start=pd.Timestamp("2025-01-01"),
        travel_end=pd.Timestamp("2025-01-15"),
    )


@pytest.fixture
def comparison_selection():
    """Return a comparison selection compatible with the dashboard."""
    return SimpleNamespace(
        entity="Liaisons",
        metric="Taux de retard à l’arrivée",
        top_n=5,
        min_volume=100,
    )


# ---------------------------------------------------------------------
# Overview dashboard
# ---------------------------------------------------------------------


def test_render_overview_dashboard(mock_streamlit, monkeypatch, sample_data):
    """Test the overview dashboard rendering and function calls."""
    summary = pd.DataFrame({"route_count": [10], "station_count": [20]})
    compute = MagicMock(return_value=summary)
    metrics = MagicMock()
    network_map = MagicMock()

    monkeypatch.setattr(dashboards, "compute_overview_summary", compute)
    monkeypatch.setattr(dashboards, "render_overview_metrics", metrics)
    monkeypatch.setattr(dashboards, "render_network_map", network_map)

    dashboards.render_overview_dashboard(sample_data)

    compute.assert_called_once_with(sample_data)
    metrics.assert_called_once_with(summary)
    network_map.assert_called_once_with(sample_data)


def test_render_network_map(mock_streamlit, monkeypatch, sample_data):
    """Test the network map rendering."""
    map_mock = MagicMock()
    monkeypatch.setattr(dashboards, "render_tgv_map", map_mock)

    dashboards.render_network_map(sample_data)

    mock_streamlit.subheader.assert_called_once_with("Le réseau en un regard")
    map_mock.assert_called_once_with(sample_data)


def test_render_overview_metrics_with_data(mock_streamlit):
    """Test overview metrics when valid data is available."""
    summary = pd.DataFrame({"route_count": [1234], "station_count": [5678]})

    dashboards.render_overview_metrics(summary)

    routes, stations = mock_streamlit._columns_by_count[2]

    routes.metric.assert_called_once_with("Liaisons couvertes", "1 234")
    stations.metric.assert_called_once_with("Gares représentées", "5 678")


@pytest.mark.parametrize("summary", [None, pd.DataFrame()])
def test_render_overview_metrics_without_data(mock_streamlit, summary):
    """Test overview metrics when data is missing or empty."""
    dashboards.render_overview_metrics(summary)

    mock_streamlit.caption.assert_called_once_with(
        "Aucune donnée exploitable pour les indicateurs du réseau."
    )

    routes, stations = mock_streamlit._columns_by_count[2]

    routes.metric.assert_called_once_with("Liaisons couvertes", "—")
    stations.metric.assert_called_once_with("Gares représentées", "—")


# ---------------------------------------------------------------------
# Exploration dashboard
# ---------------------------------------------------------------------


def test_render_exploration_dashboard(
    mock_streamlit, monkeypatch, sample_data, travel_selection
):
    """Test the exploration dashboard rendering and function calls."""
    travel_summary = MagicMock()
    summary_metrics = MagicMock()
    time_chart = MagicMock(return_value=pd.DataFrame({"month": []}))
    causes = MagicMock(return_value=pd.DataFrame({"cause": []}))
    time_evolution = MagicMock()
    delay_causes = MagicMock()

    monkeypatch.setattr(dashboards, "render_travel_summary", travel_summary)
    monkeypatch.setattr(dashboards, "render_summary_metrics", summary_metrics)
    monkeypatch.setattr(dashboards, "time_chart", time_chart)
    monkeypatch.setattr(dashboards, "cause_of_delays_ranking", causes)
    monkeypatch.setattr(
        dashboards, "render_exploration_time_evolution", time_evolution
    )
    monkeypatch.setattr(dashboards, "render_delay_causes", delay_causes)

    dashboards.render_exploration_dashboard(sample_data, travel_selection)

    travel_summary.assert_called_once_with(travel_selection)
    summary_metrics.assert_called_once_with(sample_data, travel_selection)
    time_chart.assert_called_once_with(sample_data, travel_selection)
    causes.assert_called_once_with(sample_data, travel_selection)
    time_evolution.assert_called_once()
    delay_causes.assert_called_once()
    mock_streamlit.expander.assert_called_once_with("Comprendre les résultats")


def test_render_travel_summary(mock_streamlit, travel_selection):
    """Test the display of the selected travel summary."""
    dashboards.render_travel_summary(travel_selection)

    mock_streamlit.subheader.assert_called_once_with("Paris → Lyon")
    mock_streamlit.write.assert_called_once_with(
        "Voyage du 01/01/2025 au 15/01/2025"
    )


def test_render_summary_metrics(
    mock_streamlit, monkeypatch, sample_data, travel_selection
):
    """Test summary metrics when all indicator values are available."""
    monkeypatch.setattr(
        dashboards, "scheduled_trains_count", MagicMock(return_value=1000)
    )
    monkeypatch.setattr(
        dashboards, "cancellation_rate", MagicMock(return_value=2.5)
    )
    monkeypatch.setattr(
        dashboards, "delay_rate", MagicMock(return_value=12.75)
    )
    monkeypatch.setattr(
        dashboards, "avg_delay_length", MagicMock(return_value=8.5)
    )

    dashboards.render_summary_metrics(sample_data, travel_selection)

    volume, cancellations, delays, duration = mock_streamlit._columns_by_count[
        4
    ]

    volume.metric.assert_called_once_with("Circulations prévues", "1 000")
    cancellations.metric.assert_called_once_with("Taux d’annulation", "2.50 %")
    delays.metric.assert_called_once_with(
        "Taux de retard à l’arrivée", "12.75 %"
    )
    duration.metric.assert_called_once_with(
        "Retard moyen à l’arrivée", "8.5 min"
    )


def test_render_summary_metrics_with_missing_values(
    mock_streamlit, monkeypatch, sample_data, travel_selection
):
    """Test summary metrics when indicator values are missing."""
    monkeypatch.setattr(
        dashboards,
        "scheduled_trains_count",
        MagicMock(return_value=float("nan")),
    )
    monkeypatch.setattr(
        dashboards, "cancellation_rate", MagicMock(return_value=float("nan"))
    )
    monkeypatch.setattr(
        dashboards, "delay_rate", MagicMock(return_value=float("nan"))
    )
    monkeypatch.setattr(
        dashboards, "avg_delay_length", MagicMock(return_value=float("nan"))
    )

    dashboards.render_summary_metrics(sample_data, travel_selection)

    volume, cancellations, delays, duration = mock_streamlit._columns_by_count[
        4
    ]

    volume.metric.assert_called_once_with(
        "Circulations prévues", "Indisponible"
    )
    cancellations.metric.assert_called_once_with(
        "Taux d’annulation", "Indisponible"
    )
    delays.metric.assert_called_once_with(
        "Taux de retard à l’arrivée", "Indisponible"
    )
    duration.metric.assert_called_once_with(
        "Retard moyen à l’arrivée", "Indisponible"
    )


def test_render_exploration_time_evolution_without_data(mock_streamlit):
    """Test the time evolution display when history is unavailable."""
    dashboards.render_exploration_time_evolution(None)

    mock_streamlit.subheader.assert_called_once_with("Évolution dans le temps")
    mock_streamlit.info.assert_called_once_with(
        "Aucun historique mensuel disponible pour cette liaison."
    )
    mock_streamlit.line_chart.assert_not_called()


def test_render_exploration_time_evolution_with_empty_data(
    mock_streamlit,
):
    """Test the time evolution display when history is empty."""
    dashboards.render_exploration_time_evolution(pd.DataFrame())

    mock_streamlit.info.assert_called_once_with(
        "Aucun historique mensuel disponible pour cette liaison."
    )
    mock_streamlit.line_chart.assert_not_called()


def test_render_exploration_time_evolution_with_data(mock_streamlit):
    """Test the time evolution charts with valid monthly history."""
    history = pd.DataFrame(
        {
            "month": pd.to_datetime(["2025-02-01", "2025-01-01"]),
            "cancellation_rate_pct": [2.0, 1.0],
            "arrival_delay_rate_pct": [10.0, 8.0],
            "mean_arrival_delay_minutes": [7.0, 6.0],
        }
    )

    dashboards.render_exploration_time_evolution(history)

    assert mock_streamlit.line_chart.call_count == 2


def test_render_delay_causes_without_data(mock_streamlit):
    """Test the delay causes display when data is unavailable."""
    dashboards.render_delay_causes(None)

    mock_streamlit.subheader.assert_called_once_with("Causes des retards")
    mock_streamlit.info.assert_called_once_with(
        "Aucune répartition des causes disponible."
    )
    mock_streamlit.dataframe.assert_not_called()


def test_render_delay_causes_with_empty_data(mock_streamlit):
    """Test the delay causes display when the DataFrame is empty."""
    dashboards.render_delay_causes(pd.DataFrame())

    mock_streamlit.info.assert_called_once_with(
        "Aucune répartition des causes disponible."
    )
    mock_streamlit.dataframe.assert_not_called()


def test_render_delay_causes_with_data(mock_streamlit):
    """Test the delay causes table with valid data."""
    causes = pd.DataFrame(
        {
            "cause": ["Infrastructure", "Matériel"],
            "percentage": [60.0, 40.0],
        }
    )

    dashboards.render_delay_causes(causes)

    mock_streamlit.dataframe.assert_called_once()
    args, kwargs = mock_streamlit.dataframe.call_args

    pd.testing.assert_frame_equal(args[0], causes)
    assert kwargs["hide_index"] is True
    assert "cause" in kwargs["column_config"]
    assert "percentage" in kwargs["column_config"]


# ---------------------------------------------------------------------
# Comparison dashboard
# ---------------------------------------------------------------------


def test_render_comparison_dashboard(
    mock_streamlit, monkeypatch, sample_data, comparison_selection
):
    """Test the comparison dashboard rendering and function calls."""
    ranking_data = pd.DataFrame({"entity": ["Paris → Lyon"], "value": [12.0]})
    monthly_history = pd.DataFrame(
        {
            "month": pd.to_datetime(["2025-01-01"]),
            "entity": ["Paris → Lyon"],
            "value": [12.0],
        }
    )

    ranking_mock = MagicMock(return_value=ranking_data)
    ranking_renderer = MagicMock()
    comparison_chart = MagicMock(return_value=monthly_history)
    evolution_renderer = MagicMock()

    monkeypatch.setattr(dashboards, "ranking", ranking_mock)
    monkeypatch.setattr(dashboards, "render_ranking", ranking_renderer)
    monkeypatch.setattr(dashboards, "comparison_time_chart", comparison_chart)
    monkeypatch.setattr(
        dashboards,
        "render_comparison_time_evolution",
        evolution_renderer,
    )

    dashboards.render_comparison_dashboard(sample_data, comparison_selection)

    ranking_mock.assert_called_once_with(sample_data, comparison_selection)
    ranking_renderer.assert_called_once_with(
        ranking_data, comparison_selection
    )
    comparison_chart.assert_called_once_with(
        sample_data, comparison_selection, ranking_data
    )
    evolution_renderer.assert_called_once_with(
        monthly_history, comparison_selection
    )


@pytest.mark.parametrize(
    "ranking_data",
    [None, pd.DataFrame()],
)
def test_render_comparison_dashboard_without_ranking(
    mock_streamlit,
    monkeypatch,
    sample_data,
    comparison_selection,
    ranking_data,
):
    """Test comparison dashboard behavior when ranking data is unavailable."""
    monkeypatch.setattr(
        dashboards, "ranking", MagicMock(return_value=ranking_data)
    )
    ranking_renderer = MagicMock()
    chart = MagicMock()
    evolution = MagicMock()

    monkeypatch.setattr(dashboards, "render_ranking", ranking_renderer)
    monkeypatch.setattr(dashboards, "comparison_time_chart", chart)
    monkeypatch.setattr(
        dashboards, "render_comparison_time_evolution", evolution
    )

    dashboards.render_comparison_dashboard(sample_data, comparison_selection)

    ranking_renderer.assert_called_once_with(
        ranking_data, comparison_selection
    )
    chart.assert_not_called()
    evolution.assert_called_once_with(ranking_data, comparison_selection)


def test_render_ranking_with_none(mock_streamlit, comparison_selection):
    """Test the ranking display when ranking data is None."""
    dashboards.render_ranking(None, comparison_selection)

    mock_streamlit.subheader.assert_called_once_with("Classement · Liaisons")
    mock_streamlit.info.assert_called_once_with("Aucunes données disponibles.")
    mock_streamlit.dataframe.assert_not_called()


def test_render_ranking_with_empty_data(mock_streamlit, comparison_selection):
    """Test the ranking display when ranking data is empty."""
    dashboards.render_ranking(pd.DataFrame(), comparison_selection)

    mock_streamlit.info.assert_called_once_with(
        "Aucun résultat ne correspond aux critères sélectionnés."
    )
    mock_streamlit.dataframe.assert_not_called()


@pytest.mark.parametrize(
    ("metric", "expected_unit", "expected_format"),
    [
        ("Taux de retard à l’arrivée", "%", "%.2f"),
        ("Retard moyen à l’arrivée", "min", "%.1f"),
    ],
)
def test_render_ranking_with_data(
    mock_streamlit,
    comparison_selection,
    metric,
    expected_unit,
    expected_format,
):
    """Test ranking rendering for the supported metric types."""
    comparison_selection.metric = metric
    ranking_data = pd.DataFrame(
        {
            "rank": [1],
            "entity": ["Paris → Lyon"],
            "value": [12.5],
            "scheduled_train_count": [1000],
        }
    )

    dashboards.render_ranking(ranking_data, comparison_selection)

    mock_streamlit.dataframe.assert_called_once()
    _, kwargs = mock_streamlit.dataframe.call_args

    assert kwargs["hide_index"] is True
    assert set(kwargs["column_config"]) == {
        "rank",
        "entity",
        "value",
        "scheduled_train_count",
    }

    number_column = mock_streamlit.column_config.NumberColumn
    number_column.assert_any_call("Rang", format="%d")
    number_column.assert_any_call(
        f"{metric} ({expected_unit})",
        format=expected_format,
    )


@pytest.mark.parametrize(
    ("entity", "expected_label"),
    [
        ("Liaisons", "Liaison"),
        ("Gares de départ", "Gare de départ"),
        ("Gares d’arrivée", "Gare d’arrivée"),
    ],
)
def test_render_ranking_entity_labels(
    mock_streamlit, comparison_selection, entity, expected_label
):
    """Test entity labels for the different ranking categories."""
    comparison_selection.entity = entity
    ranking_data = pd.DataFrame(
        {
            "rank": [1],
            "entity": ["Paris"],
            "value": [10.0],
            "scheduled_train_count": [100],
        }
    )

    dashboards.render_ranking(ranking_data, comparison_selection)

    mock_streamlit.column_config.TextColumn.assert_called_once_with(
        expected_label,
        width="large",
    )


def test_render_comparison_time_evolution_with_none(
    mock_streamlit, comparison_selection
):
    """Test comparison time evolution when history is None."""
    dashboards.render_comparison_time_evolution(None, comparison_selection)

    mock_streamlit.info.assert_called_once_with("Aucunes données disponibles.")
    mock_streamlit.line_chart.assert_not_called()


def test_render_comparison_time_evolution_with_empty_data(
    mock_streamlit, comparison_selection
):
    """Test comparison time evolution when history is empty."""
    dashboards.render_comparison_time_evolution(
        pd.DataFrame(), comparison_selection
    )

    mock_streamlit.info.assert_called_once_with(
        "Aucun historique disponible pour cette comparaison."
    )
    mock_streamlit.line_chart.assert_not_called()


@pytest.mark.parametrize(
    ("metric", "expected_label"),
    [
        ("Taux de retard à l’arrivée", "Taux (%)"),
        ("Retard moyen à l’arrivée", "Minutes"),
    ],
)
def test_render_comparison_time_evolution_with_data(
    mock_streamlit, comparison_selection, metric, expected_label
):
    """Test comparison time evolution for the supported metric types."""
    comparison_selection.metric = metric
    history = pd.DataFrame(
        {
            "month": pd.to_datetime(
                ["2025-01-01", "2025-01-01", "2025-02-01"]
            ),
            "entity": ["Paris → Lyon", "Lyon → Paris", "Paris → Lyon"],
            "value": [10.0, 12.0, 8.0],
        }
    )

    dashboards.render_comparison_time_evolution(history, comparison_selection)

    mock_streamlit.line_chart.assert_called_once()
    _, kwargs = mock_streamlit.line_chart.call_args
    assert kwargs["x_label"] == "Mois"
    assert kwargs["y_label"] == expected_label


# ---------------------------------------------------------------------
# Methods dashboard
# ---------------------------------------------------------------------


def test_render_data_source_dashboard(mock_streamlit):
    """Test the data source dashboard rendering."""
    dashboards.render_data_source_dashboard()

    mock_streamlit.subheader.assert_called_once_with(
        "1. Comprendre les données"
    )
    assert mock_streamlit.markdown.call_count == 2
    mock_streamlit.dataframe.assert_called_once()


def test_render_cleaning_dashboard(mock_streamlit, monkeypatch):
    """Test the cleaning dashboard rendering."""
    example_renderer = MagicMock()
    monkeypatch.setattr(
        dashboards, "render_cleaning_example", example_renderer
    )

    dashboards.render_cleaning_dashboard()

    mock_streamlit.subheader.assert_called_once_with(
        "2. Préparer sans inventer d’information"
    )
    mock_streamlit.dataframe.assert_called_once()
    example_renderer.assert_called_once()


def test_render_cleaning_example_structure(mock_streamlit, monkeypatch):
    """Test the structure and date cleaning example."""
    before = pd.DataFrame(
        {
            "date": ["2025-01"],
            "commentaire_annulation": [None],
            "commentaire_retards_depart": [None],
            "commentaires_retard_arrivee": ["Incident"],
        }
    )

    monkeypatch.setattr(
        dashboards,
        "build_cleaning_examples",
        MagicMock(return_value={"Structure et dates": before}),
    )
    monkeypatch.setattr(dashboards, "convert_dates", lambda frame: frame)
    monkeypatch.setattr(dashboards, "drop_empty_columns", lambda frame: frame)
    mock_streamlit.selectbox.return_value = "Structure et dates"

    dashboards.render_cleaning_example()

    mock_streamlit.selectbox.assert_called_once()
    assert mock_streamlit.dataframe.call_count == 2


def test_render_quality_dashboard(mock_streamlit):
    """Test the quality dashboard rendering."""
    dashboards.render_quality_dashboard()

    mock_streamlit.subheader.assert_called_once_with(
        "3. Contrôler la cohérence, décider au cas par cas"
    )
    assert mock_streamlit.expander.call_count == 6
    mock_streamlit.dataframe.assert_called_once()


def test_render_methodology_dashboard(mock_streamlit):
    """Test the methodology dashboard rendering."""
    dashboards.render_methodology_dashboard()

    mock_streamlit.subheader.assert_called_once_with(
        "4. Lire les indicateurs avec les bons repères"
    )
    assert mock_streamlit.expander.call_count == 3
    mock_streamlit.markdown.assert_called()
    mock_streamlit.write.assert_called()
