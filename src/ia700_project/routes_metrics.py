from pathlib import Path
import pandas as pd

def creer_csv_metriques(
    entree: str | Path,
    sortie: str | Path | None = None,
) -> pd.DataFrame:
    """
    Create seasonal metrics for each train route.

    Uses the already cleaned SNCF dataset and groups all years
    together by route and season.

    Args:
        entree: Path to the cleaned input CSV.
        sortie: Optional path to save the metrics CSV.

    Returns:
        DataFrame with train counts, delay rates, cancellation
        rates, and reliability rates for each route and season.
    """

    # Load the cleaned dataset
    df = pd.read_csv(entree, sep=";")

    # Convert dates to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Create a route label from departure and arrival stations
    df["Liaison"] = df["gare_depart"] + " -> " + df["gare_arrivee"]

    # Match each month to its season
    saisons = {
        12: "Hiver", 1: "Hiver", 2: "Hiver",
        3: "Printemps", 4: "Printemps", 5: "Printemps",
        6: "Été", 7: "Été", 8: "Été",
        9: "Automne", 10: "Automne", 11: "Automne",
    }

    # Assign a season to each row
    df["Saison"] = df["date"].dt.month.map(saisons)

    # Sum train counts by route and season across all years
    resultats = (
        df.groupby(["Liaison", "Saison"], as_index=False)
        .agg(
            **{
                "Nombre de circulations prévues": ("nb_train_prevu", "sum"),
                "Nombre de trains annulés": ("nb_annulation", "sum"),
                "Nombre de trains en retard à l'arrivée": ("nb_train_retard_arrivee", "sum"),
            }
        )
    )

    # Get the aggregated train counts
    prevus = resultats["Nombre de circulations prévues"]
    annules = resultats["Nombre de trains annulés"]
    retards = resultats["Nombre de trains en retard à l'arrivée"]

    # Calculate how many trains actually ran
    circules = prevus - annules

    # Store the number of operated trains
    resultats["Trains circulés"] = circules

    # Share of operated trains that arrived late
    resultats["Taux retard arrivée"] = (
        retards / circules.replace(0, float("nan"))
    )

    # Share of scheduled trains that were cancelled
    resultats["Taux annulation"] = (
        annules / prevus.replace(0, float("nan"))
    )

    # Share of scheduled trains that ran without arrival delays
    resultats["Taux fiabilité"] = (
        (circules - retards) / prevus.replace(0, float("nan"))
    )

    # Save the metrics CSV if an output path is provided
    if sortie is not None:
        resultats.to_csv(sortie, sep=";", index=False)
        print(f"CSV créé : {sortie} ({len(resultats)} lignes)")

    # Return the calculated metrics
    return resultats