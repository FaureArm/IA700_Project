"""Create pages to host dashboards."""

import pandas as pd
import streamlit as st

from ia700_project.dashboards import (
    render_comparison_dashboard,
    render_exploration_dashboard,
    render_overview_dashboard,
)
from ia700_project.sidebar import (
    comparison_sidebar,
    date_itinerary_sidebar,
)


def main_page(data: pd.DataFrame) -> None:
    """Render the home page with the TGV regularity overview.

    Args:
        data (pd.DataFrame): _description_
    """
    st.title("Accueil")
    st.markdown(
        "Découvrez la régularité des liaisons TGV, "
        "explorez l’historique de votre trajet et comparez les résultats."
    )
    st.caption("Source : SNCF Open Data · Régularité mensuelle TGV (AQST)")

    render_overview_dashboard(data)


def exploration_page(data: pd.DataFrame) -> None:
    """Render the exploration page for a selected route and travel dates.

    Args:
        data (pd.DataFrame): _description_
    """
    st.title("Explorer une liaison")
    st.markdown(
        "Sélectionnez une liaison et une période pour consulter "
        "son historique de retards et d’annulations."
    )
    st.caption("Source : SNCF Open Data · Régularité mensuelle TGV (AQST)")

    ### sidebar ###
    selection = date_itinerary_sidebar(data)

    ## main dashboard ##
    render_exploration_dashboard(data, selection)


def comparison_page(data: pd.DataFrame) -> None:
    """Render page to compare global metrics.

    Page to show some global basic metrics, through rankings,
    volumes, evolutions, etc.

    Args:
        data (pd.DataFrame): _description_
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
    render_comparison_dashboard(data, selection)


def methods_page():
    """Render the methods page."""
    st.title("Données et méthodes")
    return
