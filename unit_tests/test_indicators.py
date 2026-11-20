"""Unit tests for the indicators module."""

from datetime import date

import pandas as pd
import pytest

from ia700_project.indicators import (
    avg_delay_length,
    cancellation_rate,
    cause_of_delays_ranking,
    comparison_time_chart,
    compute_overview_summary,
    delay_rate,
    ranking,
    scheduled_trains_count,
    time_chart,
)
from ia700_project.models import ComparisonSelection, TravelSelection

CAUSE_COLUMNS = [
    "prct_cause_externe",
    "prct_cause_infra",
    "prct_cause_gestion_trafic",
    "prct_cause_materiel_roulant",
    "prct_cause_gestion_gare",
    "prct_cause_prise_en_charge_voyageurs",
]


def make_data():
    """Create a representative monthly directional dataset."""
    return pd.DataFrame(
        {
            "gare_depart": [
                "PARIS LYON",
                "PARIS LYON",
                "PARIS LYON",
                "LYON PART DIEU",
            ],
            "gare_arrivee": [
                "LYON PART DIEU",
                "LYON PART DIEU",
                "LYON PART DIEU",
                "PARIS LYON",
            ],
            "date": pd.to_datetime(
                [
                    "2024-01-01",
                    "2024-02-01",
                    "2024-03-01",
                    "2024-01-01",
                ]
            ),
            "nb_train_prevu": [100, 100, 100, 50],
            "nb_annulation": [10, 0, 0, 5],
            "nb_train_retard_arrivee": [18, 20, 10, 5],
            "retard_moyen_arrivee": [30.0, 40.0, 20.0, 15.0],
            CAUSE_COLUMNS[0]: [40.0, 30.0, 40.0, 40.0],
            CAUSE_COLUMNS[1]: [20.0, 20.0, 20.0, 20.0],
            CAUSE_COLUMNS[2]: [10.0, 10.0, 10.0, 10.0],
            CAUSE_COLUMNS[3]: [10.0, 15.0, 10.0, 10.0],
            CAUSE_COLUMNS[4]: [10.0, 15.0, 10.0, 10.0],
            CAUSE_COLUMNS[5]: [10.0, 10.0, 10.0, 10.0],
        }
    )


def travel_selection(
    start=date(2025, 1, 10),
    end=date(2025, 1, 20),
):
    """Select the Paris–Lyon route and a date range in winter."""
    return TravelSelection(
        departure="PARIS LYON",
        arrival="LYON PART DIEU",
        travel_start=start,
        travel_end=end,
    )


def comparison_selection(
    entity="Liaisons",
    metric="Taux d’annulation",
    top_n=10,
    min_volume=0,
):
    """Create a comparison selection."""
    return ComparisonSelection(
        entity=entity,
        metric=metric,
        top_n=top_n,
        min_volume=min_volume,
    )


# ---------------------------------------------------------------------
# Overview summary
# ---------------------------------------------------------------------


def test_compute_overview_summary_returns_empty_dataframe():
    """Return an empty dataframe with the expected columns for empty data."""
    data = pd.DataFrame(columns=["gare_depart", "gare_arrivee", "date"])

    result = compute_overview_summary(data)

    assert result.empty
    assert list(result.columns) == [
        "route_count",
        "station_count",
        "latest_month",
    ]


def test_compute_overview_summary_counts_routes_and_stations():
    """The function should count unique routes and stations."""
    data = pd.DataFrame(
        {
            "gare_depart": [
                "PARIS LYON",
                "PARIS LYON",
                "LYON PART DIEU",
                "MARSEILLE",
            ],
            "gare_arrivee": [
                "LYON PART DIEU",
                "LYON PART DIEU",
                "PARIS LYON",
                "PARIS LYON",
            ],
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-02-01",
                    "2025-03-01",
                    "2025-04-01",
                ]
            ),
        }
    )

    result = compute_overview_summary(data)

    assert result.loc[0, "route_count"] == 3
    assert result.loc[0, "station_count"] == 3
    assert result.loc[0, "latest_month"] == pd.Timestamp("2025-04-01")


