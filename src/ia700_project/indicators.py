"""Create indicators to later be shown through dashboards
NB this is temp, placeholder while I wait to get actual values
to then be added here
"""

import pandas as pd
from ia700_project.models import ComparisonSelection, TravelSelection

### Main Page ###

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


### Exploration Page ###

def scheduled_trains_count(data: pd.DataFrame, selection: TravelSelection) -> int | None:
    """Expected return: an intenger expressing number of scheduled trains for the selected 
    route and date.
    """
    return None


def cancellation_rate(data: pd.DataFrame, selection: TravelSelection) -> float | None:
    """Expected return: percentage (0-100) of trains cancelled for a given selection."""
    return None


def delay_rate(data: pd.DataFrame, selection: TravelSelection) -> float | None:
    """Expected return: percentage (0-100) of late trains for a given selection.
    NB: late means bigger than 15 min ?"""
    return None


def avg_delay_length(data: pd.DataFrame, selection: TravelSelection) -> float | None:
    """Expected return: integer expressin avg delay in minutes for a given selection.
    NB: Count delays below 15 min?"""
    return None


def time_chart(data: pd.DataFrame, selection: TravelSelection) -> pd.DataFrame | None:
    """Expected returns: A dataframe with cols:
            month
            cancellation_rate_pct
            arrival_delay_rate_pct
            mean_arrival_delay_minutes
        For the selection expressed in the argument
    """
    return None


def cause_of_delays_ranking(data: pd.DataFrame, selection: TravelSelection) -> pd.DataFrame | None:
    """Expected return: dataframe sorted by causes of delays for a given selection, ranked from highest to lowest.
    The goal is to see which causes are the most frequent for a given selection."""
    return None

### Comparison Page ###

def ranking(data: pd.DataFrame, selection: ComparisonSelection) -> pd.DataFrame | None:
    """Expected return: for the selected variables, return a global ranking as a dataframe:
        rank
        entity: liaison or station label ("PARIS LYON → LYON PART DIEU" or "PARIS LYON")
        value: calculated value of the indicator selected in the sidebar
        scheduled_train_count"""
    return None


def comparison_time_chart(
    data: pd.DataFrame,
    selection: ComparisonSelection,
    ranking_data: pd.DataFrame,
) -> pd.DataFrame | None:
    """Expected return: a df covering the entities provided in ranking_data
        month
        entity: liaison or station label ("PARIS LYON → LYON PART DIEU" or "PARIS LYON")
        value: calculated value of the indicator selected in the sidebar
    """
    return None
