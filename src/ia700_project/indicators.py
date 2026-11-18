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

def compute_route_seasonal_summary(
    data: pd.DataFrame, selection: TravelSelection
) -> pd.DataFrame | None:
    """For a selected roue and date, return a dataframe summary.

    Args:
        data: SNCF data as dataframe, after being cleaned up
        selection: selected route and date, see dataclass for more info

    Returns:
        A dataframe containing one row per season
        covered by the travel dates, pooling all available years.

        Expected columns: season, delayed trains count, scheduled trains,
        cancelled trains count, etc

         SHould return an empty DataFrame when no usable observations match
        the selection.
    """
    return None

def compute_route_monthly_history(
    data: pd.DataFrame, selection: TravelSelection
) -> pd.DataFrame | None:
    """Prepare the monthly history for a selected route.

    Args:
        data: SNCF data as a DataFrame, after being cleaned up
        selection: Selected route and travel dates, see dataclass for more info

    Returns:
        A DataFrame containing one row per calendar month, sorted
        chronologically and retaining the year

        Expected columns: month, scheduled_train_count,
        cancelled_train_count, operated_train_count,
        cancellation_rate_pct, arrival_delay_rate_pct,
        mean_arrival_delay_minutes

        ->mean delays are expressed in minutes

        Should return an empty DataFrame when no usable observations
        match the selected route

    """
    return None

def compute_route_delay_causes(
    data: pd.DataFrame, selection: TravelSelection
) -> pd.DataFrame | None:
    """Prepare delay causes for the selected route and travel seasons.

    Args:
    data: SNCF data as a DataFrame, after being cleaned up
    selection: Selected route and travel dates, see dataclass for more info

    Returns:
        truc
    """
    return None

def compute_overview_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Return route count, unique station count and latest observed month."""
    if data.empty:
        return pd.DataFrame(
            columns=["route_count", "station_count", "latest_month"]
        )

    return pd.DataFrame([{
        "route_count": len(
            data[["gare_depart", "gare_arrivee"]].dropna().drop_duplicates()
        ),
        "station_count": pd.concat(
            [data["gare_depart"], data["gare_arrivee"]]
        ).nunique(),
        "latest_month": data["date"].max(),
    }])