def test_compute_overview_summary_ignores_incomplete_routes():
    """Routes with missing departure or arrival should not be counted."""
    data = pd.DataFrame(
        {
            "gare_depart": ["PARIS LYON", None, "MARSEILLE"],
            "gare_arrivee": ["LYON PART DIEU", "PARIS LYON", None],
            "date": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
        }
    )

    result = compute_overview_summary(data)

    assert result.loc[0, "route_count"] == 1
    assert result.loc[0, "station_count"] == 3


def test_compute_overview_summary_counts_reverse_routes_separately():
    """A route in the reverse direction should count as a distinct route."""
    data = pd.DataFrame(
        {
            "gare_depart": ["PARIS LYON", "LYON PART DIEU"],
            "gare_arrivee": ["LYON PART DIEU", "PARIS LYON"],
            "date": pd.to_datetime(["2025-01-01", "2025-02-01"]),
        }
    )

    result = compute_overview_summary(data)

    assert result.loc[0, "route_count"] == 2
    assert result.loc[0, "station_count"] == 2


# ---------------------------------------------------------------------
# Exploration indicators
# ---------------------------------------------------------------------


def test_scheduled_trains_count_uses_matching_historical_seasons():
    """A winter selection includes historical January and February rows."""
    result = scheduled_trains_count(make_data(), travel_selection())

    assert result == 200


def test_scheduled_trains_count_returns_none_without_matching_route():
    """Return None when the selected route has no observations."""
    selection = TravelSelection(
        departure="BORDEAUX",
        arrival="MARSEILLE",
        travel_start=date(2025, 1, 1),
        travel_end=date(2025, 1, 31),
    )

    assert scheduled_trains_count(make_data(), selection) is None


def test_scheduled_trains_count_returns_none_for_reversed_dates():
    """Return None when the selected date range is invalid."""
    selection = travel_selection(
        start=date(2025, 2, 1),
        end=date(2025, 1, 1),
    )

    assert scheduled_trains_count(make_data(), selection) is None


def test_cancellation_rate_uses_scheduled_train_denominator():
    """Cancellation rate is calculated from summed cancellation counts."""
    result = cancellation_rate(make_data(), travel_selection())

    assert result == pytest.approx(5.0)


def test_delay_rate_uses_operated_train_denominator():
    """Delay rate excludes cancelled trains from its denominator."""
    result = delay_rate(make_data(), travel_selection())

    assert result == pytest.approx(20.0)


def test_avg_delay_length_is_weighted_by_delayed_train_count():
    """Average delay is weighted by the number of delayed trains."""
    result = avg_delay_length(make_data(), travel_selection())

    expected = (18 * 30 + 20 * 40) / 38
    assert result == pytest.approx(expected)


def test_rates_return_none_when_no_valid_observations():
    """Invalid counters should not contribute to indicator calculations."""
    data = make_data()
    data["nb_train_prevu"] = 0

    selection = travel_selection()

    assert cancellation_rate(data, selection) is None
    assert delay_rate(data, selection) is None
    assert avg_delay_length(data, selection) is None


def test_cancellation_rate_ignores_invalid_cancellation_counts():
    """Cancellation counts greater than scheduled trains are ignored."""
    data = make_data()
    data.loc[0, "nb_annulation"] = 101

    result = cancellation_rate(data, travel_selection())

    assert result == pytest.approx(0.0)


def test_delay_rate_ignores_invalid_delay_counts():
    """Delayed counts greater than operated trains are ignored."""
    data = make_data()
    data.loc[0, "nb_train_retard_arrivee"] = 200

    result = delay_rate(data, travel_selection())

    assert result == pytest.approx(20 / 100 * 100)


