"""Explore la régularité mensuelle des TGV avec Streamlit.

Depuis la racine du dépôt :
    uv run streamlit run src/ia700_project/streamlit_app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from ia700_project.sidebar import date_itinerary_sidebar
from ia700_project.dashboards import render_dashboard


# TODO: separate main streamlit functionalities into different files (eg: sidebar, title, graphs, cols, etc)
# TODO: add dataclasses to simplify returns of recurring features, ex: filter selection,
# TODO: create classes to  handle the different datasets/representations
# TODO: change all comments and descriptions to english

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


@st.cache_data
def load_data(path: str, modified_at: int) -> tuple[pd.DataFrame, int]:
    """Lit le CSV SNCF et écarte les lignes inutilisables pour ces indicateurs.

    Args:
        path: Chemin du CSV séparé par des points-virgules.
        modified_at: Date de modification, utilisée pour invalider le cache.

    Returns:
        Données valides et nombre de lignes écartées.

    Raises:
        ValueError: Si des colonnes requises sont absentes.
    """
    df = pd.read_csv(path, sep=";")
    required = ["Date", DEPARTURE, ARRIVAL, PLANNED, CANCELLED, DELAY]
    missing = set(required).difference(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {', '.join(sorted(missing))}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for column in [PLANNED, CANCELLED, DELAY]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    valid = (
        df[required].notna().all(axis=1)
        & df[PLANNED].gt(0)
        & df[CANCELLED].ge(0)
        & df[CANCELLED].le(df[PLANNED])
        & df[DELAY].ge(0)
        & df[[PLANNED, CANCELLED, DELAY]].lt(float("inf")).all(axis=1)
    )
    return df.loc[valid].copy(), int((~valid).sum())


def main() -> None:
    """Affiche les filtres, les indicateurs et deux graphiques temporels."""
    st.set_page_config(page_title="SNCF Regularity", page_icon="🚆", layout="wide")
    st.title(TITLE)
    st.markdown(
        "Explorez la régularité des TGV : **comment evolue la fiabilite des vos trajets TGV lors de vos departs ?**\n"
        " Sélectionnez vos dates de trajet ainsi que vos gares, et obtenez un apercu des risques de perturbations."
    )
    st.caption("Source : SNCF Open Data · Régularité mensuelle TGV (AQST)")

    try:
        df, excluded = load_data(
            str(DATA_PATH), DATA_PATH.stat().st_mtime_ns
        )  # see func load_data() to understand what are excluded lines
    except FileNotFoundError:
        st.error("Le jeu de données SNCF est absent.")
        st.info(
            "Placez regularite-mensuelle-tgv-aqst.csv dans le dossier data/ "
            "à la racine du projet. Ce fichier doit aussi être disponible sur l'hébergeur."
        )
        st.stop()
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.error(f"Impossible de lire les données SNCF : {error}")
        st.stop()

    if df.empty:
        st.warning(
            "Le fichier ne contient aucune ligne exploitable pour ces indicateurs."
        )
        st.stop()

    ### sidebar ###
    filtered, filter_selection = date_itinerary_sidebar(df)
    ### main dashboard ###
    render_dashboard(st, filtered, filter_selection, excluded)

    # TODO: do better implementation
    # this is very silly way to implement. Probably a better way would be to have
    # each indicator to load the data itself, only passing the main argument? but the
    # would also need sidebar info? need to share info? not sure how to do


if __name__ == "__main__":
    main()
