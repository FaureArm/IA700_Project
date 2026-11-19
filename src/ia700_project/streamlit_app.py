"""Main file to start running our streamlit app.

Run from root of project :
    uv run streamlit run src/ia700_project/streamlit_app.py
"""

import streamlit as st

from ia700_project.data import DATA_PATH, load_data
from ia700_project.pages import (
    comparison_page,
    exploration_page,
    main_page,
    methods_page,
)

# TODO: create classes to  handle the different datasets/representations?
# TODO: change all comments and descriptions to english


TITLE = "Projet IA700"


def main() -> None:
    """Configure the application and run the selected page."""
    st.set_page_config(
        page_title="SNCF Regularity", page_icon="🚆", layout="wide"
    )
    st.sidebar.title(TITLE)

    ## Load data ##
    try:
        cleaned_data = load_data(
            str(DATA_PATH),
            DATA_PATH.stat().st_mtime_ns,
        )
    except FileNotFoundError:
        st.error("Le jeu de données SNCF est absent.")
        st.info(
            "Placez regularite-mensuelle-tgv-aqst.csv "
            "dans le dossier data/ à la racine du projet."
        )
        st.stop()
    except (OSError, ValueError) as error:
        st.error(f"Impossible de préparer les données SNCF : {error}")
        st.stop()

    if cleaned_data.empty:
        st.warning("Le fichier ne contient aucune observation exploitable.")
        st.stop()

    # necessary functions to pass along our loaded data
    # reasoning with a top to bottom approach instead of
    # having to relaod the data everytime we need it
    # otherwise could try to have it as some kind of global variable ?
    def show_home_page() -> None:
        main_page(cleaned_data)

    def show_exploration_page() -> None:
        exploration_page(cleaned_data)

    def show_comparison_page() -> None:
        comparison_page(cleaned_data)

    ## define navigation bar ##
    # perhaps could be done in a specific component
    # although might not be reused so not sure if it's worth it
    page = st.navigation(
        [
            st.Page(show_home_page, title="Accueil", default=True),
            st.Page(show_exploration_page, title="Explorer une liaison"),
            st.Page(show_comparison_page, title="Comparer les liaisons"),
            st.Page(methods_page, title="Données et méthodes"),
        ],
        position="top",
    )
    page.run()


if __name__ == "__main__":
    main()
