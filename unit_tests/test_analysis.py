
"""Unit tests for the ``ia700_project.analysis`` module."""

import pandas as pd
import pytest

from ia700_project import analysis


ROUTE_LYON = "PARIS LYON → MARSEILLE"
ROUTE_LILLE = "LILLE → PARIS NORD"


@pytest.fixture
def df_trains() -> pd.DataFrame:
    """Minimal dataset: 2 routes observed over 2 months."""
    return pd.DataFrame(
        {
            analysis.COL_DATE: [
                "2024-01", "2024-02", "2024-01", "2024-02"
            ],
            analysis.COL_DEPARTURE: [
                "PARIS LYON", "PARIS LYON", "LILLE", "LILLE"
            ],
            analysis.COL_ARRIVAL: [
                "MARSEILLE", "MARSEILLE", "PARIS NORD", "PARIS NORD"
            ],
            analysis.COL_SCHEDULED: [100, 100, 50, 50],
            analysis.COL_CANCELLED: [10, 0, 0, 0],
            analysis.COL_ARRIVAL_DELAY: [6.0, 4.0, 2.0, 2.0],
            analysis.COL_DELAYED_15: [20, 10, 5, 5],
        }
    )


def make_causes_df(rows: list[dict]) -> pd.DataFrame:
    """Build a delay causes dataset (unspecified columns are filled with 0)."""
    columns = [
        analysis.COL_DATE,
        analysis.COL_NB_ARRIVAL_DELAYS,
        *analysis.CAUSE_COLUMNS,
    ]
    return pd.DataFrame(rows, columns=columns).fillna(0)


# --- check_columns ---------------------------------------------------------


def test_check_columns_valid():
    """No error is raised when all required columns are present."""
    df = pd.DataFrame({"Date": ["2024-01"], "Value": [10]})
    analysis.check_columns(df, ["Date", "Value"])


def test_check_columns_missing():
    """Missing columns raise MissingColumnsError."""
    df = pd.DataFrame({"Date": ["2024-01"]})

    with pytest.raises(analysis.MissingColumnsError, match="Missing columns"):
        analysis.check_columns(df, ["Date", "Value"])


# --- load_data -------------------------------------------------------------


def test_load_data_reads_semicolon_csv(tmp_path):
    """The CSV is read using the semicolon separator."""
    csv_file = tmp_path / "data.csv"
    csv_file.write_text(
        "Date;Departure station\n2024-01;PARIS LYON\n",
        encoding="utf-8",
    )

    df = analysis.load_data(str(csv_file))

    assert df.shape == (1, 2)
    assert df.loc[0, "Departure station"] == "PARIS LYON"


