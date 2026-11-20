"""Create pages to host dashboards."""

import pandas as pd
import streamlit as st

from ia700_project.dashboards import (
    render_cleaning_dashboard,
    render_comparison_dashboard,
    render_data_source_dashboard,
    render_exploration_dashboard,
    render_methodology_dashboard,
    render_overview_dashboard,
    render_quality_dashboard,
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
    st.divider()

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
    st.divider()

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
    st.divider()
    # sidebar to select what to show
    # returns type of comparison, metric, top_n, min_volume
    # for more details check in sidebar.py
    selection = comparison_sidebar()
    render_comparison_dashboard(data, selection)


def methods_page() -> None:
    """Render the methods page."""
    st.title("Données et méthodes")
    st.markdown(
        "D’où viennent les données ? Comment les avons-nous préparées ? "
        "Retrouvez les choix qui permettent de lire nos résultats."
    )
    st.caption(
        "Source : SNCF Open Data · Régularité mensuelle TGV (AQST) · "
        "Méthode documentée dans le notebook EDA"
    )
    st.divider()

    render_data_source_dashboard()
    st.divider()
    render_cleaning_dashboard()
    st.divider()
    render_quality_dashboard()
    st.divider()
    render_methodology_dashboard()