def test_avg_delay_length_returns_none_without_delayed_trains():
    """Return None when no valid delayed train has a known average delay."""
    data = make_data()
    data["nb_train_retard_arrivee"] = 0

    assert avg_delay_length(data, travel_selection()) is None


def test_time_chart_returns_full_monthly_route_history():
    """The chart includes all historical months, not only selected seasons."""
    result = time_chart(make_data(), travel_selection())

    assert result is not None
    assert list(result.columns) == [
        "month",
        "cancellation_rate_pct",
        "arrival_delay_rate_pct",
        "mean_arrival_delay_minutes",
    ]
    assert len(result) == 3
    assert result["month"].tolist() == list(
        pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"])
    )


def test_time_chart_returns_none_without_matching_route():
    """Return None when the selected route has no historical data."""
    selection = TravelSelection(
        departure="BORDEAUX",
        arrival="MARSEILLE",
        travel_start=date(2025, 1, 1),
        travel_end=date(2025, 1, 31),
    )

    assert time_chart(make_data(), selection) is None


def test_time_chart_returns_none_when_all_dates_are_invalid():
    """Return None when all route dates cannot be converted."""
    data = make_data()
    data["date"] = "not-a-date"

    assert time_chart(data, travel_selection()) is None


def test_cause_of_delays_ranking_weights_monthly_percentages():
    """Cause percentages are weighted by each month's delayed train count."""
    result = cause_of_delays_ranking(make_data(), travel_selection())

    assert result is not None
    assert list(result.columns) == ["cause", "percentage"]
    assert result.iloc[0]["cause"] == "Causes externes"
    assert result.iloc[0]["percentage"] == pytest.approx(
        (18 * 40 + 20 * 30) / 38
    )


def test_cause_of_delays_ranking_returns_none_without_cause_columns():
    """Return None if the dataset does not contain all cause columns."""
    data = make_data().drop(columns=CAUSE_COLUMNS)

    assert cause_of_delays_ranking(data, travel_selection()) is None


def test_cause_of_delays_ranking_returns_none_for_invalid_breakdowns():
    """Cause breakdowns outside the accepted percentage range are ignored."""
    data = make_data()
    data.loc[0, CAUSE_COLUMNS] = [10, 10, 10, 10, 10, 10]
    data.loc[1, CAUSE_COLUMNS] = [10, 10, 10, 10, 10, 10]

    assert cause_of_delays_ranking(data, travel_selection()) is None


# ---------------------------------------------------------------------
# Comparison indicators
# ---------------------------------------------------------------------


def test_ranking_returns_directional_route_ranking():
    """Rank directional routes from highest to lowest indicator value."""
    result = ranking(
        make_data(),
        comparison_selection(metric="Taux d’annulation"),
    )

    assert result is not None
    assert list(result.columns) == [
        "rank",
        "entity",
        "value",
        "scheduled_train_count",
    ]
    assert list(result["entity"]) == [
        "LYON PART DIEU → PARIS LYON",
        "PARIS LYON → LYON PART DIEU",
    ]
    assert list(result["value"]) == pytest.approx(
        [5 / 50 * 100, 10 / 300 * 100]
    )
    assert result.iloc[0]["rank"] == 1


def test_ranking_can_group_by_departure_station():
    """Station rankings use the selected station column."""
    result = ranking(
        make_data(),
        comparison_selection(entity="Gares de départ"),
    )

    assert result is not None
    assert set(result["entity"]) == {"PARIS LYON", "LYON PART DIEU"}


def test_ranking_supports_delay_and_average_delay_metrics():
    """The two other comparison metrics can be calculated."""
    data = make_data()

    delay_result = ranking(
        data,
        comparison_selection(metric="Taux de retard à l’arrivée"),
    )
    average_result = ranking(
        data,
        comparison_selection(metric="Retard moyen à l’arrivée"),
    )

    assert delay_result is not None
    assert average_result is not None
    assert not delay_result.empty
    assert not average_result.empty


