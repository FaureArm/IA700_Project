"""Compute the indicators displayed by the TGV reliability dashboards.

The input is the monthly, directional SNCF dataset returned by
``clean_dataset``. Rates are percentages (0–100).
"""

import pandas as pd

from ia700_project.models import ComparisonSelection, TravelSelection

# A route is directional: A -> B and B -> A are different entities.
_DELAY_COUNT = "nb_train_retard_arrivee"
_AVG_DELAY = "retard_moyen_arrivee"

_CAUSES = {
    "prct_cause_externe": "Causes externes",
    "prct_cause_infra": "Infrastructure",
    "prct_cause_gestion_trafic": "Gestion du trafic",
    "prct_cause_materiel_roulant": "Matériel roulant",
    "prct_cause_gestion_gare": "Gestion en gare",
    "prct_cause_prise_en_charge_voyageurs": "Voyageurs / affluence",
}

_ENTITY_COLUMNS = {
    "Liaisons": None,
    "Gares de départ": "gare_depart",
    "Gares d’arrivée": "gare_arrivee",
}
_METRICS = {
    "Taux d’annulation": "cancellation",
    "Taux de retard à l’arrivée": "delay",
    "Retard moyen à l’arrivée": "average_delay",
}

_MONTHLY_COLUMNS = [
    "month",
    "cancellation_rate_pct",
    "arrival_delay_rate_pct",
    "mean_arrival_delay_minutes",
]
_RANKING_COLUMNS = ["rank", "entity", "value", "scheduled_train_count"]
_COMPARISON_COLUMNS = ["month", "entity", "value"]


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


### Shared helpers ###


def _valid_services(data: pd.DataFrame) -> pd.DataFrame:
    """Keep observations with a positive number of scheduled trains."""
    return data.loc[data["nb_train_prevu"].gt(0)].copy()


def _valid_cancellations(data: pd.DataFrame) -> pd.DataFrame:
    """Keep observations with meaningful cancellation counts."""
    return data.loc[
        data["nb_annulation"].ge(0)
        & data["nb_annulation"].le(data["nb_train_prevu"])
    ]


def _valid_delays(data: pd.DataFrame) -> pd.DataFrame:
    """Keep observations with a valid count of delayed operated trains."""
    operated = data["nb_train_prevu"] - data["nb_annulation"]
    return data.loc[
        data["nb_annulation"].ge(0)
        & operated.gt(0)
        & data[_DELAY_COUNT].ge(0)
        & data[_DELAY_COUNT].le(operated)
    ]


def _percentage(numerator: pd.Series, denominator: pd.Series) -> float | None:
    """Return the percentage of summed counts, None if undefined."""
    total_denominator = denominator.sum(min_count=1)
    if pd.isna(total_denominator) or total_denominator <= 0:
        return None
    total_numerator = numerator.sum(min_count=1)
    if pd.isna(total_numerator):
        return None
    return float(100 * total_numerator / total_denominator)


def _cancellation_pct(data: pd.DataFrame) -> float | None:
    """Divide cancelled trains by scheduled trains."""
    valid = _valid_cancellations(_valid_services(data))
    return _percentage(valid["nb_annulation"], valid["nb_train_prevu"])


def _delay_pct(data: pd.DataFrame) -> float | None:
    """Divide late arrivals by operated trains (not scheduled trains)."""
    valid = _valid_delays(_valid_services(data))
    operated = valid["nb_train_prevu"] - valid["nb_annulation"]
    return _percentage(valid[_DELAY_COUNT], operated)


def _average_delay(data: pd.DataFrame) -> float | None:
    """Weight mean delay of late trains by their number per month."""
    valid = _valid_delays(_valid_services(data))
    valid = valid.loc[valid[_DELAY_COUNT].gt(0) & valid[_AVG_DELAY].notna()]
    if valid.empty:
        return None
    weights = valid[_DELAY_COUNT]
    return float((valid[_AVG_DELAY] * weights).sum() / weights.sum())


def _select_route(
    data: pd.DataFrame, selection: TravelSelection
) -> pd.DataFrame:
    """Return the observations for the selected directed route."""
    return data.loc[
        data["gare_depart"].eq(selection.departure)
        & data["gare_arrivee"].eq(selection.arrival)
    ].copy()


