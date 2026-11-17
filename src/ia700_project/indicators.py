"""
Create indicators to later be shown through dashboards
NB this is temp, placeholder while I wait to get actual values 
to then be added here
"""

import pandas as pd

from ia700_project.constants import CANCELLED, DELAY, PLANNED


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
