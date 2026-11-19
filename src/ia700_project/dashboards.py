"""Create dashboards to be displayed by our steamlit app."""

import pandas as pd
import streamlit as st

from ia700_project.indicators import (
    avg_delay_length,
    cancellation_rate,
    cause_of_delays_ranking,
    comparison_time_chart,
    compute_overview_summary,
    delay_rate,
    ranking,
    scheduled_trains_count,
    time_chart,
)
from ia700_project.map_view import render_tgv_map
from ia700_project.models import ComparisonSelection, TravelSelection

### MAIN PAGE ###


def render_overview_dashboard(data: pd.DataFrame) -> None:
    """Render the network metrics and interactive map."""
    # st.caption(f"Vérification · {len(data):,} observations reçues.")
    overview_summary = compute_overview_summary(data)
    render_overview_metrics(overview_summary)
    # to render some generic values on top, could be switched to a sidebar,
    # or smth else perhaps idk?
    render_network_map(data)  # to render the map with overlay


def render_network_map(data: pd.DataFrame) -> None:
    """Add the network heading and interactive map to the overview."""
    st.subheader("Le réseau en un regard")
    render_tgv_map(data)


def render_overview_metrics(overview_summary: pd.DataFrame | None) -> None:
    """Display the dataset overview returned by the calculation."""
    route_count_label = "—"
    station_count_label = "—"
    # latest_month_label = "—"

    if overview_summary is None:
        st.caption("Aucune donnée exploitable pour les indicateurs du réseau.")
    elif overview_summary.empty:
        st.caption("Aucune donnée exploitable pour les indicateurs du réseau.")
    else:
        summary = overview_summary.iloc[0]

        route_count_label = f"{int(summary['route_count']):,}".replace(
            ",", " "
        )
        station_count_label = f"{int(summary['station_count']):,}".replace(
            ",", " "
        )

        # if pd.notna(summary["latest_month"]):
        #     latest_month_label = pd.Timestamp(
        #         summary["latest_month"]
        #     ).strftime("%m/%Y")

    routes_column, stations_column, latest_month_column = st.columns(3)

    routes_column.metric("Liaisons couvertes", route_count_label)
    stations_column.metric("Gares représentées", station_count_label)


### EXPLORATION PAGE ###


def render_exploration_dashboard(
    data: pd.DataFrame, selection: TravelSelection
) -> None:
    """Render the summary and history for the selected journey.

    Args:
        data (pd.DataFrame): _description_
        selection (TravelSelection): _description_
    """
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
    """Display the selected route and travel dates.

    Args:
        selection (TravelSelection): _description_
    """
    st.subheader(f"{selection.departure} → {selection.arrival}")
    st.write(
        f"Voyage du {selection.travel_start:%d/%m/%Y} "
        f"au {selection.travel_end:%d/%m/%Y}"
    )


def render_summary_metrics(
    data: pd.DataFrame, selection: TravelSelection
) -> None:
    """Display train volume, cancellation, and arrival delay metrics.

    Args:
        data (pd.DataFrame): _description_
        selection (TravelSelection): _description_
    """
    st.subheader("Que montre l’historique ?")

    train_count = scheduled_trains_count(data, selection)
    cancellation_pct = cancellation_rate(data, selection)
    delay_pct = delay_rate(data, selection)
    average_delay_minutes = avg_delay_length(data, selection)

    volume, cancellations, delays, duration = st.columns(4)
    volume.metric(
        "Circulations prévues",
        f"{train_count:,}".replace(",", " ")
        if pd.notna(train_count)
        else "Indisponible",
    )
    cancellations.metric(
        "Taux d’annulation",
        f"{cancellation_pct:.2f} %"
        if pd.notna(cancellation_pct)
        else "Indisponible",
    )
    delays.metric(
        "Taux de retard à l’arrivée",
        f"{delay_pct:.2f} %" if pd.notna(delay_pct) else "Indisponible",
    )
    duration.metric(
        "Retard moyen à l’arrivée",
        f"{average_delay_minutes:.1f} min"
        if pd.notna(average_delay_minutes)
        else "Indisponible",
    )


