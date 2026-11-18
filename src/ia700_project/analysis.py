
"""Functions for analyzing monthly TGV punctuality data."""

from pathlib import Path

import pandas as pd

# CSV column names (only one place to update if they change).
COL_DATE = "Date"
COL_DEPARTURE = "Departure station"
COL_ARRIVAL = "Arrival station"
COL_SCHEDULED = "Number of scheduled train services"
COL_CANCELLED = "Number of cancelled trains"
COL_ARRIVAL_DELAY = "Average arrival delay of all trains"
COL_DELAYED_15 = "Number of trains delayed > 15min"
COL_NB_ARRIVAL_DELAYS = "Number of trains delayed on arrival"

# Columns created by our functions.
COL_ROUTE = "route"

# Delay cause percentage columns -> display label.
CAUSE_COLUMNS = {
    "Prct delay due to external causes": "External causes",
    "Prct delay due to infrastructure": "Infrastructure",
    "Prct delay due to traffic management": "Traffic management",
    "Prct delay due to rolling stock": "Rolling stock",
    (
        "Prct delay due to station management "
        "and rolling stock reuse"
    ): "Station management",
    (
        "Prct delay due to passenger handling "
        "(crowding, PRM management, connections)"
    ): "Passengers / crowding",
}

SEASON_ORDER = ["Winter", "Spring", "Summer", "Autumn"]
SEASONS = {
    12: "Winter",
    1: "Winter",
    2: "Winter",
    3: "Spring",
    4: "Spring",
    5: "Spring",
    6: "Summer",
    7: "Summer",
    8: "Summer",
    9: "Autumn",
    10: "Autumn",
    11: "Autumn",
}


class MissingColumnsError(ValueError):
    """Raised when required columns are missing from the dataset."""


def check_columns(df: pd.DataFrame, required: list[str]) -> None:
    """Check that the dataset contains all required columns.

    Args:
        df: Dataset to check.
        required: Names of the required columns.

    Raises:
        MissingColumnsError: If at least one column is missing.
    """
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise MissingColumnsError(f"Missing columns: {missing}")


def load_data(path: Path | str) -> pd.DataFrame:
    """Load the TGV punctuality CSV file.

    Args:
        path: Path to the CSV file (separator ``;``).

    Returns:
        The raw data dataset.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path, sep=";")


def add_route_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``route`` column in the form ``DEPARTURE → ARRIVAL``.

    Args:
        df: Dataset containing departure and arrival stations.

    Returns:
        A copy of the dataset with an additional ``route`` column.
    """
    check_columns(df, [COL_DEPARTURE, COL_ARRIVAL])
    result = df.copy()
    result[COL_ROUTE] = (
        result[COL_DEPARTURE] + " → " + result[COL_ARRIVAL]
    )
    return result


def compute_route_stats(
    df: pd.DataFrame, min_months: int = 12, min_trains: int = 1000
) -> pd.DataFrame:
    """Compute reliability indicators for each route.

    Rates are expressed as a percentage of scheduled train services
    and are set to ``NaN`` when no service was scheduled.

    Args:
        df: Raw data dataset.
        min_months: Minimum number of observed months required to keep a route.
        min_trains: Minimum total number of scheduled train services.

    Returns:
        A dataset indexed by route with the columns ``months``,
        ``services``, ``arrival_delay``, ``trains_delayed_15``,
        ``cancellations``, ``delay_rate_15`` and ``cancellation_rate``.

    Raises:
        MissingColumnsError: If a required column is missing.
    """
    check_columns(
        df,
        [
            COL_DATE,
            COL_DEPARTURE,
            COL_ARRIVAL,
            COL_SCHEDULED,
            COL_CANCELLED,
            COL_ARRIVAL_DELAY,
            COL_DELAYED_15,
        ],
    )
    stats = (
        add_route_column(df)
        .groupby(COL_ROUTE)
        .agg(
            months=(COL_DATE, "nunique"),
            services=(COL_SCHEDULED, "sum"),
            arrival_delay=(COL_ARRIVAL_DELAY, "mean"),
            trains_delayed_15=(COL_DELAYED_15, "sum"),
            cancellations=(COL_CANCELLED, "sum"),
        )
    )
    services = stats["services"].where(stats["services"] > 0)
    stats["delay_rate_15"] = (
        100 * stats["trains_delayed_15"] / services
    )
    stats["cancellation_rate"] = (
        100 * stats["cancellations"] / services
    )

    enough_months = stats["months"] >= min_months
    enough_trains = stats["services"] >= min_trains
    return stats[enough_months & enough_trains]


def season_of(month: int) -> str:
    """Return the season corresponding to a given month.

    Args:
        month: Month number, from 1 to 12.

    Returns:
        ``"Winter"``, ``"Spring"``, ``"Summer"`` or ``"Autumn"``.

    Raises:
        ValueError: If the month number is invalid.
    """
    try:
        return SEASONS[month]
    except KeyError as error:
        raise ValueError(f"Invalid month: {month}") from error


def seasonal_cause_shares(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the average share of each delay cause by season.

    Each row is weighted by the number of trains delayed on arrival
    (negative values are counted as 0). Since the ``Prct ...`` columns
    are already expressed as percentages, the sum of causes for each
    season equals 100.

    Args:
        df: Dataset containing the date, the number of delayed trains
            and the percentages for each delay cause.

    Returns:
        A seasons (rows) x causes (columns) dataset, expressed as
        percentages. Seasons missing from the data are filled with ``NaN``.

    Raises:
        MissingColumnsError: If a required column is missing.
    """
    check_columns(
        df,
        [COL_DATE, COL_NB_ARRIVAL_DELAYS, *CAUSE_COLUMNS],
    )
    months = pd.to_datetime(
        df[COL_DATE], format="%Y-%m", errors="coerce"
    )
    seasons = months.dt.month.map(SEASONS)
    weights = df[COL_NB_ARRIVAL_DELAYS].clip(lower=0)
    weighted = (
        df[list(CAUSE_COLUMNS)]
        .fillna(0)
        .mul(weights, axis=0)
    )
    totals = weighted.groupby(seasons).sum()
    shares = totals.div(weights.groupby(seasons).sum(), axis=0)
    return shares.rename(columns=CAUSE_COLUMNS).reindex(SEASON_ORDER)
