"""File to load, validate and handle our dataset"""

from pathlib import Path
from ia700_project.cleaning import clean_dataset
import pandas as pd
import streamlit as st

from ia700_project.constants import (
    ARRIVAL,
    CANCELLED,
    DELAY,
    DEPARTURE,
    PLANNED,
)

DATA_PATH = (
    Path(__file__).resolve().parents[2]  # adjust the path as needed
    / "data"
    / "regularite-mensuelle-tgv-aqst.csv"
)


@st.cache_data
def load_data(path: str, modified_at: int) -> pd.DataFrame:
    """Charge et nettoie le CSV quand sa date de modification change."""
    return clean_dataset(path)