def render_exploration_time_evolution(
    monthly_history: pd.DataFrame | None,
) -> None:
    """Display the monthly history returned by the calculation."""
    st.subheader("Évolution dans le temps")

    if monthly_history is None or monthly_history.empty:
        st.info("Aucun historique mensuel disponible pour cette liaison.")
        return
    chart_data = monthly_history.sort_values("month").set_index("month")

    st.line_chart(
        chart_data[["cancellation_rate_pct", "arrival_delay_rate_pct"]].rename(
            columns={
                "cancellation_rate_pct": "Annulations",
                "arrival_delay_rate_pct": "Retards à l’arrivée",
            }
        ),
        x_label="Mois",
        y_label="Taux (%)",
    )

    st.line_chart(
        chart_data[["mean_arrival_delay_minutes"]].rename(
            columns={
                "mean_arrival_delay_minutes": "Retard moyen à l’arrivée",
            }
        ),
        x_label="Mois",
        y_label="Minutes",
    )


def render_delay_causes(delay_causes: pd.DataFrame | None) -> None:
    """Display the delay causes returned by the calculation."""
    st.subheader("Causes des retards")

    if delay_causes is None or delay_causes.empty:
        st.info("Aucune répartition des causes disponible.")
        return

    # need to specifically name cols bc otherwise
    # takes the df col names, not UI friendly
    st.dataframe(
        delay_causes,
        hide_index=True,
        column_config={
            "cause": st.column_config.TextColumn(
                "Cause du retard",
            ),
            "percentage": st.column_config.NumberColumn(
                "Part des retards (%)",
                format="%.2f",
            ),
        },
    )


### COMPARISON PAGE ###


def render_comparison_dashboard(
    data: pd.DataFrame, selection: ComparisonSelection
) -> None:
    """Render the ranking and monthly trends for the comparison.

    Args:
        data (pd.DataFrame): _description_
        selection (ComparisonSelection): _description_
    """
    ranking_data = ranking(data, selection)
    render_ranking(ranking_data, selection)

    if ranking_data is None or ranking_data.empty:
        monthly_history = ranking_data
    else:
        monthly_history = comparison_time_chart(data, selection, ranking_data)

    render_comparison_time_evolution(monthly_history, selection)

    with st.expander("Comment lire cette comparaison ?"):
        st.write("TODO")


def render_ranking(
    ranking_data: pd.DataFrame | None,
    selection: ComparisonSelection,
) -> None:
    """Display the ranking for the selected metric.

    Args:
        ranking_data (pd.DataFrame | None): _description_
        selection (ComparisonSelection): _description_
    """
    st.subheader(f"Classement · {selection.entity}")
    st.caption(
        f"{selection.metric} · {selection.top_n} résultats maximum · "
        f"minimum {selection.min_volume} circulations prévues"
    )

    # here we differentiate between missing data
    # and a empty search function, unlike other dashboards
    if ranking_data is None:
        st.info("Aucunes données disponibles.")
        return

    if ranking_data.empty:
        st.info("Aucun résultat ne correspond aux critères sélectionnés.")
        return
    # need to specifically name cols bc otherwise
    # takes the df col names, not UI friendly
    # in this scenario, need to take into account selection units
    entity_label = {
        "Liaisons": "Liaison",
        "Gares de départ": "Gare de départ",
        "Gares d’arrivée": "Gare d’arrivée",
    }[selection.entity]

    is_duration = selection.metric == "Retard moyen à l’arrivée"
    unit = "min" if is_duration else "%"
    value_format = "%.1f" if is_duration else "%.2f"

    st.dataframe(
        ranking_data,
        hide_index=True,
        column_config={
            "rank": st.column_config.NumberColumn(
                "Rang",
                format="%d",
            ),
            "entity": st.column_config.TextColumn(
                entity_label,
                width="large",
            ),
            "value": st.column_config.NumberColumn(
                f"{selection.metric} ({unit})",
                format=value_format,
            ),
            "scheduled_train_count": st.column_config.NumberColumn(
                "Circulations prévues",
                format="%d",
            ),
        },
    )


def render_comparison_time_evolution(
    monthly_history: pd.DataFrame | None,
    selection: ComparisonSelection,
) -> None:
    """Plot the monthly values for the compared routes or stations.

    Args:
        monthly_history (pd.DataFrame | None): _description_
        selection (ComparisonSelection): _description_
    """
    st.subheader("Comparer les évolutions")

    # here we differentiate between missing data
    # and a empty search function, unlike other dashboards
    if monthly_history is None:
        st.info("Aucunes données disponibles.")
        return

    if monthly_history.empty:
        st.info("Aucun historique disponible pour cette comparaison.")
        return

    # plot our chart
    chart_data = monthly_history.pivot(
        index="month",
        columns="entity",
        values="value",
    ).sort_index()

    unit = (
        "Minutes"
        if selection.metric == "Retard moyen à l’arrivée"
        else "Taux (%)"
    )

    st.line_chart(chart_data, x_label="Mois", y_label=unit)
