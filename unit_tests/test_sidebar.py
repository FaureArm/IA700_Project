"""Unit tests for the Streamlit sidebar module."""

from datetime import date

import pandas as pd
import pytest

from ia700_project import sidebar


def test_date_itinerary_sidebar_returns_selection(monkeypatch) -> None:
    """Check that the itinerary sidebar returns the selected values."""
    today = date(2026, 1, 1)

    class FakeDate:
        """Provide a fixed date for the test."""

        @staticmethod
        def today():
            return today

    selections = iter(["PARIS LYON", "LYON PART DIEU"])
    travel_dates = (today, date(2026, 1, 8))

    df = pd.DataFrame(
        {
            "gare_depart": ["PARIS LYON", "LILLE"],
            "gare_arrivee": ["LYON PART DIEU", "PARIS"],
        }
    )

    monkeypatch.setattr(sidebar, "date", FakeDate)
    monkeypatch.setattr(sidebar.st.sidebar, "header", lambda *args: None)
    monkeypatch.setattr(
        sidebar.st.sidebar,
        "selectbox",
        lambda *args, **kwargs: next(selections),
    )
    monkeypatch.setattr(
        sidebar.st.sidebar,
        "date_input",
        lambda *args, **kwargs: travel_dates,
    )

    result = sidebar.date_itinerary_sidebar(df)

    assert result.departure == "PARIS LYON"
    assert result.arrival == "LYON PART DIEU"
    assert result.travel_start == today
    assert result.travel_end == date(2026, 1, 8)


def test_date_itinerary_sidebar_uses_first_stations_when_defaults_missing(
    monkeypatch,
) -> None:
    """Check that the first available stations are used as defaults."""
    today = date(2026, 1, 1)

    class FakeDate:
        """Provide a fixed date for the test."""

        @staticmethod
        def today():
            return today

    selections = iter(["BORDEAUX", "TOULOUSE"])

    df = pd.DataFrame(
        {
            "gare_depart": ["BORDEAUX", "LILLE"],
            "gare_arrivee": ["TOULOUSE", "PARIS"],
        }
    )

    monkeypatch.setattr(sidebar, "date", FakeDate)
    monkeypatch.setattr(sidebar.st.sidebar, "header", lambda *args: None)
    monkeypatch.setattr(
        sidebar.st.sidebar,
        "selectbox",
        lambda *args, **kwargs: next(selections),
    )
    monkeypatch.setattr(
        sidebar.st.sidebar,
        "date_input",
        lambda *args, **kwargs: (today, date(2026, 1, 8)),
    )

    result = sidebar.date_itinerary_sidebar(df)

    assert result.departure == "BORDEAUX"
    assert result.arrival == "TOULOUSE"


def test_date_itinerary_sidebar_stops_when_period_is_incomplete(
    monkeypatch,
) -> None:
    """Check that the sidebar stops if both travel dates are not selected."""
    today = date(2026, 1, 1)

    class FakeDate:
        """Provide a fixed date for the test."""

        @staticmethod
        def today():
            return today

    df = pd.DataFrame(
        {
            "gare_depart": ["PARIS LYON"],
            "gare_arrivee": ["LYON PART DIEU"],
        }
    )

    def stop_execution():
        raise RuntimeError("Streamlit stop")

    monkeypatch.setattr(sidebar, "date", FakeDate)
    monkeypatch.setattr(sidebar.st.sidebar, "header", lambda *args: None)
    monkeypatch.setattr(
        sidebar.st.sidebar,
        "selectbox",
        lambda *args, **kwargs: (
            "PARIS LYON"
            if kwargs.get("key") == "departure"
            else "LYON PART DIEU"
        ),
    )
    monkeypatch.setattr(
        sidebar.st.sidebar,
        "date_input",
        lambda *args, **kwargs: (today,),
    )
    monkeypatch.setattr(sidebar.st, "stop", stop_execution)

    with pytest.raises(RuntimeError, match="Streamlit stop"):
        sidebar.date_itinerary_sidebar(df)


def test_map_route_sidebar_returns_selected_route(monkeypatch) -> None:
    """Check that the map route selector returns the selected route ID."""
    routes = {
        "route_1": "PARIS LYON → LYON PART DIEU",
        "route_2": "LILLE → PARIS",
    }

    captured = {}

    def fake_selectbox(label, options, **kwargs):
        captured["label"] = label
        captured["options"] = options
        captured.update(kwargs)
        return "route_1"

    monkeypatch.setattr(
        sidebar.st.sidebar,
        "selectbox",
        fake_selectbox,
    )

    result = sidebar.map_route_sidebar(routes)

    assert result == "route_1"
    assert captured["label"] == "Liaison sur la carte"
    assert captured["options"] == routes
    assert captured["index"] is None
    assert captured["format_func"]("route_1") == routes["route_1"]


def test_map_metric_sidebar_returns_selected_metric(monkeypatch) -> None:
    """Check that the map metric selector returns the selected metric key."""
    metrics = {
        "disruption": "Perturbations",
        "delay": "Retards à l’arrivée",
        "cancellation": "Annulations",
    }

    captured = {}

    def fake_radio(label, options, **kwargs):
        captured["label"] = label
        captured["options"] = options
        captured.update(kwargs)
        return "delay"

    monkeypatch.setattr(sidebar.st.sidebar, "radio", fake_radio)

    result = sidebar.map_metric_sidebar(metrics)

    assert result == "delay"
    assert captured["label"] == "Indicateur de la carte"
    assert captured["options"] == list(metrics)
    assert captured["format_func"]("delay") == "Retards à l’arrivée"


def test_comparison_sidebar_returns_selection(monkeypatch) -> None:
    """Check that the comparison sidebar returns all selected options."""
    selections = iter(
        [
            "Liaisons",
            "Taux d’annulation",
            10,
            100,
        ]
    )

    monkeypatch.setattr(sidebar.st.sidebar, "header", lambda *args: None)
    monkeypatch.setattr(
        sidebar.st.sidebar,
        "selectbox",
        lambda *args, **kwargs: next(selections),
    )
    monkeypatch.setattr(
        sidebar.st.sidebar,
        "caption",
        lambda *args: None,
    )

    result = sidebar.comparison_sidebar()

    assert result.entity == "Liaisons"
    assert result.metric == "Taux d’annulation"
    assert result.top_n == 10
    assert result.min_volume == 100
