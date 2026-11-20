"""Build fictional inputs for the cleaning examples on the methods page.

These small datasets illustrate the existing cleaning functions. They are
independent from the SNCF export and never enter the application indicators.
"""

import pandas as pd

from ia700_project.cleaning import (
    counter_cols,
    percentage_causes,
    raw_cols,
    weighted_cols,
)


def build_cleaning_examples() -> dict[str, pd.DataFrame]:
    """Return raw example rows for each documented cleaning operation."""
    # Default to a coherent monthly observation, with two empty columns.
    base = dict.fromkeys(raw_cols, pd.NA)
    base.update(dict.fromkeys(counter_cols, 0))
    base.update(dict.fromkeys(weighted_cols, 0.0))
    base.update(
        {
            "date": "2025-03",
            "service": "National",
            "gare_depart": "Gare A",
            "gare_arrivee": "Gare B",
            "nb_train_prevu": 100,
            "nb_annulation": 5,
            "nb_train_depart_retard": 20,
            "nb_train_retard_arrivee": 20,
            "nb_train_retard_sup_15": 15,
            "nb_train_retard_sup_30": 8,
            "nb_train_retard_sup_60": 3,
            "duree_moyenne": 120.0,
            "retard_moyen_arrivee": 20.0,
            "prct_cause_externe": 100.0,
        }
    )

    examples = {
        "Structure et dates": [
            {"date": "2025-02"},
            {"date": "2025-01", "commentaires_retard_arrivee": "Incident"},
        ],
        "Fusion des doublons": [
            {"date": "2025-07", "commentaires_retard_arrivee": "Incident A"},
            {
                "date": "2025-07",
                "service": "International",
                "nb_train_prevu": 50,
                "nb_train_retard_arrivee": 10,
                "retard_moyen_arrivee": 50.0,
                "nb_train_retard_sup_15": 8,
                "nb_train_retard_sup_30": 5,
                "commentaires_retard_arrivee": "Incident B",
            },
        ],
        "Compteurs incohérents": [
            {"nb_train_retard_sup_15": 2, "nb_train_retard_sup_30": 6},
            {
                "gare_depart": "Gare C",
                "nb_train_retard_sup_30": -2,
                "nb_train_retard_sup_60": 3,
            },
        ],
        "Causes des retards": [
            {"gare_depart": "Somme : 100 %"},
            {"gare_depart": "Somme : 95 %", "prct_cause_externe": 95.0},
            {"gare_depart": "Somme : 85 %", "prct_cause_externe": 85.0},
            {
                "gare_depart": "Somme : 0 %, avec retard",
                "prct_cause_externe": 0.0,
            },
            {
                "gare_depart": "Somme : 0 %, sans retard",
                "nb_train_retard_arrivee": 0,
                "nb_train_retard_sup_15": 0,
                "nb_train_retard_sup_30": 0,
                "nb_train_retard_sup_60": 0,
                **dict.fromkeys(percentage_causes, 0.0),
            },
        ],
    }

    return {
        name: pd.DataFrame([{**base, **row} for row in rows], columns=raw_cols)
        for name, rows in examples.items()
    }