def test_load_data_missing_file(tmp_path):
    """A missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        analysis.load_data(tmp_path / "absent.csv")


# --- add_route_column ------------------------------------------------------


def test_add_route_column(df_trains):
    """The route column concatenates departure and arrival stations."""
    result = analysis.add_route_column(df_trains)

    assert result[analysis.COL_ROUTE].tolist() == [
        ROUTE_LYON,
        ROUTE_LYON,
        ROUTE_LILLE,
        ROUTE_LILLE,
    ]


def test_add_route_column_keeps_original_untouched(df_trains):
    """The original dataset is not modified."""
    analysis.add_route_column(df_trains)

    assert analysis.COL_ROUTE not in df_trains.columns


def test_add_route_column_missing_column(df_trains):
    """Missing station columns raise MissingColumnsError."""
    incomplete = df_trains.drop(
        columns=[analysis.COL_DEPARTURE]
    )

    with pytest.raises(analysis.MissingColumnsError):
        analysis.add_route_column(incomplete)


# --- compute_route_stats ---------------------------------------------------


def test_compute_route_stats_values(df_trains):
    """Route reliability indicators are correctly computed."""
    stats = analysis.compute_route_stats(
        df_trains, min_months=1, min_trains=1
    )
    row = stats.loc[ROUTE_LYON]

    assert row["months"] == 2
    assert row["services"] == 200
    assert row["arrival_delay"] == pytest.approx(5.0)
    assert row["delay_rate_15"] == pytest.approx(15.0)
    assert row["cancellation_rate"] == pytest.approx(5.0)


def test_compute_route_stats_filters_small_routes(df_trains):
    """Routes with too few scheduled services are excluded."""
    stats = analysis.compute_route_stats(
        df_trains, min_months=2, min_trains=150
    )

    assert stats.index.tolist() == [ROUTE_LYON]


def test_compute_route_stats_without_trains_gives_nan(df_trains):
    """Rates are NaN when no services are scheduled."""
    df_trains[analysis.COL_SCHEDULED] = 0

    stats = analysis.compute_route_stats(
        df_trains, min_months=1, min_trains=0
    )

    assert stats["delay_rate_15"].isna().all()
    assert stats["cancellation_rate"].isna().all()


def test_compute_route_stats_missing_column(df_trains):
    """A missing column raises MissingColumnsError."""
    incomplete = df_trains.drop(
        columns=[analysis.COL_CANCELLED]
    )

    with pytest.raises(
        analysis.MissingColumnsError, match="Missing columns"
    ):
        analysis.compute_route_stats(incomplete)


# --- season_of -------------------------------------------------------------


@pytest.mark.parametrize(
    ("month", "expected"),
    [
        (12, "Winter"),
        (1, "Winter"),
        (4, "Spring"),
        (7, "Summer"),
        (10, "Autumn"),
    ],
)
def test_season_of(month, expected):
    """Each month is associated with the correct season."""
    assert analysis.season_of(month) == expected


@pytest.mark.parametrize("month", [0, 13, -1])
def test_season_of_invalid_month(month):
    """An invalid month number raises ValueError."""
    with pytest.raises(ValueError, match="Invalid month"):
        analysis.season_of(month)


# --- seasonal_cause_shares -------------------------------------------------


def test_seasonal_cause_shares_weighted_average():
    """The average is weighted by delayed trains and sums to 100."""
    external, infrastructure = list(analysis.CAUSE_COLUMNS)[:2]

    date = analysis.COL_DATE
    nb = analysis.COL_NB_ARRIVAL_DELAYS

    df = make_causes_df(
        [
            {date: "2024-01", nb: 10, external: 100.0},
            {date: "2024-01", nb: 30, infrastructure: 100.0},
        ]
    )

    shares = analysis.seasonal_cause_shares(df)

    assert shares.loc["Winter", "External causes"] == pytest.approx(25.0)
    assert shares.loc["Winter", "Infrastructure"] == pytest.approx(75.0)
    assert shares.loc["Winter"].sum() == pytest.approx(100.0)


def test_seasonal_cause_shares_absent_season_is_nan():
    """A season with no data returns a row of NaN values."""
    external = list(analysis.CAUSE_COLUMNS)[0]

    date = analysis.COL_DATE
    nb = analysis.COL_NB_ARRIVAL_DELAYS

    df = make_causes_df(
        [{date: "2024-01", nb: 10, external: 100.0}]
    )

    shares = analysis.seasonal_cause_shares(df)

    assert shares.index.tolist() == analysis.SEASON_ORDER
    assert shares.loc["Summer"].isna().all()


def test_seasonal_cause_shares_ignores_negative_counts():
    """Negative delayed train counts are treated as zero."""
    external, infrastructure = list(analysis.CAUSE_COLUMNS)[:2]

    date = analysis.COL_DATE
    nb = analysis.COL_NB_ARRIVAL_DELAYS

    df = make_causes_df(
        [
            {date: "2024-01", nb: 10, external: 100.0},
            {date: "2024-01", nb: -5, infrastructure: 100.0},
        ]
    )

    shares = analysis.seasonal_cause_shares(df)

    assert shares.loc["Winter", "External causes"] == pytest.approx(100.0)
    assert shares.loc["Winter", "Infrastructure"] == pytest.approx(0.0)


def test_seasonal_cause_shares_missing_column():
    """A missing cause column raises MissingColumnsError."""
    df = pd.DataFrame(
        {analysis.COL_DATE: ["2024-01"]}
    )

    with pytest.raises(analysis.MissingColumnsError):
        analysis.seasonal_cause_shares(df)
