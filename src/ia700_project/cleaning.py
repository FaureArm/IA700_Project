"""Cleaning pipeline for the SNCF monthly TGV punctuality dataset.

Refer to datasheet.md for details regarding EDA and data cleaning
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

cols_duplicates = ["date", "gare_depart", "gare_arrivee"]

counter_cols = [
    "nb_train_prevu",
    "nb_annulation",
    "nb_train_depart_retard",
    "nb_train_retard_arrivee",
    "nb_train_retard_sup_15",
    "nb_train_retard_sup_30",
    "nb_train_retard_sup_60",
]

weighted_cols = {
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

percentage_causes = [
    "prct_cause_externe",
    "prct_cause_infra",
    "prct_cause_gestion_trafic",
    "prct_cause_materiel_roulant",
    "prct_cause_gestion_gare",
    "prct_cause_prise_en_charge_voyageurs",
]

comment_col = "commentaires_retard_arrivee"


conversion_col_names = {
    "Date": "date",
    "Service": "service",
    "Gare de départ": "gare_depart",
    "Gare d'arrivée": "gare_arrivee",
    "Durée moyenne du trajet": "duree_moyenne",
    "Nombre de circulations prévues": "nb_train_prevu",
    "Nombre de trains annulés": "nb_annulation",
    "Commentaire annulations": "commentaire_annulation",
    "Nombre de trains en retard au départ": "nb_train_depart_retard",
    "Retard moyen des trains en retard au départ": "retard_moyen_depart",
    "Retard moyen de tous les trains au départ": "retard_moyen_tous_trains_depart",
    "Commentaire retards au départ": "commentaire_retards_depart",
    "Nombre de trains en retard à l'arrivée": "nb_train_retard_arrivee",
    "Retard moyen des trains en retard à l'arrivée": "retard_moyen_arrivee",
    "Retard moyen de tous les trains à l'arrivée": "retard_moyen_tous_trains_arrivee",
    "Commentaire retards à l'arrivée": "commentaires_retard_arrivee",
    "Nombre trains en retard > 15min": "nb_train_retard_sup_15",
    "Retard moyen trains en retard > 15 (si liaison concurrencée par vol)": "retard_moyen_trains_retard_sup15",
    "Nombre trains en retard > 30min": "nb_train_retard_sup_30",
    "Nombre trains en retard > 60min": "nb_train_retard_sup_60",
    "Prct retard pour causes externes": "prct_cause_externe",
    "Prct retard pour cause infrastructure": "prct_cause_infra",
    "Prct retard pour cause gestion trafic": "prct_cause_gestion_trafic",
    "Prct retard pour cause matériel roulant": "prct_cause_materiel_roulant",
    "Prct retard pour cause gestion en gare et réutilisation de matériel": "prct_cause_gestion_gare",
    "Prct retard pour cause prise en compte voyageurs (affluence, gestions PSH, correspondances)": "prct_cause_prise_en_charge_voyageurs",
}

raw_cols = list(conversion_col_names.values())

# Label chosen for the merged National/International pairs.
merged_service = "National"

# First French lockdown: start of the documented COVID anomalies.
covid_start = pd.Timestamp("2020-03")

# Start of the 2025 window where SNCF published broken counters.
post_covid = pd.Timestamp("2025-01")


def load_raw_data(csv_path: str | Path) -> pd.DataFrame:
    """Read a raw SNCF CSV export and normalize its headers.

    For some reason, column names may vary depending on how the
    data was downloaded from the SNCF portal. Some datasets may
    use descriptive column names (e.g., Date, Departure Station),
    while others may use standardized column names (e.g., date,
    departure_station). This function ensures that the dataset
    uses the standardized column names.

    Args:
        csv_path: Path to the raw CSV file (";"-separated, UTF-8)

    Returns:
        DataFrame with the 26 raw columns under their technical
        ids

    Raises:
        FileNotFoundError: If ``csv_path`` does not exist.
        ValueError: If the headers match neither nomenclature.
    """
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    if set(raw_cols).issubset(df.columns):
        # headers already normalized, keep them.
        pass
    elif set(conversion_col_names).issubset(df.columns):
        # if not, rename columns
        df = df.rename(columns=conversion_col_names)
        logger.info("Renamed %d display headers to ids", len(conversion_col_names))
    else:
        raise ValueError(
            "Unrecognized headers: expected the 26 technical ids "
            "(API export) or their French display labels (portal "
            "download); got: " + str(list(df.columns))
        )
    logger.info("Loaded raw data: %d rows, %d columns", *df.shape)
    return df


def drop_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the columns that contain no value at all.

    In the raw export these are commentaire_annulation and
    commentaire_retards_depart

    Args:
        df: Raw data.

    Returns:
        Copy of df without the fully empty columns.
    """
    df = df.copy()
    empty_columns = df.columns[df.isna().all()].tolist()
    df = df.drop(columns=empty_columns)
    logger.info("Dropped empty columns: %s", empty_columns)
    return df


