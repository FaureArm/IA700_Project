"""Cleaning pipeline for the SNCF monthly TGV punctuality dataset.

Ports the reference EDA notebook (``EDA.ipynb``) into importable
functions, so the cleaning steps can be reused by the rest of the
project (analysis modules, Streamlit app, unit tests). Every
decision encoded here is the decision taken in the notebook, in the
same order: load the ";"-separated raw export, drop the fully empty
columns, parse and sort the dates, merge the National/International
duplicate pairs, report consistency checks, quantify the pre-COVID
anomalies (nothing corrected), set the unrecoverable 2025 counters
to NA, set the unusable cause breakdowns to NaN, or run everything
end to end with ``clean_dataset``.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Key identifying one observation: month + route.
KEY_COLUMNS = ["date", "gare_depart", "gare_arrivee"]

# Columns counting trains: merged by summation.
COUNTER_COLUMNS = [
    "nb_train_prevu", "nb_annulation",
    "nb_train_depart_retard", "nb_train_retard_arrivee",
    "nb_train_retard_sup_15", "nb_train_retard_sup_30",
    "nb_train_retard_sup_60",
]

# Columns meaning "an average over trains": merged as train-volume
# weighted means. Maps value column -> weight column.
WEIGHTED_COLUMNS = {
    "duree_moyenne": "nb_train_prevu",
    "retard_moyen_depart": "nb_train_depart_retard",
    "retard_moyen_tous_trains_depart": "nb_train_prevu",
    "retard_moyen_arrivee": "nb_train_retard_arrivee",
    "retard_moyen_tous_trains_arrivee": "nb_train_prevu",
    "retard_moyen_trains_retard_sup15": "nb_train_retard_sup_15",
    "prct_cause_externe": "nb_train_retard_arrivee",
    "prct_cause_infra": "nb_train_retard_arrivee",
    "prct_cause_gestion_trafic": "nb_train_retard_arrivee",
    "prct_cause_materiel_roulant": "nb_train_retard_arrivee",
    "prct_cause_gestion_gare": "nb_train_retard_arrivee",
    "prct_cause_prise_en_charge_voyageurs": "nb_train_retard_arrivee",
}

# Percentage-of-delay-cause columns (subset of WEIGHTED_COLUMNS).
CAUSE_COLUMNS = [
    "prct_cause_externe", "prct_cause_infra",
    "prct_cause_gestion_trafic",
    "prct_cause_materiel_roulant",
    "prct_cause_gestion_gare",
    "prct_cause_prise_en_charge_voyageurs",
]

# Free-text column, 94.6% missing (publication stopped in 2020).
COMMENT_COLUMN = "commentaires_retard_arrivee"

# Label chosen for the merged National/International pairs.
MERGED_SERVICE = "National"

# First French lockdown: start of the documented COVID anomalies.
COVID_START = pd.Timestamp("2020-01")

# Start of the 2025 window where SNCF published broken counters.
POST_COVID_START = pd.Timestamp("2025-01")


def load_raw_data(csv_path: str | Path) -> pd.DataFrame:
    """Read the raw SNCF CSV export.

    Args:
        csv_path: Path to the raw CSV file (";"-separated).

    Returns:
        DataFrame with the 26 raw columns (12,907 rows in the
        Nov 2026 export, months 2018-01 to 2026-09).

    Raises:
        FileNotFoundError: If ``csv_path`` does not exist.
    """
    df = pd.read_csv(csv_path, sep=";")
    logger.info("Loaded raw data: %d rows, %d columns", *df.shape)
    return df


def drop_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the columns that contain no value at all.

    In the raw export these are ``commentaire_annulation`` and
    ``commentaire_retards_depart`` (both 100% empty).

    Args:
        df: Raw data.

    Returns:
        Copy of ``df`` without the fully empty columns (24 remain).
    """
    df = df.copy()
    # Columns with no observed value.
    empty_columns = df.columns[df.isna().all()].tolist()
    df = df.drop(columns=empty_columns)
    logger.info("Dropped empty columns: %s", empty_columns)
    return df


