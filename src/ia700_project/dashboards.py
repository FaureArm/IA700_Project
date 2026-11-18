"""Create dashboards to be displayed by our Streamlit app."""

import pandas as pd
import streamlit as st

from ia700_project.map_view import render_tgv_map
from ia700_project.models import ComparisonSelection, TravelSelection


def render_exploration_dashboard(selection: TravelSelection) -> None:
    """Display the travel summary and historical analysis placeholders."""
    render_travel_summary(selection)

    st.info(
        "=> Ici, on affiche les résultats historiques de la sélection. "
        "Pas une prédiction : on présente les retards moyens et les taux "
        "d'annulation observés aux mêmes périodes les années précédentes. "
        "On pourrait éventuellement regrouper les résultats par mois."
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
    """Display the ranking for the selected comparison."""
    st.subheader(f"Classement · {selection.entity}")
    st.caption(
        f"{selection.metric} · {selection.top_n} résultats maximum · "
        f"minimum {selection.min_volume} circulations prévues"
    )
    st.info(
        "Afficher ici le classement et les volumes associés "
        "à la recherche du sidebar."
    )


def render_comparison_time_evolution(
    selection: ComparisonSelection,
) -> None:
    """Display the time evolution of the selected comparison."""
    st.subheader("Comparer les évolutions")
    st.info(
        "Ici, montrer une évolution temporelle des variables sélectionnées. "
        "Faut-il afficher tous les candidats ou seulement ceux du top ? "
        "Faut-il prendre en compte le volume minimal de circulations ?"
    )


def render_travel_summary(selection: TravelSelection) -> None:
    """Display the selected journey and its travel dates."""
    st.subheader(f"{selection.departure} → {selection.arrival}")
    st.write(
        f"Voyage du {selection.travel_start:%d/%m/%Y} "
        f"au {selection.travel_end:%d/%m/%Y}"
    )


def render_summary_metrics() -> None:
    """Display the historical summary metrics."""
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
    """Display the historical evolution of delays and cancellations."""
    st.subheader("Évolution dans le temps")
    st.info("Afficher les graphiques d'évolution des retards et annulations.")


def render_delay_causes() -> None:
    """Display the distribution of delay causes."""
    st.subheader("Causes des retards")
    st.info(
        "Afficher la répartition des causes en grandes catégories, "
        "selon les informations disponibles."
    )


def render_comparison_dashboard(selection: ComparisonSelection) -> None:
    """Display the ranking and time evolution of a comparison."""
    render_ranking(selection)
    render_comparison_time_evolution(selection)

    with st.expander("Comment lire cette comparaison ?"):
        st.write("blablabla petite description pour faire jolie")


def render_overview_metrics(df: pd.DataFrame | None = None) -> None:
    """Display basic dashboard metrics.

    The metrics are displayed through three columns.

    Args:
        df: Optional DataFrame containing the data used to compute
            the dashboard metrics.
    """
    liaisons_col, stations_col, latest_month_col = st.columns(3)
    if df is None or df.empty:
        liaison_count, station_count, latest_month = "-", "-", "-"
    else:
        liaison_count, station_count, latest_month = (
            0,
            0,
            0,
        )  # TODO: Compute these metrics from df in a reusable function.

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
    """Display the overview dashboard components."""
    df = None
    render_overview_metrics(df)
    render_network_map()
