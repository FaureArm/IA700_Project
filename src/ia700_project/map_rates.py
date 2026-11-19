"""Compute route-level rates for the TGV map."""

import pandas as pd
import streamlit as st

from ia700_project.constants import ARRIVAL, CANCELLED, DEPARTURE, PLANNED

ARRIVAL_DELAY_COUNT = "Nombre de trains en retard à l'arrivée"


def aggregate_map_rates(
    rows: pd.DataFrame,
) -> dict[tuple[str, str], dict[str, float]]:
    """Aggregate monthly counts into rates by departure and arrival."""
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
    path: str, modified_at: int
) -> dict[tuple[str, str], dict[str, float]]:
    """Read the CSV and cache the map rates until its timestamp changes."""
    rows = pd.read_csv(
        path,
        sep=";",
        usecols=[DEPARTURE, ARRIVAL, PLANNED, CANCELLED, ARRIVAL_DELAY_COUNT],
    )
    return aggregate_map_rates(rows)
