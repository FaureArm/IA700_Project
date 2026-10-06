"""
Create dashboards to be displayed by our steamlit app.
"""

from pathlib import Path
import streamlit as st
from ia700_project.indicators import monthly_indicators
import pandas as pd
from ia700_project.models import FilterSelection


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
    st: st.streamlit,
    filtered: pd.DataFrame,
    filter_selection: FilterSelection,
    excluded,
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