def _season_months(selection: TravelSelection) -> set[int]:
    """Return all months in seasons touched by the travel date range.

    Winter spans December–February. The selection is interpreted as a
    seasonal analogue, so historical observations from *all years* are
    used for the journey summary rather than filtering by travel year.
    """
    if selection.travel_start > selection.travel_end:
        return set()

    months = pd.period_range(
        selection.travel_start, selection.travel_end, freq="M"
    ).month
    seasons = (
        {12, 1, 2},
        {3, 4, 5},
        {6, 7, 8},
        {9, 10, 11},
    )
    return set().union(*(s for s in seasons if any(m in s for m in months)))


def _seasonal_route(
    data: pd.DataFrame, selection: TravelSelection
) -> pd.DataFrame:
    """Filter the selected route to the matching historical seasons."""
    months = _season_months(selection)
    route = _select_route(data, selection)
    if not months or route.empty:
        return route.iloc[0:0]
    observed_months = pd.to_datetime(route["date"], errors="coerce").dt.month
    return route.loc[observed_months.isin(months)]


def _metric(data: pd.DataFrame, metric: str) -> float | None:
    """Evaluate one of the metrics exposed by the comparison sidebar."""
    kind = _METRICS[metric]
    if kind == "cancellation":
        return _cancellation_pct(data)
    if kind == "delay":
        return _delay_pct(data)
    return _average_delay(data)


def _entities(data: pd.DataFrame, entity: str) -> pd.Series:
    """Produce matching route/station labels for comparison grouping."""
    column = _ENTITY_COLUMNS[entity]
    if column is not None:
        return data[column]
    return data["gare_depart"] + " → " + data["gare_arrivee"]


### Exploration Page ###


def scheduled_trains_count(
    data: pd.DataFrame, selection: TravelSelection
) -> int | None:
    """Return scheduled trains in historically corresponding seasons.

    Returns None if the chosen route/season has no observed months;
    otherwise, zero-scheduled months contribute zero trains.
    """
    route = _seasonal_route(data, selection)
    if route.empty:
        return None
    return int(route["nb_train_prevu"].sum())


def cancellation_rate(
    data: pd.DataFrame, selection: TravelSelection
) -> float | None:
    """Return cancellations as a percentage of scheduled trains."""
    return _cancellation_pct(_seasonal_route(data, selection))


def delay_rate(data: pd.DataFrame, selection: TravelSelection) -> float | None:
    """Return late arrivals as a percentage of operated trains.

    SNCF's ``nb_train_retard_arrivee`` uses its journey-duration-based
    composite punctuality threshold, rather than a fixed 15 minutes.
    """
    return _delay_pct(_seasonal_route(data, selection))


def avg_delay_length(
    data: pd.DataFrame, selection: TravelSelection
) -> float | None:
    """Return the train-weighted mean delay among late arrivals.

    Monthly ``retard_moyen_arrivee`` values are weighted by the count
    ``nb_train_retard_arrivee``. Rows without a defined mean are omitted.
    """
    return _average_delay(_seasonal_route(data, selection))


def time_chart(
    data: pd.DataFrame, selection: TravelSelection
) -> pd.DataFrame | None:
    """Return full monthly history for a selected directional route.

    The selected dates choose seasons for the summary, not the chart.
    Output columns are ``month``, ``cancellation_rate_pct``,
    ``arrival_delay_rate_pct``, and ``mean_arrival_delay_minutes``.
    """
    route = _valid_services(_select_route(data, selection))
    if route.empty:
        return None

    route["month"] = (
        pd.to_datetime(route["date"], errors="coerce")
        .dt.to_period("M")
        .dt.to_timestamp()
    )
    route = route.dropna(subset=["month"])
    if route.empty:
        return None

    records = []
    for month, group in route.groupby("month", sort=True):
        records.append(
            {
                "month": month,
                "cancellation_rate_pct": _cancellation_pct(group),
                "arrival_delay_rate_pct": _delay_pct(group),
                "mean_arrival_delay_minutes": _average_delay(group),
            }
        )
    return pd.DataFrame(records, columns=_MONTHLY_COLUMNS)


