"""Unit tests for the SNCF cleaning pipeline (``cleaning.py``)."""

import pandas as pd
import pytest

from ia700_project import cleaning

# A consistent raw row: it violates none of the pipeline consistency rules.
BASE_ROW = {
    "date": "2024-01",
    "service": "National",
    "gare_depart": "PARIS LYON",
    "gare_arrivee": "MARSEILLE ST CHARLES",
    "duree_moyenne": 180,
    "nb_train_prevu": 100,
    "nb_annulation": 5,
    "commentaire_annulation": None,
    "nb_train_depart_retard": 20,
    "retard_moyen_depart": 10.0,
    "retard_moyen_tous_trains_depart": 2.0,
    "commentaire_retards_depart": None,
    "nb_train_retard_arrivee": 30,
    "retard_moyen_arrivee": 25.0,
    "retard_moyen_tous_trains_arrivee": 5.0,
    "commentaires_retard_arrivee": None,
    "nb_train_retard_sup_15": 20,
    "retard_moyen_trains_retard_sup15": 35.0,
    "nb_train_retard_sup_30": 10,
    "nb_train_retard_sup_60": 3,
    "prct_cause_externe": 20.0,
    "prct_cause_infra": 20.0,
    "prct_cause_gestion_trafic": 20.0,
    "prct_cause_materiel_roulant": 20.0,
    "prct_cause_gestion_gare": 10.0,
    "prct_cause_prise_en_charge_voyageurs": 10.0,
}

# Columns that are completely empty in the raw SNCF export.
EMPTY_COLUMNS = ["commentaire_annulation", "commentaire_retards_depart"]

# The six delay-cause percentages, all set to zero.
ZERO_CAUSES = {column: 0.0 for column in cleaning.percentage_causes}


def make_df(
    rows: list[dict] | None = None, with_empty: bool = False
) -> pd.DataFrame:
    """Build a raw-like DataFrame from the base row plus overrides.

    Args:
        rows: One dict of overrides per row (``[{}]`` gives one base row).
        with_empty: Keep the two columns that are empty in the raw export.

    Returns:
        DataFrame using the technical column ids.
    """
    rows = rows if rows is not None else [{}]
    df = pd.DataFrame([{**BASE_ROW, **row} for row in rows])
    if not with_empty:
        df = df.drop(columns=EMPTY_COLUMNS)
    return df


# ---- load_raw_data ----


def test_load_raw_data_keeps_technical_headers(tmp_path):
    """A CSV that already uses the technical ids is loaded as is."""
    csv_file = tmp_path / "raw.csv"
    make_df(with_empty=True).to_csv(csv_file, sep=";", index=False)

    df = cleaning.load_raw_data(csv_file)

    assert set(df.columns) == set(cleaning.raw_cols)
    assert df.shape == (1, 26)


def test_load_raw_data_renames_display_headers(tmp_path):
    """French portal headers are renamed to the technical ids."""
    csv_file = tmp_path / "portal.csv"
    display_names = {v: k for k, v in cleaning.conversion_col_names.items()}
    portal_df = make_df(with_empty=True).rename(columns=display_names)
    portal_df.to_csv(csv_file, sep=";", index=False)

    df = cleaning.load_raw_data(csv_file)

    assert set(df.columns) == set(cleaning.raw_cols)
    assert df.loc[0, "gare_depart"] == "PARIS LYON"


def test_load_raw_data_handles_utf8_bom(tmp_path):
    """A BOM at the start of the file does not pollute the first header."""
    csv_file = tmp_path / "bom.csv"
    make_df(with_empty=True).to_csv(
        csv_file, sep=";", index=False, encoding="utf-8-sig"
    )

    df = cleaning.load_raw_data(csv_file)

    assert "date" in df.columns


def test_load_raw_data_rejects_unknown_headers(tmp_path):
    """Headers matching neither nomenclature raise a ValueError."""
    csv_file = tmp_path / "unknown.csv"
    pd.DataFrame({"foo": [1], "bar": [2]}).to_csv(
        csv_file, sep=";", index=False
    )

    with pytest.raises(ValueError, match="Unrecognized headers"):
        cleaning.load_raw_data(csv_file)