def test_ranking_applies_minimum_volume_and_top_n():
    """Only entities meeting the volume threshold are returned."""
    result = ranking(
        make_data(),
        comparison_selection(top_n=1, min_volume=150),
    )

    assert result is not None
    assert len(result) == 1
    assert result.iloc[0]["scheduled_train_count"] == 300


def test_ranking_returns_empty_dataframe_when_no_entity_meets_threshold():
    """Return the expected empty ranking structure when no entity qualifies."""
    result = ranking(
        make_data(),
        comparison_selection(min_volume=1000),
    )

    assert result is not None
    assert result.empty
    assert list(result.columns) == [
        "rank",
        "entity",
        "value",
        "scheduled_train_count",
    ]


def test_ranking_returns_empty_dataframe_when_top_n_is_zero():
    """A non-positive top_n produces an empty ranking."""
    result = ranking(
        make_data(),
        comparison_selection(top_n=0),
    )

    assert result is not None
    assert result.empty


def test_ranking_returns_none_for_empty_data():
    """Return None when the input dataframe is empty."""
    assert (
        ranking(
            pd.DataFrame(),
            comparison_selection(),
        )
        is None
    )


def test_ranking_returns_none_when_no_services_are_valid():
    """Return None when no row has a positive scheduled train count."""
    data = make_data()
    data["nb_train_prevu"] = 0

    assert ranking(data, comparison_selection()) is None


@pytest.mark.parametrize(
    ("entity", "metric", "message"),
    [
        ("Unknown entity", "Taux d’annulation", "Unknown comparison entity"),
        ("Liaisons", "Unknown metric", "Unknown comparison metric"),
    ],
)
def test_ranking_rejects_unknown_selection_values(entity, metric, message):
    """Unknown entity and metric labels raise ValueError."""
    with pytest.raises(ValueError, match=message):
        ranking(
            make_data(),
            comparison_selection(entity=entity, metric=metric),
        )


def test_comparison_time_chart_returns_monthly_values_for_ranked_entities():
    """Return monthly values only for entities present in the ranking."""
    data = make_data()
    selected = comparison_selection()
    ranked = ranking(data, selected)

    result = comparison_time_chart(data, selected, ranked)

    assert result is not None
    assert list(result.columns) == ["month", "entity", "value"]
    assert set(result["entity"]) == set(ranked["entity"])
    assert len(result) == 4


def test_comparison_time_chart_returns_none_without_ranking_data():
    """Return None when no ranking is provided."""
    assert (
        comparison_time_chart(
            make_data(),
            comparison_selection(),
            pd.DataFrame(),
        )
        is None
    )


def test_comparison_time_chart_returns_none_when_no_services_are_valid():
    """Return None when the dataset contains no valid scheduled services."""
    data = make_data()
    data["nb_train_prevu"] = 0
    ranked = pd.DataFrame({"entity": ["PARIS LYON → LYON PART DIEU"]})

    assert (
        comparison_time_chart(
            data,
            comparison_selection(),
            ranked,
        )
        is None
    )


def test_comparison_time_chart_returns_none_when_no_entities_match():
    """Return None when none of the ranked entities occur in the data."""
    ranked = pd.DataFrame({"entity": ["UNKNOWN ROUTE"]})

    assert (
        comparison_time_chart(
            make_data(),
            comparison_selection(),
            ranked,
        )
        is None
    )


@pytest.mark.parametrize(
    ("entity", "metric", "message"),
    [
        ("Unknown entity", "Taux d’annulation", "Unknown comparison entity"),
        ("Liaisons", "Unknown metric", "Unknown comparison metric"),
    ],
)
def test_comparison_time_chart_rejects_unknown_selection_values(
    entity, metric, message
):
    """Unknown entity and metric labels raise ValueError."""
    with pytest.raises(ValueError, match=message):
        comparison_time_chart(
            make_data(),
            comparison_selection(entity=entity, metric=metric),
            pd.DataFrame({"entity": ["PARIS LYON → LYON PART DIEU"]}),
        )
