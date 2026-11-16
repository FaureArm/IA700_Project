"""Explore la régularité mensuelle des TGV avec Streamlit.

Depuis la racine du dépôt :
    uv run streamlit run src/ia700_project/streamlit_app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from ia700_project.dashboards import render_dashboard
from ia700_project.sidebar import date_itinerary_sidebar
from ia700_project.pages import main_page, methods_page,comparison_page, exploration_page
from ia700_project.streamlit_utils import header


# TODO: add dataclasses to simplify returns of recurring features, ex: filter selection,
# TODO: create classes to  handle the different datasets/representations
# TODO: change all comments and descriptions to english


TITLE = "Projet IA700"


def main() -> None:
    """Affiche les filtres, les indicateurs et deux graphiques temporels."""

    st.set_page_config(page_title="SNCF Regularity", page_icon="🚆", layout="wide")
    st.sidebar.title(TITLE)

    page = st.navigation(
        [
            st.Page(main_page, title="Accueil", default=True),
            st.Page(exploration_page, title="Explorer une liaison"),
            st.Page(comparison_page, title="Comparer les liaisons"),
            st.Page(methods_page, title="Données et méthodes"),
        ],
        position="top",
    )
    page.run()

    # TODO: do better implementation
    # this is very silly way to implement. Probably a better way would be to have
    # each indicator to load the data itself, only passing the main argument? but the
    # would also need sidebar info? need to share info? not sure how to do


if __name__ == "__main__":
    main()
