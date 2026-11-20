"""Download and set up the data required for this project.

This module downloads the main SNCF monthly TGV regularity dataset.
Additional datasets, such as weather and holidays, may be added later.

Users can also download datasets manually and place them in the
'data' folder.
"""

from pathlib import Path

import requests

TGV_REGULARITY_URL = "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/regularite-mensuelle-tgv-aqst/exports/csv?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"
TGV_REGULARITY_PATH = "data/regularite-mensuelle-tgv-aqst.csv"


def download_data():
    """Download and set up the required project dataset."""
    # NB: this likely results in a timeout;
    # This file serves more as an example for later files,
    # can simply be deleting later on cause not that useful
    print(f"Downloading data to {TGV_REGULARITY_PATH}")
    output_path = Path(TGV_REGULARITY_PATH)

    response = requests.get(TGV_REGULARITY_URL, timeout=30)
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)


if __name__ == "__main__":
    download_data()