def test_load_raw_data_missing_file(tmp_path):
    """A missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        cleaning.load_raw_data(tmp_path / "absent.csv")


# ---- drop_empty_columns ----


def test_drop_empty_columns_removes_only_fully_empty_columns():
    """Fully empty columns go away, partly filled ones stay."""
    df = make_df(
        [{}, {"commentaires_retard_arrivee": "strike"}], with_empty=True
    )

    result = cleaning.drop_empty_columns(df)

    assert not set(EMPTY_COLUMNS) & set(result.columns)
    assert "commentaires_retard_arrivee" in result.columns


def test_drop_empty_columns_does_not_modify_input():
    """The input DataFrame is left untouched."""
    df = make_df(with_empty=True)

    cleaning.drop_empty_columns(df)

    assert set(EMPTY_COLUMNS) <= set(df.columns)


# ---- convert_dates ----


def test_convert_dates_parses_and_sorts_chronologically():
    """Dates become timestamps and rows are sorted by date."""
    df = make_df(
        [{"date": "2024-03"}, {"date": "2023-12"}, {"date": "2024-01"}]
    )

    result = cleaning.convert_dates(df)

    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert result["date"].tolist() == [
        pd.Timestamp("2023-12"),
        pd.Timestamp("2024-01"),
        pd.Timestamp("2024-03"),
    ]
    assert result.index.tolist() == [0, 1, 2]


def test_convert_dates_does_not_modify_input():
    """The input DataFrame keeps its original date strings."""
    df = make_df([{"date": "2024-03"}, {"date": "2023-12"}])

    cleaning.convert_dates(df)

    assert df["date"].tolist() == ["2024-03", "2023-12"]


def test_convert_dates_rejects_invalid_dates():
    """A date that is not formatted YYYY-MM raises a ValueError."""
    df = make_df([{"date": "not a date"}])

    with pytest.raises(ValueError):
        cleaning.convert_dates(df)


# ---- merge_duplicate_pairs ----


@pytest.fixture
def duplicated_pair() -> pd.DataFrame:
    """Two rows for the same month and route, one per service."""
    return make_df(
        [
            {
                "service": "National",
                "nb_train_prevu": 100,
                "nb_annulation": 4,
                "duree_moyenne": 100,
                "commentaires_retard_arrivee": "works",
            },
            {
                "service": "International",
                "nb_train_prevu": 300,
                "nb_annulation": 6,
                "duree_moyenne": 200,
                "commentaires_retard_arrivee": "strike",
            },
        ]
    )


def test_merge_duplicate_pairs_builds_one_national_row(duplicated_pair):
    """A National/International pair becomes a single National row."""
    result = cleaning.merge_duplicate_pairs(duplicated_pair)

    assert len(result) == 1
    assert result.loc[0, "service"] == "National"


def test_merge_duplicate_pairs_sums_counters(duplicated_pair):
    """Counter columns are summed over the two services."""
    result = cleaning.merge_duplicate_pairs(duplicated_pair)

    assert result.loc[0, "nb_train_prevu"] == 400
    assert result.loc[0, "nb_annulation"] == 10


def test_merge_duplicate_pairs_weights_averages(duplicated_pair):
    """Averages are weighted by the matching train counts."""
    result = cleaning.merge_duplicate_pairs(duplicated_pair)

    # (100 * 100 + 200 * 300) / 400
    assert result.loc[0, "duree_moyenne"] == pytest.approx(175.0)


def test_merge_duplicate_pairs_zero_weights_fall_back_to_mean(
    duplicated_pair,
):
    """With all weights at zero, the plain mean is used."""
    duplicated_pair["nb_train_depart_retard"] = 0
    duplicated_pair["retard_moyen_depart"] = [4.0, 8.0]

    result = cleaning.merge_duplicate_pairs(duplicated_pair)

    assert result.loc[0, "retard_moyen_depart"] == pytest.approx(6.0)


def test_merge_duplicate_pairs_joins_comments(duplicated_pair):
    """Both comments are kept, separated by a pipe."""
    result = cleaning.merge_duplicate_pairs(duplicated_pair)

    assert result.loc[0, "commentaires_retard_arrivee"] == "works | strike"


def test_merge_duplicate_pairs_single_comment(duplicated_pair):
    """A single comment is kept without any separator."""
    duplicated_pair["commentaires_retard_arrivee"] = ["works", None]

    result = cleaning.merge_duplicate_pairs(duplicated_pair)

    assert result.loc[0, "commentaires_retard_arrivee"] == "works"


def test_merge_duplicate_pairs_without_comment(duplicated_pair):
    """Without any comment, the merged comment is missing."""
    duplicated_pair["commentaires_retard_arrivee"] = None

    result = cleaning.merge_duplicate_pairs(duplicated_pair)

    assert pd.isna(result.loc[0, "commentaires_retard_arrivee"])


def test_merge_duplicate_pairs_keeps_regular_rows(duplicated_pair):
    """Regular rows are kept as they are, sorted with the merged ones."""
    regular = make_df([{"gare_depart": "LILLE", "gare_arrivee": "PARIS NORD"}])
    df = pd.concat([duplicated_pair, regular], ignore_index=True)

    result = cleaning.merge_duplicate_pairs(df)

    assert result["gare_depart"].tolist() == ["LILLE", "PARIS LYON"]
    assert result.loc[0, "nb_train_prevu"] == 100
    assert result.index.tolist() == [0, 1]


def test_merge_duplicate_pairs_without_duplicates_changes_nothing():
    """Data without any duplicated pair comes back unchanged."""
    df = make_df(
        [
            {"gare_depart": "LILLE", "gare_arrivee": "PARIS NORD"},
            {"gare_depart": "PARIS LYON"},
        ]
    )

    result = cleaning.merge_duplicate_pairs(df)

    assert len(result) == 2
    assert result["nb_train_prevu"].tolist() == [100, 100]


# ---- consistency_checks ----

VIOLATIONS = [
    ("negative counter", {"nb_annulation": -1}),
    ("zero scheduled trains", {"nb_train_prevu": 0}),
    ("cancellations > scheduled trains", {"nb_annulation": 101}),
    ("departure delays > operated trains", {"nb_train_depart_retard": 96}),
    ("arrival delays > operated trains", {"nb_train_retard_arrivee": 96}),
    ("(delays >15min) > arrival delays", {"nb_train_retard_sup_15": 31}),
    ("(delays >30min) > delays >15min", {"nb_train_retard_sup_30": 21}),
    ("(delays >60min) > delays >30min", {"nb_train_retard_sup_60": 11}),
    ("zero or negative average duration", {"duree_moyenne": 0}),
]


def test_consistency_checks_reports_nothing_on_consistent_data():
    """A consistent dataset has zero error for every rule."""
    checks = cleaning.consistency_checks(make_df())

    assert len(checks) == len(VIOLATIONS)
    assert (checks["errors"] == 0).all()


@pytest.mark.parametrize(
    ("rule", "override"), VIOLATIONS, ids=[rule for rule, _ in VIOLATIONS]
)
def test_consistency_checks_counts_violating_rows(rule, override):
    """Each rule counts exactly the one row that breaks it."""
    df = make_df([{}, override])  # one consistent row, one broken row

    checks = cleaning.consistency_checks(df)

    assert checks.loc[rule, "errors"] == 1


# ---- precovid_sensitivity ----


def test_precovid_sensitivity_corrects_precovid_anomalies():
    """The correction raises the delay rate when anomalies exist."""
    df = make_df(
        [
            # anomaly: more ">15 min" delays (20) than arrival delays (10)
            {
                "date": "2019-01",
                "nb_annulation": 0,
                "nb_train_retard_arrivee": 10,
                "nb_train_retard_sup_15": 20,
            },
            {
                "date": "2024-01",
                "nb_annulation": 0,
                "nb_train_retard_arrivee": 10,
                "nb_train_retard_sup_15": 5,
            },
        ]
    )

    result = cleaning.precovid_sensitivity(cleaning.convert_dates(df))

    assert result.index.tolist() == ["before correction", "after correction"]
    assert result["delay_rate_pct"].tolist() == pytest.approx([10.0, 15.0])


def test_precovid_sensitivity_ignores_rows_after_covid_start():
    """Anomalies dated after March 2020 are not corrected."""
    df = make_df(
        [
            {
                "date": "2024-01",
                "nb_annulation": 0,
                "nb_train_retard_arrivee": 10,
                "nb_train_retard_sup_15": 20,
            }
        ]
    )

    result = cleaning.precovid_sensitivity(cleaning.convert_dates(df))

    assert result["delay_rate_pct"].tolist() == pytest.approx([10.0, 10.0])


# ---- fix_postcovid_anomalies ----


@pytest.fixture
def anomalous_counters() -> pd.DataFrame:
    """Four rows: two with a broken counter hierarchy, two without."""
    df = make_df(
        [
            # 2025 row with sup_30 (25) > sup_15 (20): sup_15 is unknown
            {"date": "2025-02", "nb_train_retard_sup_30": 25},
            # the same issue before 2025 is left untouched
            {"date": "2024-02", "nb_train_retard_sup_30": 25},
            # sup_60 (12) > sup_30 (10): sup_30 is unknown, whatever the date
            {"date": "2023-05", "nb_train_retard_sup_60": 12},
            {"date": "2023-06"},
        ]
    )
    return cleaning.convert_dates(df)


def test_fix_postcovid_anomalies_blanks_sup_15_in_2025(anomalous_counters):
    """sup_15 becomes NA when sup_30 exceeds it from 2025 on."""
    result = cleaning.fix_postcovid_anomalies(anomalous_counters)

    flagged = result[result["date"] == pd.Timestamp("2025-02")]
    untouched = result[result["date"] == pd.Timestamp("2024-02")]
    assert flagged["nb_train_retard_sup_15"].isna().all()
    assert untouched["nb_train_retard_sup_15"].notna().all()


def test_fix_postcovid_anomalies_blanks_sup_30_when_sup_60_is_larger(
    anomalous_counters,
):
    """sup_30 becomes NA when sup_60 exceeds it, at any date."""
    result = cleaning.fix_postcovid_anomalies(anomalous_counters)

    assert result["nb_train_retard_sup_30"].isna().sum() == 1
    flagged = result[result["date"] == pd.Timestamp("2023-05")]
    assert flagged["nb_train_retard_sup_30"].isna().all()


def test_fix_postcovid_anomalies_does_not_modify_input(anomalous_counters):
    """The input DataFrame is left untouched."""
    cleaning.fix_postcovid_anomalies(anomalous_counters)

    assert anomalous_counters["nb_train_retard_sup_15"].notna().all()
    assert anomalous_counters["nb_train_retard_sup_30"].notna().all()


# ---- fix_cause_percentages ----


def test_fix_cause_percentages_blanks_only_unusable_breakdowns():
    """Only unusable breakdowns are set to NaN."""
    df = make_df(
        [
            {},  # complete breakdown (sums to 100)
            {
                **ZERO_CAUSES,
                "nb_train_retard_arrivee": 0,
            },  # no delay, no cause
            {**ZERO_CAUSES},  # delays but no cause at all
            {**ZERO_CAUSES, "prct_cause_externe": 50.0},  # partial, below 90
            {**ZERO_CAUSES, "prct_cause_externe": 95.0},  # partial, kept
        ]
    )

    result = cleaning.fix_cause_percentages(df)

    blanked = result[cleaning.percentage_causes].isna().all(axis=1)
    assert blanked.tolist() == [False, False, True, True, False]


def test_fix_cause_percentages_keeps_complete_breakdown_values():
    """A complete breakdown keeps its original values."""
    result = cleaning.fix_cause_percentages(make_df())

    assert result[cleaning.percentage_causes].iloc[0].sum() == 100.0


# ---- clean_dataset ----


@pytest.fixture
def raw_csv(tmp_path):
    """Write a small raw CSV with one National/International pair."""
    csv_file = tmp_path / "raw.csv"
    rows = [
        {"date": "2025-08", "commentaires_retard_arrivee": "works"},
        {
            "date": "2025-08",
            "service": "International",
            "commentaires_retard_arrivee": "strike",
        },
        {
            "date": "2023-01",
            "gare_depart": "LILLE",
            "gare_arrivee": "PARIS NORD",
        },
    ]
    make_df(rows, with_empty=True).to_csv(csv_file, sep=";", index=False)
    return csv_file


def test_clean_dataset_runs_the_full_pipeline(raw_csv):
    """The pipeline drops empty columns, parses dates and merges pairs."""
    result = cleaning.clean_dataset(raw_csv)

    assert len(result) == 2
    assert not set(EMPTY_COLUMNS) & set(result.columns)
    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert result["date"].is_monotonic_increasing
    assert result["service"].tolist() == ["National", "National"]


def test_clean_dataset_saves_the_result_when_asked(raw_csv, tmp_path):
    """With an output path, the cleaned data is saved as a CSV."""
    output_file = tmp_path / "cleaned.csv"

    result = cleaning.clean_dataset(raw_csv, output_file)

    saved = pd.read_csv(output_file, sep=";")
    assert saved.shape == result.shape


def test_clean_dataset_writes_nothing_without_output_path(raw_csv, tmp_path):
    """Without an output path, no file is created."""
    cleaning.clean_dataset(raw_csv)

    assert [path.name for path in tmp_path.iterdir()] == ["raw.csv"]


def test_clean_dataset_missing_file(tmp_path):
    """A missing input file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        cleaning.clean_dataset(tmp_path / "absent.csv")
