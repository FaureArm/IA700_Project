"""
Create dashboards to be displayed by our steamlit app.
"""

from pathlib import Path
import streamlit as st
from ia700_project.indicators import monthly_indicators
import pandas as pd
from ia700_project.models import FilterSelection, TravelSelection, ComparisonSelection

DATA_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "regularite-mensuelle-tgv-aqst.csv"
)
PLANNED = "Nombre de circulations prévues"
CANCELLED = "Nombre de trains annulés"
DELAY = "Retard moyen de tous les trains à l'arrivée"
DEPARTURE = "Gare de départ"
ARRIVAL = "Gare d'arrivée"
ALL_STATIONS = "Toutes les gares"
TITLE = "Projet IA700"


def render_dashboard(
    filtered: pd.DataFrame, filter_selection: FilterSelection, excluded
):

    start = filter_selection.start_month
    end = filter_selection.end_month

    monthly = monthly_indicators(filtered)
    planned = int(filtered[PLANNED].sum())
    cancelled = int(filtered[CANCELLED].sum())
    circulated = planned - cancelled
    delay = float(monthly["delay_minutes"].sum() / circulated) if circulated else None
    st.subheader(f"Votre bilan : {start} à {end}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Circulations prévues", f"{planned:,}".replace(",", " "))
    col2.metric("Taux d'annulation", f"{cancelled / planned * 100:.2f} %")
    col3.metric(
        "Retard moyen à l'arrivée",
        f"{delay:.1f} min" if delay is not None else "Indisponible",
    )
    st.caption(
        f"{len(filtered):,} observations mensuelles par liaison · "
        f"{filtered[[DEPARTURE, ARRIVAL]].drop_duplicates().shape[0]} liaisons orientées. "
        "Une circulation est comptée pour chaque liaison déclarée dans le dataset ; "
        "ces volumes ne représentent pas nécessairement des trains uniques sur le réseau."
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Comment évoluent les retards ?")
        st.line_chart(
            monthly[["Retard moyen à l'arrivée (min)"]],
            x_label="Mois",
            y_label="Minutes",
            color="#2563EB",
        )
        st.caption(
            "Retard moyen de tous les trains à l'arrivée, pondéré par le nombre "
            "de circulations réalisées sur chaque liaison."
        )
    with right:
        st.subheader("Quelle part des trains est annulée ?")
        st.line_chart(
            monthly[["Taux d'annulation (%)"]],
            x_label="Mois",
            y_label="Annulations (%)",
            color="#E97732",
        )
        st.caption(
            "Nombre total d'annulations / nombre total de circulations prévues × 100."
        )

    with st.expander("Voir les données de la sélection"):
        st.dataframe(filtered, hide_index=True)
    with st.expander("Comprendre les calculs"):
        st.markdown("Lorem ipsum blablabla")
        st.caption(f"{excluded} lignes écartées sur le fichier complet.")
    st.markdown(
        "[Consulter le jeu de données SNCF](https://ressources.data.sncf.com/"
        "explore/dataset/regularite-mensuelle-tgv-aqst/information/)"
    )


def render_exploration_dashboard(selection: TravelSelection) -> None:
    """Display the travel summary and historical analysis placeholders."""
    render_travel_summary(selection)

    st.info(
        "=> ici on affiche les résultats historiques de la selection. Pas une prédiction, juste" \
        "dire que ba à cette période la des années précédentes, on a eu tel retard moyen et tel taux d'annulation" \
        "On peut probablement juste faire par mois au final"
    )

    render_summary_metrics()

    left, right = st.columns(2)

    with left:
        render_exploration_time_evolution()

    with right:
        render_delay_causes()

    with st.expander("Comprendre les résultats"):
        st.write(
            "blablabla petite description pour faire jolie"
        )


def render_ranking(selection: ComparisonSelection) -> None:
    st.subheader(f"Classement · {selection.entity}")
    st.caption(
        f"{selection.metric} · {selection.top_n} résultats maximum · "
        f"minimum {selection.min_volume} circulations prévues"
    )
    st.info(
        "Afficher ici le classement et les volumes associés à la recherche du sidebar"
    )


def render_time_evolution(selection: ComparisonSelection) -> None:
    st.subheader("Comparer les évolutions")
    st.info(
        " Ici, montrer une évolution temporelle de nos variables séléctionnées " \
        " montrer évolution pour tous les candidats du top ? eg si on choisit le nbre de résultats" \
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
    st.info("Afficher répartition des causes, grosses catégories ou qqchose vu qu'on a pas bcp d'infos")
