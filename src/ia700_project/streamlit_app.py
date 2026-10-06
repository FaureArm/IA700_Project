"""Explore la régularité mensuelle des TGV avec Streamlit.

Depuis la racine du dépôt :
    uv run streamlit run src/ia700_project/streamlit_app.py
"""

from pathlib import Path
import pandas as pd
import streamlit as st


# TODO: separate main streamlit functionalities into different files (eg: sidebar, title, graphs, cols, etc)
# TODO: add dataclasses to simplify returns of recurring features, ex: filter selection,
# TODO: create classes to  handle the different datasets/representations

DATA_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "regularite-mensuelle-tgv-aqst.csv"
)
PLANNED = "Nombre de circulations prévues"
CANCELLED = "Nombre de trains annulés"
DELAY = "Retard moyen de tous les trains à l'arrivée"
DEPARTURE = "Gare de départ"
ARRIVAL = "Gare d'arrivée"
ALL_STATIONS = "Toutes les gares"
TITLE = "Projet IA700"


@st.cache_data
def load_data(path: str, modified_at: int) -> tuple[pd.DataFrame, int]:
    """Lit le CSV SNCF et écarte les lignes inutilisables pour ces indicateurs.

    Args:
        path: Chemin du CSV séparé par des points-virgules.
        modified_at: Date de modification, utilisée pour invalider le cache.

    Returns:
        Données valides et nombre de lignes écartées.

    Raises:
        ValueError: Si des colonnes requises sont absentes.
    """
    df = pd.read_csv(path, sep=";")
    required = ["Date", DEPARTURE, ARRIVAL, PLANNED, CANCELLED, DELAY]
    missing = set(required).difference(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {', '.join(sorted(missing))}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for column in [PLANNED, CANCELLED, DELAY]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    valid = (
        df[required].notna().all(axis=1)
        & df[PLANNED].gt(0)
        & df[CANCELLED].ge(0)
        & df[CANCELLED].le(df[PLANNED])
        & df[DELAY].ge(0)
        & df[[PLANNED, CANCELLED, DELAY]].lt(float("inf")).all(axis=1)
    )
    return df.loc[valid].copy(), int((~valid).sum())


def monthly_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les annulations et pondère le retard par les trains ayant circulé."""
    prepared = df.assign(
        circulated=df[PLANNED] - df[CANCELLED],
        delay_minutes=df[DELAY] * (df[PLANNED] - df[CANCELLED]),
    )
    monthly = (
        prepared.groupby("Date")[[PLANNED, CANCELLED, "circulated", "delay_minutes"]]
        .sum()
        .sort_index()
    )
    monthly["Retard moyen à l'arrivée (min)"] = monthly["delay_minutes"] / monthly[
        "circulated"
    ].replace(0, float("nan"))
    monthly["Taux d'annulation (%)"] = monthly[CANCELLED] / monthly[PLANNED] * 100
    return monthly


def sidebar(df: pd.DataFrame) -> pd.DataFrame:
    ### Sidebar ###
    st.sidebar.header("Votre sélection")
    months = sorted(df["Date"].dt.strftime("%Y-%m").unique().tolist())
    if len(months) > 1:
        start, end = st.sidebar.select_slider(
            "Période", options=months, value=(months[0], months[-1]), key="period"
        )
    else:
        start = end = months[0]
        st.sidebar.caption(f"Période disponible : {start}")
    month_values = df["Date"].dt.strftime(
        "%Y-%m"
    )  # cut days from format since we only have months
    filtered = df.loc[month_values.between(start, end)].copy()

    departure = st.sidebar.selectbox(
        "Gare de départ",
        [ALL_STATIONS] + sorted(filtered[DEPARTURE].unique().tolist()),
        key="departure",
    )
    if departure != ALL_STATIONS:
        filtered = filtered.loc[filtered[DEPARTURE].eq(departure)]
    arrival = st.sidebar.selectbox(
        "Gare d'arrivée",
        [ALL_STATIONS] + sorted(filtered[ARRIVAL].unique().tolist()),
        key="arrival",
    )
    if arrival != ALL_STATIONS:
        filtered = filtered.loc[filtered[ARRIVAL].eq(arrival)]

    if filtered.empty:
        st.info("Aucune donnée disponible pour cette sélection.")
        st.stop()
    return filtered, start, end


def main() -> None:
    """Affiche les filtres, les indicateurs et deux graphiques temporels."""
    st.set_page_config(page_title="SNCF Regularity", page_icon="🚆", layout="wide")
    st.title(TITLE)
    st.markdown(
        "Explorez la régularité des TGV : **comment evolue la fiabilite des vos trajets TGV lors de vos departs ?**\n"
        " Sélectionnez vos dates de trajet ainsi que vos gares, et obtenez un apercu des risques de perturbations."
    )
    st.caption("Source : SNCF Open Data · Régularité mensuelle TGV (AQST)")

    try:
        df, excluded = load_data(
            str(DATA_PATH), DATA_PATH.stat().st_mtime_ns
        )  # see func load_data() to understand what are excluded lines
    except FileNotFoundError:
        st.error("Le jeu de données SNCF est absent.")
        st.info(
            "Placez regularite-mensuelle-tgv-aqst.csv dans le dossier data/ "
            "à la racine du projet. Ce fichier doit aussi être disponible sur l'hébergeur."
        )
        st.stop()
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.error(f"Impossible de lire les données SNCF : {error}")
        st.stop()

    if df.empty:
        st.warning(
            "Le fichier ne contient aucune ligne exploitable pour ces indicateurs."
        )
        st.stop()
    ### sidebar ###
    filtered, start, end = sidebar(df)

    ### Indicators ###
    monthly = monthly_indicators(filtered)
    planned = int(filtered[PLANNED].sum())
    cancelled = int(filtered[CANCELLED].sum())
    circulated = planned - cancelled
    delay = float(monthly["delay_minutes"].sum() / circulated) if circulated else None
    st.subheader(f"Votre bilan : {start} à {end}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Circulations prévues", f"{planned:,}".replace(",", " "))
    col2.metric("Taux d'annulation", f"{cancelled / planned * 100:.2f} %")
    col3.metric(
        "Retard moyen à l'arrivée",
        f"{delay:.1f} min" if delay is not None else "Indisponible",
    )
    st.caption(
        f"{len(filtered):,} observations mensuelles par liaison · "
        f"{filtered[[DEPARTURE, ARRIVAL]].drop_duplicates().shape[0]} liaisons orientées. "
        "Une circulation est comptée pour chaque liaison déclarée dans le dataset ; "
        "ces volumes ne représentent pas nécessairement des trains uniques sur le réseau."
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Comment évoluent les retards ?")
        st.line_chart(
            monthly[["Retard moyen à l'arrivée (min)"]],
            x_label="Mois",
            y_label="Minutes",
            color="#2563EB",
        )
        st.caption(
            "Retard moyen de tous les trains à l'arrivée, pondéré par le nombre "
            "de circulations réalisées sur chaque liaison."
        )
    with right:
        st.subheader("Quelle part des trains est annulée ?")
        st.line_chart(
            monthly[["Taux d'annulation (%)"]],
            x_label="Mois",
            y_label="Annulations (%)",
            color="#E97732",
        )
        st.caption(
            "Nombre total d'annulations / nombre total de circulations prévues × 100."
        )

    with st.expander("Voir les données de la sélection"):
        st.dataframe(filtered, hide_index=True)
    with st.expander("Comprendre les calculs"):
        st.markdown("Lorem ipsum blablabla")
        st.caption(f"{excluded} lignes écartées sur le fichier complet.")
    st.markdown(
        "[Consulter le jeu de données SNCF](https://ressources.data.sncf.com/"
        "explore/dataset/regularite-mensuelle-tgv-aqst/information/)"
    )


if __name__ == "__main__":
    main()
