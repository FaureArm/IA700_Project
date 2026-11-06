"""Explore la régularité mensuelle des TGV avec Streamlit.

Depuis la racine du dépôt :
    uv run streamlit run src/ia700_project/streamlit_app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from ia700_project.dashboards import render_dashboard
from ia700_project.sidebar import date_itinerary_sidebar
from ia700_project.pages import main_page


def header():

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"

    def select_page(page: str) -> None:
        st.session_state.current_page = page

    title_col, *nav_cols = st.columns([3, 1, 1, 1])

    with title_col:
        st.subheader("🚆 SNCF Regularity")

    for column, name in zip(nav_cols, ["Home", "Test", "Data quality"]):
        column.button(
            name,
            key=f"nav_{name}",
            type="primary" if st.session_state.current_page == name else "secondary",
            use_container_width=True,
            on_click=select_page,
            args=(name,),
        )

    st.divider()
    page = st.session_state.current_page
    return page
