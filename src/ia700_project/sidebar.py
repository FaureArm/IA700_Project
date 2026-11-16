"""
Detail the creation and handling of different
kind of sidebars for
streamlit app.
"""

import pandas as pd
import streamlit as st
from datetime import date, timedelta

from ia700_project.models import TravelSelection

# TODO: find a way to have this values global accross files. Import ?
PLANNED = "Nombre de circulations prévues"
CANCELLED = "Nombre de trains annulés"
DELAY = "Retard moyen de tous les trains à l'arrivée"
DEPARTURE = "Gare de départ"
ARRIVAL = "Gare d'arrivée"
ALL_STATIONS = "Toutes les gares"
TITLE = "Projet IA700"


def date_itinerary_sidebar(df: pd.DataFrame) -> tuple[pd.DataFrame, TravelSelection]:
    """Render sidebar controls and filter train data by month and itinerary.

    Args:
        df: Nonempty train dataset with a datetime-like "Date" column
            and departure and arrival station columns.

    Returns:
        A tuple containing the filtered dataset and the selected filters.
        Month boundaries are inclusive. A station value of None in the
        filter selection means all stations are included.

    Notes:
        Displays a message and stops Streamlit execution if no rows
        match the selection.
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

    filtered = filtered.loc[filtered[ARRIVAL].eq(arrival)]

    selection = TravelSelection(
        departure=departure,
        arrival=arrival,
        travel_start=travel_start,
        travel_end=travel_end,
    )

    return filtered, selection
