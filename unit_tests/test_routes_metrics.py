"""Unit tests for the ``ia700_project.routes_metrics`` module."""

import pandas as pd
import pytest

from ia700_project import routes_metrics


@pytest.fixture
def df_trains(tmp_path):
    """Create a minimal cleaned dataset covering several seasons."""
    df = pd.DataFrame(
        {
            "date": [
                "2024-01-15",
                "2024-02-15",
                "2024-04-15",
                "2024-07-15",
                "2024-10-15",
                "2024-01-15",
            ],
            "gare_depart": [
                "PARIS LYON",
                "PARIS LYON",
                "PARIS LYON",
                "PARIS LYON",
                "PARIS LYON",
                "LILLE",
            ],
            "gare_arrivee": [
                "MARSEILLE",
                "MARSEILLE",
                "MARSEILLE",
                "MARSEILLE",
                "MARSEILLE",
                "PARIS NORD",
            ],
            "nb_train_prevu": [100, 100, 100, 100, 100, 50],
            "nb_annulation": [10, 0, 5, 10, 0, 5],
            "nb_train_retard_arrivee": [20, 10, 15, 20, 10, 5],
        }
    )

    csv_file = tmp_path / "cleaned_data.csv"
    df.to_csv(csv_file, sep=";", index=False)

    return csv_file


# --- creer_csv_metriques ---------------------------------------------------


def test_creer_csv_metriques_returns_dataframe(df_trains):
    """The function returns a pandas DataFrame."""
    result = routes_metrics.creer_csv_metriques(df_trains)

    assert isinstance(result, pd.DataFrame)
    assert not result.empty


def test_creer_csv_metriques_creates_route_column(df_trains):
    """Departure and arrival stations are combined into a route label."""
    result = routes_metrics.creer_csv_metriques(df_trains)

    routes = result["Liaison"].tolist()

    assert "PARIS LYON -> MARSEILLE" in routes
    assert "LILLE -> PARIS NORD" in routes


def test_creer_csv_metriques_assigns_seasons(df_trains):
    """Each month is correctly assigned to its corresponding season."""
    result = routes_metrics.creer_csv_metriques(df_trains)

    seasons = result["Saison"].tolist()

    assert set(seasons) == {
        "Hiver",
        "Printemps",
        "Été",
        "Automne",
    }


def test_creer_csv_metriques_aggregates_values(df_trains):
    """Train counts are correctly aggregated by route and season."""
    result = routes_metrics.creer_csv_metriques(df_trains)

    winter = result[
        (result["Liaison"] == "PARIS LYON -> MARSEILLE")
        & (result["Saison"] == "Hiver")
    ].iloc[0]

    assert winter["Nombre de circulations prévues"] == 200
    assert winter["Nombre de trains annulés"] == 10
    assert winter["Nombre de trains en retard à l'arrivée"] == 30


def test_creer_csv_metriques_calculates_operated_trains(df_trains):
    """The number of operated trains is correctly calculated."""
    result = routes_metrics.creer_csv_metriques(df_trains)

    winter = result[
        (result["Liaison"] == "PARIS LYON -> MARSEILLE")
        & (result["Saison"] == "Hiver")
    ].iloc[0]

    assert winter["Trains circulés"] == 190


def test_creer_csv_metriques_calculates_delay_rate(df_trains):
    """The arrival delay rate is correctly calculated."""
    result = routes_metrics.creer_csv_metriques(df_trains)

    winter = result[
        (result["Liaison"] == "PARIS LYON -> MARSEILLE")
        & (result["Saison"] == "Hiver")
    ].iloc[0]

    assert winter["Taux retard arrivée"] == pytest.approx(30 / 190)


def test_creer_csv_metriques_calculates_cancellation_rate(df_trains):
    """The cancellation rate is correctly calculated."""
    result = routes_metrics.creer_csv_metriques(df_trains)

    winter = result[
        (result["Liaison"] == "PARIS LYON -> MARSEILLE")
        & (result["Saison"] == "Hiver")
    ].iloc[0]

    assert winter["Taux annulation"] == pytest.approx(10 / 200)