def cause_of_delays_ranking(
    data: pd.DataFrame, selection: TravelSelection
) -> pd.DataFrame | None:
    """Rank causes by their estimated share of delayed trains.

    Use valid cause breakdowns only (at least 90% reported and at most
    100.1%, in line with the cleaning datasheet). Monthly percentages
    are weighted by delayed-train counts; they are not renormalized.
    Output columns: ``cause``, ``percentage`` (in percentage points).
    """
    route = _seasonal_route(data, selection)
    if route.empty or not set(_CAUSES).issubset(route.columns):
        return None
    causes = list(_CAUSES)
    totals = route[causes].sum(axis=1, min_count=1)
    valid = route.loc[route[_DELAY_COUNT].gt(0) & totals.between(90, 100.1)]
    if valid.empty:
        return None

    weights = valid[_DELAY_COUNT]
    total_weight = weights.sum()
    if total_weight <= 0:
        return None

    # The source columns are already percentages: a weighted mean is
    # directly expressed in percentage points.
    weighted_shares = (
        valid[causes].fillna(0).mul(weights, axis=0).sum() / total_weight
    )

    return (
        pd.DataFrame(
            {
                "cause": [_CAUSES[col] for col in causes],
                "percentage": [float(weighted_shares[col]) for col in causes],
            }
        )
        .sort_values(["percentage", "cause"], ascending=[False, True])
        .reset_index(drop=True)
    )


### Comparison Page ###


def ranking(
    data: pd.DataFrame, selection: ComparisonSelection
) -> pd.DataFrame | None:
    """Rank routes or stations from best (lowest) to worst indicator.

    ``min_volume`` applies to scheduled services for each entity over
    the full historical dataset. Rates are calculated from summed
    counters, never as unweighted means of monthly percentages.
    Output columns: rank, entity, value, scheduled_train_count.
    """
    # Explicitly validate labels before attempting aggregation.
    if selection.entity not in _ENTITY_COLUMNS:
        raise ValueError(f"Unknown comparison entity: {selection.entity}")
    if selection.metric not in _METRICS:
        raise ValueError(f"Unknown comparison metric: {selection.metric}")

    if data.empty:
        return None
    valid = _valid_services(data)
    if valid.empty:
        return None

    valid = valid.assign(entity=_entities(valid, selection.entity))
    valid = valid.dropna(subset=["entity"])
    if valid.empty:
        return None

    records = []
    for name, group in valid.groupby("entity", sort=True):
        volume = int(group["nb_train_prevu"].sum())
        if volume < selection.min_volume:
            continue
        value = _metric(group, selection.metric)
        if value is not None and pd.notna(value):
            records.append(
                {
                    "entity": str(name),
                    "value": value,
                    "scheduled_train_count": volume,
                }
            )

    if not records or selection.top_n <= 0:
        return pd.DataFrame(columns=_RANKING_COLUMNS)

    result = (
        pd.DataFrame(records)
        .sort_values(["value", "entity"], ascending=[True, True])
        .head(selection.top_n)
        .reset_index(drop=True)
    )
    result.insert(0, "rank", range(1, len(result) + 1))
    return result[_RANKING_COLUMNS]


def comparison_time_chart(
    data: pd.DataFrame,
    selection: ComparisonSelection,
    ranking_data: pd.DataFrame,
) -> pd.DataFrame | None:
    """Return monthly indicator values for the ranked entities.

    Only entities present in ``ranking_data`` are included. Each month
    is recomputed from that month's counts (or weighted mean delays),
    not from the full-period ranking value. Output: month, entity, value.
    """
    if selection.entity not in _ENTITY_COLUMNS:
        raise ValueError(f"Unknown comparison entity: {selection.entity}")
    if selection.metric not in _METRICS:
        raise ValueError(f"Unknown comparison metric: {selection.metric}")
    if ranking_data is None or ranking_data.empty:
        return None

    valid = _valid_services(data)
    if valid.empty:
        return None
    valid["entity"] = _entities(valid, selection.entity)
    valid = valid.loc[valid["entity"].isin(ranking_data["entity"])]
    valid["month"] = (
        pd.to_datetime(valid["date"], errors="coerce")
        .dt.to_period("M")
        .dt.to_timestamp()
    )
    valid = valid.dropna(subset=["month", "entity"])
    if valid.empty:
        return None

    records = []
    for (month, name), group in valid.groupby(["month", "entity"], sort=True):
        value = _metric(group, selection.metric)
        if value is not None and pd.notna(value):
            records.append({"month": month, "entity": name, "value": value})

    if not records:
        return None
    return pd.DataFrame(records, columns=_COMPARISON_COLUMNS)