def convert_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse ``date`` as monthly timestamps and sort chronologically.

    No year/month columns are derived: year and month stay
    available on the fly via ``df["date"].dt``.

    Args:
        df: Data without the empty columns.

    Returns:
        Copy of ``df`` with a datetime64 "date" column, sorted by
        date, index reset.
    """
    df = df.copy()
    # Monthly dates arrive as "YYYY-MM" strings.
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m")
    return df.sort_values("date").reset_index(drop=True)


def _merge_pair(group: pd.DataFrame) -> dict:
    """Merge one National/International pair into a single row.

    Args:
        group: Exactly two rows sharing month and route.

    Returns:
        Dict with a merged value for every column.
    """
    row: dict = {}
    # Key columns: identical route for the pair, kept as-is.
    for column in KEY_COLUMNS:
        row[column] = group[column].iloc[0]
    # Service label chosen for the merged pair.
    row["service"] = MERGED_SERVICE
    # Counters count trains: merged by summation.
    for column in COUNTER_COLUMNS:
        row[column] = group[column].sum()
    # Averages and percentages mean things: merged as train-volume
    # weighted means (simple mean when no train backs the values).
    for column, weight_column in WEIGHTED_COLUMNS.items():
        values = group[column].to_numpy(dtype=float)
        weights = group[weight_column].to_numpy(dtype=float)
        if weights.sum() > 0:
            row[column] = float((values * weights).sum() / weights.sum())
        else:
            row[column] = float(values.mean())
    # Free-text comments: concatenated with a separator.
    comments = group[COMMENT_COLUMN].dropna().tolist()
    row[COMMENT_COLUMN] = " | ".join(comments) if comments else pd.NA
    return row


def merge_duplicate_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """Merge the National/International duplicate pairs.

    42 pairs appear twice, once per service (2025-07 to 2025-09
    only, after the rail market opened to competition). Each pair
    becomes a single National row: counters summed, averages and
    percentages weighted by train volumes, comments joined.

    Args:
        df: Data with parsed dates.

    Returns:
        DataFrame without duplicates on month + route, sorted
        (12,865 rows: National 11,339, International 1,526).
    """
    # Number of distinct services per month + route.
    n_services = df.groupby(KEY_COLUMNS)["service"].transform("nunique")
    # Rows duplicated across the two services, and regular rows.
    to_merge = df[n_services == 2]
    to_keep = df[n_services == 1]
    # One merged row per duplicated pair.
    merged_rows = pd.DataFrame(
        [_merge_pair(group) for _, group in to_merge.groupby(KEY_COLUMNS)]
    )
    df = pd.concat([to_keep, merged_rows], ignore_index=True)
    return df.sort_values(KEY_COLUMNS).reset_index(drop=True)


def _build_check_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Build one boolean mask per expected consistency rule.

    Args:
        df: Data after the duplicate merge.

    Returns:
        Dict mapping rule name to a boolean mask Series.
    """
    # Trains actually operated: scheduled minus cancelled.
    trains_operated = df["nb_train_prevu"] - df["nb_annulation"]
    return {
        # Counters can only add up, never go negative.
        "negative counter": (df[COUNTER_COLUMNS] < 0).any(axis=1),
        # A month without any scheduled train should not exist.
        "zero scheduled trains": df["nb_train_prevu"] == 0,
        # Cancellations cannot exceed the scheduled trains.
        "cancellations > scheduled trains": (
            df["nb_annulation"] > df["nb_train_prevu"]
        ),
        # Late departures cannot exceed the operated trains.
        "departure delays > operated trains": (
            df["nb_train_depart_retard"] > trains_operated
        ),
        # Late arrivals cannot exceed the operated trains.
        "arrival delays > operated trains": (
            df["nb_train_retard_arrivee"] > trains_operated
        ),
        # Thresholds nest: >15 min delays subset the arrival delays.
        "(delays >15min) > arrival delays": (
            df["nb_train_retard_sup_15"] > df["nb_train_retard_arrivee"]
        ),
        # Same nesting between the 30 min and 15 min thresholds.
        "(delays >30min) > delays >15min": (
            df["nb_train_retard_sup_30"] > df["nb_train_retard_sup_15"]
        ),
        # Same nesting between the 60 min and 30 min thresholds.
        "(delays >60min) > delays >30min": (
            df["nb_train_retard_sup_60"] > df["nb_train_retard_sup_30"]
        ),
        # An average journey duration is strictly positive.
        "zero or negative average duration": df["duree_moyenne"] <= 0,
    }


def consistency_checks(df: pd.DataFrame) -> pd.DataFrame:
    """Count the rows violating each expected consistency rule.

    Diagnostics only: most hits are legitimate documented events
    (COVID period) or anomalies fixed by the dedicated functions.

    Args:
        df: Data after the duplicate merge.

    Returns:
        DataFrame with one row per rule and an "errors" column
        holding the number of violating rows.
    """
    # One boolean mask per expected rule.
    masks = _build_check_masks(df)
    # Number of violating rows for each rule.
    results = pd.DataFrame(
        {"errors": [int(mask.sum()) for mask in masks.values()]},
        index=list(masks.keys()),
    )
    return results