def convert_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse date as monthly timestamps and sort chronologically.

    Args:
        df: Data

    Returns:
        Copy of df with a datetime64 "date" column, sorted by
        date
    """
    df = df.copy()
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
    for column in cols_duplicates:
        row[column] = group[column].iloc[0]
    # Service label chosen for the merged pair.
    row["service"] = merged_service
    # add counter columns
    for column in counter_cols:
        row[column] = group[column].sum()
    # do a weighted average for the columns concerned
    for column, weight_column in weighted_cols.items():
        values = group[column].to_numpy(dtype=float)
        weights = group[weight_column].to_numpy(dtype=float)
        if weights.sum() > 0:
            row[column] = float((values * weights).sum() / weights.sum())
        else:
            row[column] = float(values.mean())
    # handling comments
    comments = group[comment_col].dropna().tolist()
    row[comment_col] = " | ".join(comments) if comments else pd.NA
    return row


def merge_duplicate_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """Merge the National/International duplicate pairs.

    42 pairs appear twice, once per service (2025-07 to 2025-09
    only, after the rail market opened to competition). Each pair
    becomes a single National row: counters summed, averages and
    percentages weighted by train volumes, comments joined.

    Args:
        df: Data

    Returns:
        DataFrame without duplicates on month + route
    """
    # Number of distinct services per month + route.
    n_services = df.groupby(cols_duplicates)["service"].transform("nunique")
    # Rows duplicated across the two services, and regular rows.
    to_merge = df[n_services == 2]
    to_keep = df[n_services == 1]
    # One merged row per duplicated pair.
    merged_rows = pd.DataFrame(
        [_merge_pair(group) for _, group in to_merge.groupby(cols_duplicates)]
    )
    df = pd.concat([to_keep, merged_rows], ignore_index=True)
    return df.sort_values(cols_duplicates).reset_index(drop=True)


def _build_check_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Build one boolean mask per expected consistency rule.

    Args:
        df: Data

    Returns:
        Dict mapping rule name to a boolean mask Series.
    """
    trains_operated = df["nb_train_prevu"] - df["nb_annulation"]
    return {
        # Counters can only add up, never go negative.
        "negative counter": (df[counter_cols] < 0).any(axis=1),
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

    Args:
        df: Data

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
    .
        Args:
            df: Data

        Returns:
            DataFrame with the national delay rate before and after the
            hypothetical correction
    """
    # Anomalous rows before the first lockdown.
    mask_precovid = (df["nb_train_retard_sup_15"] > df["nb_train_retard_arrivee"]) & (
        df["date"] < covid_start
    )
    # Hypothetical arrival counter on the anomalous rows.
    corrected = df["nb_train_retard_sup_15"].where(
        mask_precovid, df["nb_train_retard_arrivee"]
    )
    trains_operated = (df["nb_train_prevu"] - df["nb_annulation"]).clip(lower=0)
    # National delay rate in %, before and after the correction.
    before = round(100 * df["nb_train_retard_arrivee"].sum() / trains_operated.sum(), 4)
    after = round(100 * corrected.sum() / trains_operated.sum(), 4)
    return pd.DataFrame(
        {"delay_rate_pct": [before, after]},
        index=["before correction", "after correction"],
    )


def fix_postcovid_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Set the unrecoverable post-COVID delay counters to NA.

    Args:
        df: Data

    Returns:
        Copy of df with the anomalous counters set to NA.
    """
    df = df.copy()
    # sup_30 > sup_15 in 2025: hierarchy violation, value unknown.
    mask_sup_15 = (df["nb_train_retard_sup_30"] > df["nb_train_retard_sup_15"]) & (
        df["date"] >= post_covid
    )
    df.loc[mask_sup_15, "nb_train_retard_sup_15"] = pd.NA
    # sup_60 > sup_30: SNCF bug on the sup_30 counter.
    mask_sup_30 = df["nb_train_retard_sup_60"] > df["nb_train_retard_sup_30"]
    df.loc[mask_sup_30, "nb_train_retard_sup_30"] = pd.NA
    logger.info(
        "Post-COVID fixes: %d sup_15, %d sup_30 values set to NA",
        int(mask_sup_15.sum()),
        int(mask_sup_30.sum()),
    )
    return df


def fix_cause_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """Set the unusable delay-cause breakdowns to NaN.

    Kept: rows summing to 100 and coherent zero rows without delayed
    trains
    Set to NaN: rows with delayed trains but a zero cause sum and partial
    rows below 90%. The other partial rows >= 90% are kept and
    documented.

    Args:
        df: Data

    Returns:
        Copy of df with the six prct_cause_* fixed and consistent
    """
    df = df.copy()
    cause_sum = df[percentage_causes].sum(axis=1)
    delayed = df["nb_train_retard_arrivee"]
    # Complete breakdown: the six causes add up to 100%.
    complete = cause_sum.between(99.9, 100.1)
    # Breakdown unusable: trains were delayed but the causes are missing.
    mask_missing = (delayed > 0) & ~complete & (cause_sum < 90)
    df.loc[mask_missing, percentage_causes] = np.nan
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

    Returns:
        The cleaned DataFrame

    Raises:
        FileNotFoundError: If csv_path does not exist.
        ValueError: If the raw headers match neither the technical
            ids nor the display labels.
    """
    df = load_raw_data(csv_path)
    df = drop_empty_columns(df)
    df = convert_dates(df)
    df = merge_duplicate_pairs(df)
    checks = consistency_checks(df)
    logger.info("Consistency checks:\n%s", checks.to_string())
    sensitivity = precovid_sensitivity(df)
    logger.info("Pre-COVID sensitivity:\n%s", sensitivity.to_string())
    df = fix_postcovid_anomalies(df)
    df = fix_cause_percentages(df)
    logger.info("Cleaned data: %d rows, %d columns", *df.shape)
    if output_path is not None:
        df.to_csv(output_path, sep=";", index=False)
        logger.info("Saved cleaned data to %s", output_path)
    return df
