"""Explore la régularité mensuelle des TGV avec Streamlit.

Depuis la racine du dépôt :
    uv run streamlit run src/ia700_project/streamlit_app.py
"""


import streamlit as st

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
    """Configure the application and run the selected page"""

    st.set_page_config(page_title="SNCF Regularity", page_icon="🚆", layout="wide")
    st.sidebar.title(TITLE)


    ## define navigation bar ##
    # perhaps could be done in a specific component
    # although might not be reused so not sure if it's worth it
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

if __name__ == "__main__":
    main()
