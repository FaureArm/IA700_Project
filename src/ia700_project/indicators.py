"""Create indicators to later be shown through dashboards
NB this is temp, placeholder while I wait to get actual values
to then be added here
"""

import pandas as pd
from ia700_project.models import TravelSelection
from ia700_project.constants import CANCELLED, DELAY, PLANNED


def monthly_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les annulations et pondère le retard par les trains ayant circulé."""
    prepared = df.assign(
        circulated=df[PLANNED] - df[CANCELLED],
        delay_minutes=df[DELAY] * (df[PLANNED] - df[CANCELLED]),
    )
    monthly = (
        prepared.groupby("Date")[
            [PLANNED, CANCELLED, "circulated", "delay_minutes"]
        ]
        .sum()
        .sort_index()
    )
    monthly["Retard moyen à l'arrivée (min)"] = monthly[
        "delay_minutes"
    ] / monthly["circulated"].replace(0, float("nan"))
    monthly["Taux d'annulation (%)"] = (
        monthly[CANCELLED] / monthly[PLANNED] * 100
    )
    return monthly


def count_historical_scheduled_trains(
    data: pd.DataFrame, selection: TravelSelection
) -> int | None:
    """Function to calculate the number of planned trains over a date selection"""
    travel_months = pd.period_range(
        start=selection.travel_start,
        end=selection.travel_end,
        freq="M",
    ).month.unique()

    matching_rows = (
        data["gare_depart"].eq(selection.departure)
        & data["gare_arrivee"].eq(selection.arrival)
        & data["date"].dt.month.isin(travel_months)
        & data["nb_train_prevu"].gt(0)
    )
    scheduled_counts = data.loc[matching_rows, "nb_train_prevu"]

    if scheduled_counts.empty:
        return None

    return int(scheduled_counts.sum())
