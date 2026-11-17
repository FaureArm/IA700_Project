"""
Create pages to host dashboards
"""

from pathlib import Path
from ia700_project.data import DATA_PATH, load_data
import pandas as pd
import streamlit as st

from ia700_project.sidebar import (
    date_itinerary_sidebar,
    comparison_sidebar,
)
from ia700_project.dashboards import (
    render_exploration_dashboard,
    render_ranking,
    render_time_evolution,
)

TITLE = "Projet IA700"



def main_page():
    st.title("Accueil")
    st.map(
        pd.DataFrame({"lat": [46.6], "lon": [2.2]}),
        zoom=4,
    )

def exploration_page():
    st.title("Explorer une liaison")
    st.markdown(
        "Sélectionnez une liaison et une période pour consulter "
        "son historique de retards et d’annulations."
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
    filtered, selection = date_itinerary_sidebar(df)
    render_exploration_dashboard(selection)


def comparison_page():
    """
    Page to show some global basic metrics,
    through rankings, volumes, evolutions, etc.
    """
    st.title("Comparer les liaisons")
    st.markdown(
        "Comparez la régularité des liaisons et des gares "
        "sur une même période historique."
    )
    # sidebar to select what to show
    # returns type of comparison, metric, top_n, min_volume
    # for more details check in sidebar.py
    selection = comparison_sidebar()


    render_ranking(selection)
    render_time_evolution(selection)

    with st.expander("Comment lire cette comparaison ?"):
        st.write(
            "blablabla petite description pour faire jolie"
        )

def methods_page():
    st.title("Données et méthodes")
    return
