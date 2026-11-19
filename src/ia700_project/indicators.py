"""Create indicators to later be shown through dashboards."""

import pandas as pd

from ia700_project.models import ComparisonSelection, TravelSelection

### Main Page ###


def compute_overview_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Return route count, unique station count and latest observed month."""
    if data.empty:
        return pd.DataFrame(
            columns=["route_count", "station_count", "latest_month"]
        )

    return pd.DataFrame(
        [
            {
                "route_count": len(
                    data[["gare_depart", "gare_arrivee"]]
                    .dropna()
                    .drop_duplicates()
                ),
                "station_count": pd.concat(
                    [data["gare_depart"], data["gare_arrivee"]]
                ).nunique(),
                "latest_month": data["date"].max(),
            }
        ]
    )


### Exploration Page ###


def scheduled_trains_count(
    data: pd.DataFrame, selection: TravelSelection
) -> int | None:
    """Return the number of scheduled trains for a selected route and date."""
    return None


def cancellation_rate(
    data: pd.DataFrame, selection: TravelSelection
) -> float | None:
    """Return the cancellation percentage for a given selection."""
    return None


def delay_rate(data: pd.DataFrame, selection: TravelSelection) -> float | None:
    """Return the percentage of late trains for a given selection.

    A late train may be defined as a train delayed by more than 15 minutes.
    """
    return None


def avg_delay_length(
    data: pd.DataFrame, selection: TravelSelection
) -> float | None:
    """Return the average arrival delay in minutes for a given selection.

    The treatment of delays below 15 minutes remains to be defined.
    """
    return None


def time_chart(
    data: pd.DataFrame, selection: TravelSelection
) -> pd.DataFrame | None:
    """Return monthly indicators for the selected route and date range.

    Expected columns:
        - month
        - cancellation_rate_pct
        - arrival_delay_rate_pct
        - mean_arrival_delay_minutes
    """
    return None


def cause_of_delays_ranking(
    data: pd.DataFrame, selection: TravelSelection
) -> pd.DataFrame | None:
    """Return delay causes ranked from most to least frequent.

    The ranking identifies the most frequent causes for a given selection.
    """
    return None


### Comparison Page ###


def ranking(
    data: pd.DataFrame, selection: ComparisonSelection
) -> pd.DataFrame | None:
    """Return a global ranking for the selected comparison variables.

    Expected columns:
        - rank
        - entity: route or station label
        - value: calculated indicator value
        - scheduled_train_count
    """
    return None


def comparison_time_chart(
    data: pd.DataFrame,
    selection: ComparisonSelection,
    ranking_data: pd.DataFrame,
) -> pd.DataFrame | None:
    """Return monthly indicator values for the ranked entities.

    Expected columns:
        - month
        - entity: route or station label
        - value: calculated indicator value
    """
    return None
