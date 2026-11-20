"""Calculate monthly route metrics for the SNCF dataset."""

from pathlib import Path

import pandas as pd


def creer_csv_metriques(
    df: pd.DataFrame | str | Path,
    sortie: str | Path | None = None,
) -> pd.DataFrame:
    """Create monthly route metrics with season labels.

    Uses the cleaned SNCF DataFrame and groups all years
    together by route, season, and month.

    Args:
        df: Cleaned SNCF DataFrame or path to a CSV file.
        sortie: Optional path to save the metrics CSV.

    Returns:
        DataFrame with train counts, delay rates, cancellation
        rates, and reliability rates for each route and month.
    """
    # Load the CSV if a path is provided, otherwise copy the DataFrame.
    if isinstance(df, (str, Path)):
        df = pd.read_csv(df, sep=";")
    else:
        df = df.copy()

    # Ensure the date column uses datetime format.
    df["date"] = pd.to_datetime(df["date"])

    # Create a route label from departure and arrival stations.
    df["Liaison"] = df["gare_depart"] + " -> " + df["gare_arrivee"]

    # Match each month to its season.
    saisons = {
        12: "Hiver",
        1: "Hiver",
        2: "Hiver",
        3: "Printemps",
        4: "Printemps",
        5: "Printemps",
        6: "Été",
        7: "Été",
        8: "Été",
        9: "Automne",
        10: "Automne",
        11: "Automne",
    }

    # Match each month number to its name.
    mois = {
        1: "Janvier",
        2: "Février",
        3: "Mars",
        4: "Avril",
        5: "Mai",
        6: "Juin",
        7: "Juillet",
        8: "Août",
        9: "Septembre",
        10: "Octobre",
        11: "Novembre",
        12: "Décembre",
    }

    # Extract the month number and assign its season.
    df["Mois"] = df["date"].dt.month
    df["Saison"] = df["Mois"].map(saisons)

    # Aggregate train counts by route, season, and month.
    resultats = df.groupby(
        ["Liaison", "Saison", "Mois"],
        as_index=False,
    ).agg(
        **{
            "Nombre de circulations prévues": (
                "nb_train_prevu",
                "sum",
            ),
            "Nombre de trains annulés": (
                "nb_annulation",
                "sum",
            ),
            "Nombre de trains en retard à l'arrivée": (
                "nb_train_retard_arrivee",
                "sum",
            ),
        }
    )

    # Get the aggregated train counts.
    prevus = resultats["Nombre de circulations prévues"]
    annules = resultats["Nombre de trains annulés"]
    retards = resultats["Nombre de trains en retard à l'arrivée"]

    # Calculate how many trains actually ran.
    circules = prevus - annules
    resultats["Trains circulés"] = circules

    # Share of operated trains that arrived late.
    resultats["Taux retard arrivée"] = retards / circules.replace(
        0, float("nan")
    )

    # Share of scheduled trains that were cancelled.
    resultats["Taux annulation"] = annules / prevus.replace(0, float("nan"))

    # Share of scheduled trains that ran without arrival delays.
    resultats["Taux fiabilité"] = (circules - retards) / prevus.replace(
        0, float("nan")
    )

    # Sort months chronologically for each route.
    resultats = resultats.sort_values(["Liaison", "Mois"]).reset_index(
        drop=True
    )

    # Replace month numbers with names.
    resultats["Mois"] = resultats["Mois"].map(mois)

    # Save the metrics CSV if an output path is provided.
    if sortie is not None:
        resultats.to_csv(sortie, sep=";", index=False)
        print(f"CSV créé : {sortie} ({len(resultats)} lignes)")

    # Return the calculated metrics.
    return resultats