def test_creer_csv_metriques_calculates_reliability_rate(df_trains):
    """The reliability rate is correctly calculated."""
    result = routes_metrics.creer_csv_metriques(df_trains)

    winter = result[
        (result["Liaison"] == "PARIS LYON -> MARSEILLE")
        & (result["Saison"] == "Hiver")
    ].iloc[0]

    assert winter["Taux fiabilité"] == pytest.approx(160 / 200)


def test_creer_csv_metriques_groups_all_years(tmp_path):
    """Data from different years are grouped by route and season."""
    df = pd.DataFrame(
        {
            "date": ["2023-01-15", "2024-02-15"],
            "gare_depart": ["PARIS LYON", "PARIS LYON"],
            "gare_arrivee": ["MARSEILLE", "MARSEILLE"],
            "nb_train_prevu": [100, 100],
            "nb_annulation": [5, 5],
            "nb_train_retard_arrivee": [10, 20],
        }
    )

    csv_file = tmp_path / "multi_year.csv"
    df.to_csv(csv_file, sep=";", index=False)

    result = routes_metrics.creer_csv_metriques(csv_file)

    winter = result[
        (result["Liaison"] == "PARIS LYON -> MARSEILLE")
        & (result["Saison"] == "Hiver")
    ]

    assert len(winter) == 1
    assert winter.iloc[0]["Nombre de circulations prévues"] == 200
    assert winter.iloc[0]["Nombre de trains annulés"] == 10
    assert winter.iloc[0]["Nombre de trains en retard à l'arrivée"] == 30


def test_creer_csv_metriques_handles_zero_operated_trains(tmp_path):
    """A zero number of operated trains produces NaN delay rates."""
    df = pd.DataFrame(
        {
            "date": ["2024-01-15"],
            "gare_depart": ["PARIS LYON"],
            "gare_arrivee": ["MARSEILLE"],
            "nb_train_prevu": [10],
            "nb_annulation": [10],
            "nb_train_retard_arrivee": [0],
        }
    )

    csv_file = tmp_path / "zero_operated.csv"
    df.to_csv(csv_file, sep=";", index=False)

    result = routes_metrics.creer_csv_metriques(csv_file)

    assert pd.isna(result.loc[0, "Taux retard arrivée"])
    assert result.loc[0, "Taux annulation"] == pytest.approx(1.0)
    assert result.loc[0, "Taux fiabilité"] == pytest.approx(0.0)


def test_creer_csv_metriques_handles_zero_scheduled_trains(tmp_path):
    """Zero scheduled trains produce NaN rates without raising an error."""
    df = pd.DataFrame(
        {
            "date": ["2024-01-15"],
            "gare_depart": ["PARIS LYON"],
            "gare_arrivee": ["MARSEILLE"],
            "nb_train_prevu": [0],
            "nb_annulation": [0],
            "nb_train_retard_arrivee": [0],
        }
    )

    csv_file = tmp_path / "zero_scheduled.csv"
    df.to_csv(csv_file, sep=";", index=False)

    result = routes_metrics.creer_csv_metriques(csv_file)

    assert pd.isna(result.loc[0, "Taux retard arrivée"])
    assert pd.isna(result.loc[0, "Taux annulation"])
    assert pd.isna(result.loc[0, "Taux fiabilité"])


def test_creer_csv_metriques_saves_output_file(df_trains, tmp_path):
    """The metrics are correctly saved when an output path is provided."""
    output_file = tmp_path / "metrics.csv"

    result = routes_metrics.creer_csv_metriques(df_trains, sortie=output_file)

    assert output_file.is_file()

    saved_df = pd.read_csv(output_file, sep=";")

    pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        saved_df,
    )


def test_creer_csv_metriques_accepts_string_paths(df_trains, tmp_path):
    """The function accepts input and output paths as strings."""
    output_file = tmp_path / "metrics.csv"

    result = routes_metrics.creer_csv_metriques(
        str(df_trains),
        sortie=str(output_file),
    )

    assert isinstance(result, pd.DataFrame)
    assert output_file.is_file()


def test_creer_csv_metriques_without_output_path(df_trains):
    """No output file is created when no output path is provided."""
    result = routes_metrics.creer_csv_metriques(df_trains)

    assert isinstance(result, pd.DataFrame)
