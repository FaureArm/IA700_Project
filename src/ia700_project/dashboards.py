"""Create dashboards to be displayed by our steamlit app.
"""

import pandas as pd
import streamlit as st

from ia700_project.map_view import render_tgv_map
from ia700_project.models import ComparisonSelection, TravelSelection


def render_exploration_dashboard(selection: TravelSelection) -> None:
    """Display the travel summary and historical analysis placeholders"""
    render_travel_summary(selection)

    st.info(
        "=> ici on affiche les résultats historiques de la selection. Pas une prédiction, juste"
        "dire que ba à cette période la des années précédentes, on a eu tel retard moyen et tel taux d'annulation"
        "On peut probablement juste faire par mois au final"
    )

    render_summary_metrics()

    left, right = st.columns(2)

    with left:
        render_exploration_time_evolution()

    with right:
        render_delay_causes()

    with st.expander("Comprendre les résultats"):
        st.write("blablabla petite description pour faire jolie")


def render_ranking(selection: ComparisonSelection) -> None:
    st.subheader(f"Classement · {selection.entity}")
    st.caption(
        f"{selection.metric} · {selection.top_n} résultats maximum · "
        f"minimum {selection.min_volume} circulations prévues"
    )
    st.info(
        "Afficher ici le classement et les volumes associés à la recherche du sidebar"
    )


def render_comparison_time_evolution(selection: ComparisonSelection) -> None:
    st.subheader("Comparer les évolutions")
    st.info(
        " Ici, montrer une évolution temporelle de nos variables séléctionnées "
        " montrer évolution pour tous les candidats du top ? eg si on choisit le nbre de résultats"
        "valant 10, seuelement 10 sur graphes? ou tous? prendre en compte nombre minimal de vilume?"
    )


def render_travel_summary(selection: TravelSelection) -> None:
    st.subheader(f"{selection.departure} → {selection.arrival}")
    st.write(
        f"Voyage du {selection.travel_start:%d/%m/%Y} "
        f"au {selection.travel_end:%d/%m/%Y}"
    )


def render_summary_metrics() -> None:
    st.subheader("Que montre l’historique ?")

    volume, cancellations, delays, duration = st.columns(4)
    volume.metric("Circulations étudiées", "—")
    cancellations.metric("Taux d’annulation", "—")
    delays.metric("Taux de retard à l’arrivée", "—")
    duration.metric("Retard moyen à l’arrivée", "—")

    st.caption(
        "TODO: indicateurs à calculer "
        "-> décrire les observations historiques de cette liaison"
    )


def render_exploration_time_evolution() -> None:
    st.subheader("Évolution dans le temps")
    st.info("afficher graphs d'évolutions de retard et annulation")


def render_delay_causes() -> None:
    st.subheader("Causes des retards")
    st.info(
        "Afficher répartition des causes, grosses catégories ou qqchose vu qu'on a pas bcp d'infos"
    )


def render_comparison_dashboard(selection: ComparisonSelection) -> None:
    render_ranking(selection)
    render_comparison_time_evolution(selection)

    with st.expander("Comment lire cette comparaison ?"):
        st.write("blablabla petite description pour faire jolie")


def render_overview_metrics(df: pd.DataFrame | None = None) -> None:
    """Small dashboard showing basic metrics
    through three columns.
    NB: we spam try excepts, not very elegant but foolproof i suppose

    Args:
        liaison_count (int): _description_
        station_count (int): _description_
        latest_month (str): _description_
    """
    liaisons_col, stations_col, latest_month_col = st.columns(3)
    if df is None or df.empty:
        liaison_count, station_count, latest_month = "-", "-", "-"
    else:
        liaison_count, station_count, latest_month = (
            0,
            0,
            0,
        )  # TODO: compute these metrics from df, maybe in a separate function to be reused in the sidebar?

    liaisons_col, stations_col, latest_month_col = st.columns(3)
    try:
        liaisons_col.metric("Liaisons couvertes", liaison_count)
    except TypeError:
        liaisons_col.metric("Liaisons couvertes", "—")
    try:
        stations_col.metric("Gares représentées", station_count)
    except TypeError:
        stations_col.metric("Gares représentées", "—")
    try:
        latest_month_col.metric("Dernier mois disponible", latest_month)
    except TypeError:
        latest_month_col.metric("Dernier mois disponible", "—")


def render_network_map() -> None:
    """Add the network heading and interactive map to the overview."""
    st.subheader("Le réseau en un regard")
    render_tgv_map()


def render_overview_dashboard() -> None:
    """Acts as a global entry point for different
    components to be shown on the main page
    """
    df = None
    render_overview_metrics(
        df
    )  # to render some generic values on top, could be switched to a sidebar, or smth else perhaps idk?
    render_network_map()  # to render the map with overlay
