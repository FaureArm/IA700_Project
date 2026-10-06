"""
Create indicators to later be shown through dashboards
"""

from pathlib import Path

import pandas as pd

DATA_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "regularite-mensuelle-tgv-aqst.csv"
)
PLANNED = "Nombre de circulations prévues"
CANCELLED = "Nombre de trains annulés"
DELAY = "Retard moyen de tous les trains à l'arrivée"
DEPARTURE = "Gare de départ"
ARRIVAL = "Gare d'arrivée"
ALL_STATIONS = "Toutes les gares"
TITLE = "Projet IA700"


def monthly_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les annulations et pondère le retard par les trains ayant circulé."""
    prepared = df.assign(
        circulated=df[PLANNED] - df[CANCELLED],
        delay_minutes=df[DELAY] * (df[PLANNED] - df[CANCELLED]),
    )
    monthly = (
        prepared.groupby("Date")[[PLANNED, CANCELLED, "circulated", "delay_minutes"]]
        .sum()
        .sort_index()
    )
    monthly["Retard moyen à l'arrivée (min)"] = monthly["delay_minutes"] / monthly[
        "circulated"
    ].replace(0, float("nan"))
    monthly["Taux d'annulation (%)"] = monthly[CANCELLED] / monthly[PLANNED] * 100
    return monthly
