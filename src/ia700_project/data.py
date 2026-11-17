"""File to load, validate and handle our dataset"""

from pathlib import Path

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
    Path(__file__).resolve().parents[2] # adjust the path as needed
    / "data"
    / "regularite-mensuelle-tgv-aqst.csv"
)



@st.cache_data
def load_data(path: str, modified_at: int) -> tuple[pd.DataFrame, int]:
    """Lit le CSV SNCF et écarte les lignes inutilisables pour ces indicateurs.

    Args:
        path: CSV path
        modified_at: last modification timestep, used to invalidate cache later on

    Returns:
        Données valides et nombre de lignes écartées

    Raises:
        ValueError: Si des colonnes requises sont absentes
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
