"""Create dashboards to be displayed by our steamlit app.
"""

import pandas as pd
import streamlit as st

from ia700_project.map_view import render_tgv_map
from ia700_project.models import ComparisonSelection, TravelSelection
from ia700_project.indicators import (
    compute_overview_summary,
    scheduled_trains_count,
    cancellation_rate,
    delay_rate,
    avg_delay_length,
    time_chart,
    cause_of_delays_ranking,
)

### MAIN PAGE ###


def render_overview_dashboard(data: pd.DataFrame) -> None:
    """Acts as a global entry point for different
    components to be shown on the main page
    """
    #st.caption(f"Vérification · {len(data):,} observations reçues.")
    overview_summary = compute_overview_summary(data)
    render_overview_metrics(overview_summary)  # to render some generic values on top, could be switched to a sidebar, or smth else perhaps idk?
    render_network_map()  # to render the map with overlay

def render_network_map() -> None:
    """Add the network heading and interactive map to the overview."""
    st.subheader("Le réseau en un regard")
    render_tgv_map()

def render_overview_metrics(overview_summary: pd.DataFrame | None) -> None:
    """Display the dataset overview returned by the calculation."""
    route_count_label = "—"
    station_count_label = "—"
    latest_month_label = "—"

    if overview_summary is None:
        st.caption("Aucune donnée exploitable pour les indicateurs du réseau.")
    elif overview_summary.empty:
        st.caption("Aucune donnée exploitable pour les indicateurs du réseau.")
    else:
        summary = overview_summary.iloc[0]

        route_count_label = (
            f"{int(summary['route_count']):,}".replace(",", " ")
        )
        station_count_label = (
            f"{int(summary['station_count']):,}".replace(",", " ")
        )

        if pd.notna(summary["latest_month"]):
            latest_month_label = pd.Timestamp(
                summary["latest_month"]
            ).strftime("%m/%Y")

    routes_column, stations_column, latest_month_column = st.columns(3)

    routes_column.metric("Liaisons couvertes", route_count_label)
    stations_column.metric("Gares représentées", station_count_label)

### EXPLORATION PAGE ###

def render_exploration_dashboard(
    data: pd.DataFrame, selection: TravelSelection
) -> None:
    render_travel_summary(selection)
    render_summary_metrics(data, selection)

    left, right = st.columns(2)

    with left:
        monthly_history = time_chart(data, selection)
        render_exploration_time_evolution(monthly_history)

    with right:
        delay_causes = cause_of_delays_ranking(data, selection)
        render_delay_causes(delay_causes)

    with st.expander("Comprendre les résultats"):
        st.write(
            "Le bilan et les causes portent sur les saisons complètes "
            "correspondant aux dates du voyage. "
            "La courbe mensuelle présente l’historique complet "
            "de la liaison."
        )

def render_travel_summary(selection: TravelSelection) -> None:
    st.subheader(f"{selection.departure} → {selection.arrival}")
    st.write(
        f"Voyage du {selection.travel_start:%d/%m/%Y} "
        f"au {selection.travel_end:%d/%m/%Y}"
    )

def render_summary_metrics(data: pd.DataFrame, selection: TravelSelection) -> None:
    st.subheader("Que montre l’historique ?")

    train_count = scheduled_trains_count(data, selection)
    cancellation_pct = cancellation_rate(data, selection)
    delay_pct = delay_rate(data, selection)
    average_delay_minutes = avg_delay_length(data, selection)

    volume, cancellations, delays, duration = st.columns(4)
    volume.metric(
        "Circulations prévues",
        f"{train_count:,}".replace(",", " ") if pd.notna(train_count) else "Indisponible",
    )
    cancellations.metric(
        "Taux d’annulation",
        f"{cancellation_pct:.2f} %" if pd.notna(cancellation_pct) else "Indisponible",
    )
    delays.metric(
        "Taux de retard à l’arrivée",
        f"{delay_pct:.2f} %" if pd.notna(delay_pct) else "Indisponible",
    )
    duration.metric(
        "Retard moyen à l’arrivée",
        f"{average_delay_minutes:.1f} min" if pd.notna(average_delay_minutes) else "Indisponible",
    )

def render_exploration_time_evolution(monthly_history: pd.DataFrame | None) -> None:
    """Display the monthly history returned by the calculation."""
    st.subheader("Évolution dans le temps")

    if monthly_history is None or monthly_history.empty :
        st.info("Aucun historique mensuel disponible pour cette liaison.")
        return
    chart_data = monthly_history.sort_values("month").set_index("month")

    st.line_chart(
        chart_data[
            ["cancellation_rate_pct", "arrival_delay_rate_pct"]
        ].rename(columns={
            "cancellation_rate_pct": "Annulations",
            "arrival_delay_rate_pct": "Retards à l’arrivée",
        }),
        x_label="Mois",
        y_label="Taux (%)",
    )

    st.line_chart(
        chart_data[["mean_arrival_delay_minutes"]].rename(columns={
            "mean_arrival_delay_minutes": "Retard moyen à l’arrivée",
        }),
        x_label="Mois",
        y_label="Minutes",
    )

def render_delay_causes(delay_causes: pd.DataFrame | None) -> None:
    """Display the delay causes returned by the calculation."""
    st.subheader("Causes des retards")

    if delay_causes is None or delay_causes.empty :
        st.info("Aucune répartition des causes disponible.")
        return

    st.dataframe(delay_causes, hide_index=True)

### COMPARISON PAGE ###

def render_comparison_dashboard(data: pd.DataFrame, selection: ComparisonSelection) -> None:
    render_ranking(selection)
    render_comparison_time_evolution(selection)

    with st.expander("Comment lire cette comparaison ?"):
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



