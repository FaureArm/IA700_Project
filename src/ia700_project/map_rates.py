"""Calculate cancellation, disruption, and delay rates for railway routes."""

import pandas as pd
import streamlit as st

from ia700_project.constants import ARRIVAL, CANCELLED, DEPARTURE, PLANNED

ARRIVAL_DELAY_COUNT = "Nombre de trains en retard à l'arrivée"


def aggregate_map_rates(
    rows: pd.DataFrame,
) -> dict[tuple[str, str], dict[str, float]]:
    """Aggregate monthly counts and calculate rates for each route.

    Args:
        rows: DataFrame containing the monthly traffic counts.

    Returns:
        A dictionary containing cancellation, disruption, and delay rates,
        indexed by departure and arrival stations.
    """
    totals = rows.groupby([DEPARTURE, ARRIVAL], as_index=False)[
        [PLANNED, CANCELLED, ARRIVAL_DELAY_COUNT]
    ].sum()

    result = {}

    for departure, arrival, planned, cancelled, delayed in totals.itertuples(
        index=False, name=None
    ):
        if planned <= 0:
            continue

        rates = {
            "cancellation": cancelled / planned,
            "disruption": (delayed + cancelled) / planned,
        }

        if planned > cancelled:
            rates["delay"] = delayed / (planned - cancelled)

        result[departure, arrival] = rates

    return result


@st.cache_data(show_spinner=False)
def load_map_rates(
    path: str,
    modified_at: int,
) -> dict[tuple[str, str], dict[str, float]]:
    """Load and cache map rates until the file timestamp changes.

    Args:
        path: Path to the CSV file.
        modified_at: File modification timestamp used for cache invalidation.

    Returns:
        A dictionary containing the calculated rates for each route.
    """
    rows = pd.read_csv(
        path,
        sep=";",
        usecols=[DEPARTURE, ARRIVAL, PLANNED, CANCELLED, ARRIVAL_DELAY_COUNT],
    )

    # TODO: Replace with the actual function call later.
    return aggregate_map_rates(rows)
