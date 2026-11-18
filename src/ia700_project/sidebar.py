"""
Detail the creation and handling of different
kind of sidebars for
streamlit app.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from ia700_project.constants import (
    ARRIVAL,
    CANCELLED,
    DELAY,
    DEPARTURE,
    PLANNED,
)
from ia700_project.models import ComparisonSelection, TravelSelection


def date_itinerary_sidebar(df: pd.DataFrame) -> TravelSelection:
    """Render route and travel-date controls and return the selection

    Args:
        df: Nonempty dataset containing departure and arrival stations

    Returns:
        Selected stations and travel dates
    """
    st.sidebar.header("Votre sélection")

    # select departure and arrival stations ##

    # we have a default selection, but otherwise we just
    # use first in our lists
    departures = sorted(df[DEPARTURE].unique().tolist())
    default_departure = "PARIS LYON"

    departure = st.sidebar.selectbox(
        "Gare de départ",
        departures,
        index=(
            departures.index(default_departure)
            if default_departure in departures
            else 0
        ),
        key="departure",
    )

    filtered = df.loc[df[DEPARTURE].eq(departure)]

    arrivals = sorted(filtered[ARRIVAL].unique().tolist())
    default_arrival = "LYON PART DIEU"

    arrival = st.sidebar.selectbox(
        "Gare d'arrivée",
        arrivals,
        index=(
            arrivals.index(default_arrival)
            if default_arrival in arrivals
            else 0
        ),
        key="arrival",
    )

    ## Date selection ##
    # calendar based to mimic traveling dates

    today = date.today()

    travel_dates = st.sidebar.date_input(
        "Dates de voyage",
        value=(today, today + timedelta(days=7)),
        min_value=today,
        format="DD/MM/YYYY",
        key="travel_dates",
    )

    if len(travel_dates) != 2:
        st.sidebar.info("Sélectionnez le début et la fin de votre période.")
        st.stop()

    travel_start, travel_end = travel_dates

    selection = TravelSelection(
        departure=departure,
        arrival=arrival,
        travel_start=travel_start,
        travel_end=travel_end,
    )

    return selection


def map_route_sidebar(routes: dict[str, str]) -> str | None:
    """Return the selected route ID, else None to show all liaisons"""
    return st.sidebar.selectbox(
        "Liaison sur la carte",
        routes,
        index=None,
        format_func=routes.__getitem__,
        placeholder="Toutes les liaisons",
        key="map_route",
    )


def map_metric_sidebar(metrics: dict[str, str]) -> str:
    """Return the metric key used to colour the overview map"""
    return st.sidebar.radio(
        "Indicateur de la carte",
        list(metrics),
        format_func=metrics.__getitem__,
        key="map_metric",
    )


def comparison_sidebar() -> ComparisonSelection:
    """Render comparison selected metrics and return the selected options"""
    st.sidebar.header("Votre comparaison")
    
    entity = st.sidebar.selectbox(
        "Que souhaitez-vous comparer ?",
        ["Liaisons", "Gares de départ", "Gares d’arrivée"],
        key="comparison_entity",
    )

    metric = st.sidebar.selectbox(
        "Indicateur",
        [
            "Taux d’annulation",
            "Taux de retard à l’arrivée",
            "Retard moyen à l’arrivée",
        ],
        key="comparison_metric",
    )

    top_n = st.sidebar.selectbox(
        "Nombre de résultats",
        [5, 10, 20],
        index=1,
        key="comparison_top_n",
    )

    min_volume = st.sidebar.selectbox(
        "Minimum de circulations prévues sur la période",
        [0, 50, 100, 500],
        index=2,
        key="comparison_min_volume",
    )

    st.sidebar.caption(
        "Ce seuil permettra d’écarter les résultats "
        "reposant sur un faible nombre de circulations"
    )

    return ComparisonSelection(
        entity=entity,
        metric=metric,
        top_n=top_n,
        min_volume=min_volume,
    )







