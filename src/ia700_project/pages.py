"""Create pages to host dashboards
"""

import pandas as pd
import streamlit as st

from ia700_project.dashboards import (
    render_comparison_dashboard,
    render_exploration_dashboard,
    render_overview_dashboard,
)
from ia700_project.data import DATA_PATH, load_data
from ia700_project.sidebar import (
    comparison_sidebar,
    date_itinerary_sidebar,
)


def main_page():
    st.title("Accueil")
    st.markdown(
        "Découvrez la régularité des liaisons TGV, "
        "explorez l’historique de votre trajet et comparez les résultats."
    )
    st.caption("Source : SNCF Open Data · Régularité mensuelle TGV (AQST)")

    render_overview_dashboard()


def exploration_page():
    st.title("Explorer une liaison")
    st.markdown(
        "Sélectionnez une liaison et une période pour consulter "
        "son historique de retards et d’annulations."
    )
    st.caption("Source : SNCF Open Data · Régularité mensuelle TGV (AQST)")

    try:
        df = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns) #st_mtime_ns is the time of last modification of the file
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
    selection = date_itinerary_sidebar(df)

    ## main dashboard ##
    render_exploration_dashboard(df, selection)


def comparison_page():
    """Page to show some global basic metrics,
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

    render_comparison_dashboard(selection)


def methods_page():
    st.title("Données et méthodes")
    return
