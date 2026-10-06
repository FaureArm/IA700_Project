"""
Detail the creation and handling of different
kind of sidebars for
streamlit app.
"""

from pathlib import Path
import pandas as pd
import streamlit as st
from dataclasses import dataclass
from ia700_project.models import FilterSelection


# TODO: find a way to have this values global accross files. Import ?
PLANNED = "Nombre de circulations prévues"
CANCELLED = "Nombre de trains annulés"
DELAY = "Retard moyen de tous les trains à l'arrivée"
DEPARTURE = "Gare de départ"
ARRIVAL = "Gare d'arrivée"
ALL_STATIONS = "Toutes les gares"
TITLE = "Projet IA700"


def date_itinerary_sidebar(df: pd.DataFrame) -> tuple[pd.DataFrame, FilterSelection]:
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
    months = sorted(df["Date"].dt.strftime("%Y-%m").unique().tolist())
    if len(months) > 1:
        start, end = st.sidebar.select_slider(
            "Période", options=months, value=(months[0], months[-1]), key="period"
        )
    else:
        start = end = months[0]
        st.sidebar.caption(f"Période disponible : {start}")
    month_values = df["Date"].dt.strftime(
        "%Y-%m"
    )  # cut days from format since we only have months
    filtered = df.loc[month_values.between(start, end)].copy()

    departure = st.sidebar.selectbox(
        "Gare de départ",
        [ALL_STATIONS] + sorted(filtered[DEPARTURE].unique().tolist()),
        key="departure",
    )
    if departure != ALL_STATIONS:
        filtered = filtered.loc[filtered[DEPARTURE].eq(departure)]
    arrival = st.sidebar.selectbox(
        "Gare d'arrivée",
        [ALL_STATIONS] + sorted(filtered[ARRIVAL].unique().tolist()),
        key="arrival",
    )
    if arrival != ALL_STATIONS:
        filtered = filtered.loc[filtered[ARRIVAL].eq(arrival)]

    if filtered.empty:
        st.info("Aucune donnée disponible pour cette sélection.")
        st.stop()

    filter_selection = FilterSelection(
        start_month=start,
        end_month=end,
        departure=None if departure == ALL_STATIONS else departure,
        arrival=None if arrival == ALL_STATIONS else arrival,
    )

    return filtered, filter_selection
