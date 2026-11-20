"""Compute route-level rates for the TGV map."""

import pandas as pd
import streamlit as st

ARRIVAL_DELAY_COUNT = "nb_train_retard_arrivee"

def aggregate_map_rates(
    rows: pd.DataFrame,
) -> dict[tuple[str, str], dict[str, float]]:
    """Aggregate valid cleaned monthly counts by departure and arrival."""
    valid = rows.loc[
        rows["nb_train_prevu"].gt(0)
        & rows["nb_annulation"].ge(0)
        & rows["nb_annulation"].le(rows["nb_train_prevu"])
    ]

    result = {}
    for (departure, arrival), group in valid.groupby(
        ["gare_depart", "gare_arrivee"]
    ):
        planned = group["nb_train_prevu"].sum()
        cancelled = group["nb_annulation"].sum()

        rates = {
            "cancellation": float(cancelled / planned),
        }

        # NB: keep valid cancellations even if the delay counter is missing
        operated = group["nb_train_prevu"] - group["nb_annulation"]
        valid_delays = group.loc[
            group[ARRIVAL_DELAY_COUNT].ge(0)
            & group[ARRIVAL_DELAY_COUNT].le(operated)
        ]

        if not valid_delays.empty:
            planned = valid_delays["nb_train_prevu"].sum()
            cancelled = valid_delays["nb_annulation"].sum()
            delayed = valid_delays[ARRIVAL_DELAY_COUNT].sum()

            rates["disruption"] = float(
                (delayed + cancelled) / planned
            )

            if planned > cancelled:
                rates["delay"] = float(delayed / (planned - cancelled))

        result[departure, arrival] = rates

    return result

@st.cache_data(show_spinner=False)
def load_map_rates(
    data: pd.DataFrame,
) -> dict[tuple[str, str], dict[str, float]]:
    """Cache the map rates computed from the already cleaned dataset."""
    return aggregate_map_rates(data)