def precovid_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """Quantify the pre-COVID sup_15 > arrivee anomalies.

    On 13 pre-COVID rows the >15 min counter exceeds the total
    arrival-delay counter. The notebook leaves them unchanged: the
    hypothetical correction only moves the delay rate from
    14.6583% to 14.6595%.

    Args:
        df: Data after the duplicate merge.

    Returns:
        DataFrame with the national delay rate (% of operated
        trains) before and after the hypothetical correction, NOT
        applied to the data.
    """
    # Anomalous rows before the first lockdown.
    mask_precovid = (
        (df["nb_train_retard_sup_15"] > df["nb_train_retard_arrivee"])
        & (df["date"] < COVID_START)
    )
    # Hypothetical arrival counter on the anomalous rows.
    corrected = df["nb_train_retard_sup_15"].where(
        mask_precovid, df["nb_train_retard_arrivee"]
    )
    # Operated trains: scheduled minus cancelled, floored at zero.
    trains_operated = (
        df["nb_train_prevu"] - df["nb_annulation"]
    ).clip(lower=0)
    # National delay rate in %, before and after the correction.
    before = round(
        100 * df["nb_train_retard_arrivee"].sum() / trains_operated.sum(), 4
    )
    after = round(100 * corrected.sum() / trains_operated.sum(), 4)
    return pd.DataFrame(
        {"delay_rate_pct": [before, after]},
        index=["before correction", "after correction"],
    )


def fix_postcovid_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Set the unrecoverable post-COVID delay counters to NA.

    Two unrecoverable anomalies: 2025 rows with more trains
    delayed >30 min than >15 min (1 row, Tours -> Paris
    Montparnasse 2025-03) get sup_15 set to NA; rows with more
    trains delayed >60 min than >30 min (SNCF bug 2025-01 to
    2025-03, 354 rows) get sup_30 set to NA. The two 2020-05 rows
    with the same profile stay as documented COVID values.

    Args:
        df: Data after the duplicate merge.

    Returns:
        Copy of ``df`` with the anomalous counters set to NA.
    """
    df = df.copy()
    # sup_30 > sup_15 in 2025: hierarchy violation, value unknown.
    mask_sup_15 = (
        (df["nb_train_retard_sup_30"] > df["nb_train_retard_sup_15"])
        & (df["date"] >= POST_COVID_START)
    )
    df.loc[mask_sup_15, "nb_train_retard_sup_15"] = pd.NA
    # sup_60 > sup_30: SNCF bug on the sup_30 counter.
    mask_sup_30 = df["nb_train_retard_sup_60"] > df["nb_train_retard_sup_30"]
    df.loc[mask_sup_30, "nb_train_retard_sup_30"] = pd.NA
    logger.info(
        "Post-COVID fixes: %d sup_15, %d sup_30 values set to NA",
        int(mask_sup_15.sum()), int(mask_sup_30.sum()),
    )
    return df


def fix_cause_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """Set the unusable delay-cause breakdowns to NaN.

    Kept: rows summing to 100 (+- 0.1 pt, 12,584 rows) and
    coherent zero rows without delayed trains (191). Set to NaN:
    rows with delayed trains but a zero cause sum (80) and partial
    rows below 90% (3); the 7 partial rows >= 90% are kept and
    documented. Renormalizing to 100% is rejected: it would invent
    a cause for the unclassified trains.

    Args:
        df: Data after the post-COVID fixes.

    Returns:
        Copy of ``df`` with the six ``prct_cause_*`` columns set to
        NaN on 83 rows in total.
    """
    df = df.copy()
    # Sum of the six cause percentages for each row.
    cause_sum = df[CAUSE_COLUMNS].sum(axis=1)
    # Trains delayed at arrival for each row.
    delayed = df["nb_train_retard_arrivee"]
    # Complete breakdown: the six causes add up to 100%.
    complete = cause_sum.between(99.9, 100.1)
    # Breakdown unusable: trains were delayed but the causes are
    # missing (zero or partial sum below 90%).
    mask_missing = (delayed > 0) & ~complete & (cause_sum < 90)
    df.loc[mask_missing, CAUSE_COLUMNS] = np.nan
    logger.info("Cause fixes: %d rows set to NaN", int(mask_missing.sum()))
    return df


def clean_dataset(
    csv_path: str | Path,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Run the full cleaning pipeline on the raw export.

    Args:
        csv_path: Path to the raw CSV file.
        output_path: Optional CSV path to save the cleaned data
            (";"-separated, no index).

    Returns:
        The cleaned DataFrame: 12,865 rows, 24 columns, no
        duplicates on month + route.

    Raises:
        FileNotFoundError: If ``csv_path`` does not exist.
    """
    df = load_raw_data(csv_path)
    df = drop_empty_columns(df)
    df = convert_dates(df)
    df = merge_duplicate_pairs(df)
    # Diagnostics: reported, they do not modify the data.
    checks = consistency_checks(df)
    logger.info("Consistency checks:\n%s", checks.to_string())
    sensitivity = precovid_sensitivity(df)
    logger.info("Pre-COVID sensitivity:\n%s", sensitivity.to_string())
    df = fix_postcovid_anomalies(df)
    df = fix_cause_percentages(df)
    logger.info("Cleaned data: %d rows, %d columns", *df.shape)
    if output_path is not None:
        # Cleaned export: same separator as the raw file.
        df.to_csv(output_path, sep=";", index=False)
        logger.info("Saved cleaned data to %s", output_path)
    return df
