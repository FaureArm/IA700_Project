"""Create dashboards to be displayed by our steamlit app."""

import pandas as pd
import streamlit as st

from ia700_project.cleaning import (
    convert_dates,
    drop_empty_columns,
    fix_average_delays,
    fix_cause_percentages,
    fix_postcovid_anomalies,
    fix_precovid_anomalies,
    merge_duplicate_pairs,
    percentage_causes,
)
from ia700_project.indicators import (
    avg_delay_length,
    cancellation_rate,
    cause_of_delays_ranking,
    comparison_time_chart,
    compute_overview_summary,
    delay_rate,
    ranking,
    scheduled_trains_count,
    time_chart,
)
from ia700_project.map_view import render_tgv_map
from ia700_project.methods_examples import build_cleaning_examples
from ia700_project.models import ComparisonSelection, TravelSelection

# Keep the same metric colours across the exploration charts.
CANCELLATION_COLOR = "#971B4C"
DELAY_COLOR = "#B97716"

### MAIN PAGE ###


def render_overview_dashboard(data: pd.DataFrame) -> None:
    """Render the network metrics and interactive map."""
    # st.caption(f"Vérification · {len(data):,} observations reçues.")
    overview_summary = compute_overview_summary(data)
    render_overview_metrics(overview_summary)
    # to render some generic values on top, could be switched to a sidebar,
    # or smth else perhaps idk?
    render_network_map(data)  # to render the map with overlay


def render_network_map(data: pd.DataFrame) -> None:
    """Add the network heading and interactive map to the overview."""
    st.subheader("Le réseau en un regard")
    render_tgv_map(data)


def render_overview_metrics(overview_summary: pd.DataFrame | None) -> None:
    """Display the dataset overview returned by the calculation."""
    route_count_label = "—"
    station_count_label = "—"

    if overview_summary is None:
        st.caption("Aucune donnée exploitable pour les indicateurs du réseau.")
    elif overview_summary.empty:
        st.caption("Aucune donnée exploitable pour les indicateurs du réseau.")
    else:
        summary = overview_summary.iloc[0]

        route_count_label = f"{int(summary['route_count']):,}".replace(
            ",", " "
        )
        station_count_label = f"{int(summary['station_count']):,}".replace(
            ",", " "
        )

    routes_column, stations_column = st.columns(2, border=True)

    routes_column.metric("Liaisons couvertes", route_count_label)
    stations_column.metric("Gares représentées", station_count_label)


### EXPLORATION PAGE ###


def render_exploration_dashboard(
    data: pd.DataFrame, selection: TravelSelection
) -> None:
    """Render the summary and history for the selected journey.

    Args:
        data (pd.DataFrame): _description_
        selection (TravelSelection): _description_
    """
    render_travel_summary(selection)
    render_summary_metrics(data, selection)

    left, right = st.columns(2)

    with left:
        monthly_history = time_chart(data, selection)
        render_exploration_time_evolution(monthly_history)

    with right:
        delay_causes = cause_of_delays_ranking(data, selection)
        render_delay_causes(delay_causes)

    with st.expander("Comprendre les résultats"):
        st.write(
            "Le bilan et les causes portent sur les saisons complètes "
            "correspondant aux dates du voyage. "
            "La courbe mensuelle présente l’historique complet "
            "de la liaison."
        )


def render_travel_summary(selection: TravelSelection) -> None:
    """Display the selected route and travel dates.

    Args:
        selection (TravelSelection): _description_
    """
    st.subheader(f"{selection.departure} → {selection.arrival}")
    st.write(
        f"Voyage du {selection.travel_start:%d/%m/%Y} "
        f"au {selection.travel_end:%d/%m/%Y}"
    )


def render_summary_metrics(
    data: pd.DataFrame, selection: TravelSelection
) -> None:
    """Display train volume, cancellation, and arrival delay metrics.

    Args:
        data (pd.DataFrame): _description_
        selection (TravelSelection): _description_
    """
    st.subheader("Que montre l’historique ?")

    train_count = scheduled_trains_count(data, selection)
    cancellation_pct = cancellation_rate(data, selection)
    delay_pct = delay_rate(data, selection)
    average_delay_minutes = avg_delay_length(data, selection)

    volume, cancellations, delays, duration = st.columns(4, border=True)
    volume.metric(
        "Circulations prévues",
        f"{train_count:,}".replace(",", " ")
        if pd.notna(train_count)
        else "Indisponible",
    )
    cancellations.metric(
        "Taux d’annulation",
        f"{cancellation_pct:.2f} %"
        if pd.notna(cancellation_pct)
        else "Indisponible",
    )
    delays.metric(
        "Taux de retard à l’arrivée",
        f"{delay_pct:.2f} %" if pd.notna(delay_pct) else "Indisponible",
    )
    duration.metric(
        "Retard moyen à l’arrivée",
        f"{average_delay_minutes:.1f} min"
        if pd.notna(average_delay_minutes)
        else "Indisponible",
    )


def render_exploration_time_evolution(
    monthly_history: pd.DataFrame | None,
) -> None:
    """Display the monthly history returned by the calculation."""
    st.subheader("Évolution dans le temps")

    if monthly_history is None or monthly_history.empty:
        st.info("Aucun historique mensuel disponible pour cette liaison.")
        return
    chart_data = monthly_history.sort_values("month").set_index("month")

    st.line_chart(
        chart_data[["cancellation_rate_pct", "arrival_delay_rate_pct"]].rename(
            columns={
                "cancellation_rate_pct": "Annulations",
                "arrival_delay_rate_pct": "Retards à l’arrivée",
            }
        ),
        x_label="Mois",
        y_label="Taux (%)",
        color=[CANCELLATION_COLOR, DELAY_COLOR],
    )

    st.line_chart(
        chart_data[["mean_arrival_delay_minutes"]].rename(
            columns={
                "mean_arrival_delay_minutes": "Retard moyen à l’arrivée",
            }
        ),
        x_label="Mois",
        y_label="Minutes",
        color=DELAY_COLOR,
    )


def render_delay_causes(delay_causes: pd.DataFrame | None) -> None:
    """Display the delay causes returned by the calculation."""
    st.subheader("Causes des retards")

    if delay_causes is None or delay_causes.empty:
        st.info("Aucune répartition des causes disponible.")
        return

    # need to specifically name cols bc otherwise
    # takes the df col names, not UI friendly
    st.dataframe(
        delay_causes,
        hide_index=True,
        column_config={
            "cause": st.column_config.TextColumn(
                "Cause du retard",
            ),
            "percentage": st.column_config.NumberColumn(
                "Part des retards (%)",
                format="%.2f",
            ),
        },
    )


### COMPARISON PAGE ###


def render_comparison_dashboard(
    data: pd.DataFrame, selection: ComparisonSelection
) -> None:
    """Render the ranking and monthly trends for the comparison.

    Args:
        data (pd.DataFrame): _description_
        selection (ComparisonSelection): _description_
    """
    ranking_data = ranking(data, selection)
    render_ranking(ranking_data, selection)

    if ranking_data is None or ranking_data.empty:
        monthly_history = ranking_data
    else:
        monthly_history = comparison_time_chart(data, selection, ranking_data)

    render_comparison_time_evolution(monthly_history, selection)

    with st.expander("Comment lire cette comparaison ?"):
        st.write(
            "Le classement porte sur l’historique disponible, avec le "
            "volume minimal de circulations sélectionné. Les valeurs les "
            "plus élevées apparaissent en premier. Chaque couleur de la "
            "courbe représente une liaison ou une gare du classement ; "
            "les indicateurs sont recalculés mois par mois."
        )


def render_ranking(
    ranking_data: pd.DataFrame | None,
    selection: ComparisonSelection,
) -> None:
    """Display the ranking for the selected metric.

    Args:
        ranking_data (pd.DataFrame | None): _description_
        selection (ComparisonSelection): _description_
    """
    st.subheader(f"Classement · {selection.entity}")
    st.caption(
        f"{selection.metric} · {selection.top_n} résultats maximum · "
        f"minimum {selection.min_volume} circulations prévues"
    )

    # here we differentiate between missing data
    # and a empty search function, unlike other dashboards
    if ranking_data is None:
        st.info("Aucunes données disponibles.")
        return

    if ranking_data.empty:
        st.info("Aucun résultat ne correspond aux critères sélectionnés.")
        return
    # need to specifically name cols bc otherwise
    # takes the df col names, not UI friendly
    # in this scenario, need to take into account selection units
    entity_label = {
        "Liaisons": "Liaison",
        "Gares de départ": "Gare de départ",
        "Gares d’arrivée": "Gare d’arrivée",
    }[selection.entity]

    is_duration = selection.metric == "Retard moyen à l’arrivée"
    unit = "min" if is_duration else "%"
    value_format = "%.1f" if is_duration else "%.2f"

    st.dataframe(
        ranking_data,
        hide_index=True,
        column_config={
            "rank": st.column_config.NumberColumn(
                "Rang",
                format="%d",
            ),
            "entity": st.column_config.TextColumn(
                entity_label,
                width="large",
            ),
            "value": st.column_config.NumberColumn(
                f"{selection.metric} ({unit})",
                format=value_format,
            ),
            "scheduled_train_count": st.column_config.NumberColumn(
                "Circulations prévues",
                format="%d",
            ),
        },
    )


def render_comparison_time_evolution(
    monthly_history: pd.DataFrame | None,
    selection: ComparisonSelection,
) -> None:
    """Plot the monthly values for the compared routes or stations.

    Args:
        monthly_history (pd.DataFrame | None): _description_
        selection (ComparisonSelection): _description_
    """
    st.subheader("Comparer les évolutions")

    # here we differentiate between missing data
    # and a empty search function, unlike other dashboards
    if monthly_history is None:
        st.info("Aucunes données disponibles.")
        return

    if monthly_history.empty:
        st.info("Aucun historique disponible pour cette comparaison.")
        return

    # plot our chart
    chart_data = monthly_history.pivot(
        index="month",
        columns="entity",
        values="value",
    ).sort_index()

    unit = (
        "Minutes"
        if selection.metric == "Retard moyen à l’arrivée"
        else "Taux (%)"
    )

    st.line_chart(chart_data, x_label="Mois", y_label=unit)


### METHODS PAGE ###
# Reference figures describe the studied export, not the loaded dataset.
# Fictional examples use the same cleaning functions as the application.


def render_data_source_dashboard() -> None:
    """Present the source, observation unit and reference export."""
    st.subheader("1. Comprendre les données")
    st.markdown(
        "La SNCF publie chaque mois les résultats de régularité TGV "
        "dans le cadre du suivi AQST. **Une ligne correspond à un mois "
        "et à une liaison orientée**, avec un service National ou "
        "International. Paris → Lyon et Lyon → Paris sont deux liaisons "
        "distinctes."
    )
    st.caption(
        "Repères de l’export étudié dans le notebook EDA : "
        "janvier 2018 à septembre 2026. Ces chiffres décrivent cet export "
        "de référence, pas un calcul sur le fichier actuellement chargé."
    )
    st.markdown(
        "[Consulter le jeu de données SNCF Open Data]"
        "(https://ressources.data.sncf.com/explore/dataset/"
        "regularite-mensuelle-tgv-aqst/information/)"
    )

    raw, cleaned, routes = st.columns(3, border=True)
    raw.metric("Avant préparation", "12 907 lignes")
    cleaned.metric("Après préparation", "12 865 lignes")
    routes.metric("Liaisons orientées", "130")

    with st.expander("Quelles informations contient une ligne ?"):
        st.dataframe(
            pd.DataFrame(
                {
                    "Famille": [
                        "Repérage",
                        "Volumes",
                        "Durée du trajet",
                        "Retards moyens",
                        "Causes des retards",
                        "Commentaires",
                    ],
                    "Contenu": [
                        "Mois, gare de départ, gare d’arrivée, service",
                        "Trains prévus, annulés, en retard ; "
                        "seuils 15/30/60 min",
                        "Durée moyenne de la liaison, en minutes",
                        "Retards moyens au départ et à l’arrivée, pour "
                        "les trains retardés ou l’ensemble des trains ; "
                        "moyenne > 15 min sur les liaisons concurrencées "
                        "par l’avion",
                        "Six parts en % : externe, infrastructure, trafic, "
                        "matériel, gare, voyageurs",
                        "Texte explicatif lorsqu’il est renseigné",
                    ],
                }
            ),
            hide_index=True,
        )


def render_cleaning_dashboard() -> None:
    """Explain the preparation pipeline and illustrate its transformations."""
    st.subheader("2. Préparer sans inventer d’information")
    st.markdown(
        "**Importer → structurer → fusionner → contrôler → traiter.** "
        "Le fichier source reste intact : les transformations produisent "
        "une nouvelle table en mémoire."
    )
    st.dataframe(
        pd.DataFrame(
            {
                "Étape": [
                    "Harmoniser les colonnes",
                    "Retirer les colonnes vides",
                    "Préparer les dates",
                    "Fusionner les doubles entrées",
                ],
                "Décision": [
                    "Accepter les en-têtes techniques "
                    "ou les libellés français",
                    "26 → 24 colonnes : les commentaires d’annulation et "
                    "de retard au départ sont entièrement vides",
                    "Convertir les mois en dates et trier chronologiquement",
                    "42 paires National/International de juillet à septembre "
                    "2025 deviennent chacune une ligne National",
                ],
            }
        ),
        hide_index=True,
    )
    st.write(
        "Pour fusionner deux lignes, on additionne les compteurs. "
        "Les moyennes et pourcentages sont pondérés par le volume "
        "correspondant : trains prévus pour la durée du trajet, trains "
        "retardés pour le retard moyen et les causes. Les commentaires "
        "sont réunis."
    )
    st.write(
        "Les commentaires à l’arrivée sont conservés sans les compléter : "
        "698 textes, uniquement en 2018–2019, puis aucun à partir de 2020. "
        "Cette absence dépend de la période de publication ; un commentaire "
        "manquant ne signifie donc pas qu’il n’y a pas eu d’incident."
    )

    with st.expander("Voir des exemples avant / après", expanded=True):
        render_cleaning_example()


def render_cleaning_example() -> None:
    """Apply the existing cleaning functions to clearly fictional rows."""
    st.caption(
        "Exemples fictifs et simplifiés, calculés avec les mêmes fonctions "
        "de nettoyage que l’application. Ils ne sont pas des observations "
        "SNCF et ne contribuent pas aux indicateurs. « — » signifie manquant."
    )
    examples = build_cleaning_examples()

    # Extend the existing fictional inputs without loading the SNCF export.
    examples["Compteurs avant COVID"] = (
        examples["Structure et dates"]
        .iloc[:1]
        .assign(
            date="2019-01",
            nb_train_retard_arrivee=5,
            nb_train_retard_sup_15=8,
            nb_train_retard_sup_30=3,
            nb_train_retard_sup_60=1,
        )
    )
    average_example = (
        examples["Structure et dates"]
        .iloc[:1]
        .assign(
            retard_moyen_depart=10.0,
            retard_moyen_tous_trains_depart=2.0,
            retard_moyen_arrivee=20.0,
            retard_moyen_tous_trains_arrivee=4.0,
            retard_moyen_trains_retard_sup15=25.0,
        )
    )
    examples["Moyennes de retard"] = pd.concat(
        [average_example] * 3, ignore_index=True
    ).assign(
        gare_depart=["Moyenne négative", "Zéro avec retards", "Cas cohérent"],
        retard_moyen_arrivee=[-5.0, 0.0, 20.0],
        retard_moyen_tous_trains_arrivee=[-1.0, 0.0, 4.0],
    )
    examples["Moyenne des retards > 15 min"] = pd.concat(
        [average_example] * 4, ignore_index=True
    ).assign(
        gare_depart=[
            "Sous le seuil",
            "Aucun train > 15 min",
            "Cas cohérent",
            "Compteur inconnu",
        ],
        nb_train_retard_sup_15=[5.0, 0.0, 5.0, float("nan")],
        nb_train_retard_sup_30=[3, 0, 3, 3],
        nb_train_retard_sup_60=[1, 0, 1, 1],
        retard_moyen_trains_retard_sup15=[6.0, 7.0, 25.0, 6.0],
    )
    example = st.selectbox(
        "Transformation à observer", list(examples), key="methods_example"
    )
    before = examples[example]

    # Only the structure example starts with unparsed dates.
    if example == "Structure et dates":
        after = drop_empty_columns(convert_dates(before))
        columns = [
            "date",
            "commentaire_annulation",
            "commentaire_retards_depart",
            "commentaires_retard_arrivee",
        ]
        st.write(
            "Les mois sont triés et convertis en dates. Les deux colonnes "
            "sans aucune valeur disparaissent ; le commentaire renseigné "
            "à l’arrivée est conservé."
        )
    elif example == "Fusion des doublons":
        before = convert_dates(before)
        after = merge_duplicate_pairs(before)
        columns = [
            "service",
            "nb_train_prevu",
            "nb_train_retard_arrivee",
            "retard_moyen_arrivee",
            "commentaires_retard_arrivee",
        ]
        st.write(
            "Même mois, même liaison : 100 + 50 = 150 trains prévus. "
            "Le retard moyen devient (20 × 20 + 50 × 10) / (20 + 10) "
            "= 30 minutes, pondéré par les trains en retard."
        )
    elif example == "Compteurs incohérents":
        before = convert_dates(before)
        after = fix_postcovid_anomalies(before)
        columns = [
            "gare_depart",
            "nb_train_retard_sup_15",
            "nb_train_retard_sup_30",
            "nb_train_retard_sup_60",
        ]
        st.write(
            "Si le compteur > 30 min dépasse celui > 15 min en 2025, "
            "le compteur > 15 min est rendu manquant. Si le compteur "
            "> 60 min dépasse celui > 30 min, celui > 30 min est rendu "
            "manquant. La vraie valeur reste inconnue."
        )
    elif example == "Compteurs avant COVID":
        before = convert_dates(before)
        after = fix_precovid_anomalies(before)
        columns = ["date", "nb_train_retard_arrivee", "nb_train_retard_sup_15"]
        st.write(
            "Avant mars 2020, lorsque le compteur > 15 min dépasse "
            "le total des retards à l’arrivée, ce total est porté au "
            "niveau du compteur > 15 min. Ici, 5 devient 8 ; "
            "le compteur > 15 min reste inchangé."
        )
    elif example == "Moyennes de retard":
        before = convert_dates(before)
        after = fix_average_delays(before)
        columns = [
            "gare_depart",
            "nb_train_retard_arrivee",
            "retard_moyen_arrivee",
            "retard_moyen_tous_trains_arrivee",
        ]
        st.write(
            "Les moyennes négatives deviennent manquantes. Les moyennes "
            "nulles deviennent aussi manquantes lorsque le compteur "
            "correspondant indique des trains retardés. La même règle "
            "est appliquée au départ et à l’arrivée, aux trains retardés "
            "comme à l’ensemble des trains."
        )
    elif example == "Moyenne des retards > 15 min":
        before = convert_dates(before)
        after = fix_average_delays(before)
        columns = [
            "gare_depart",
            "nb_train_retard_sup_15",
            "retard_moyen_trains_retard_sup15",
        ]
        st.write(
            "Si le compteur > 15 min est positif, une moyenne inférieure "
            "à 15 devient 15. Si ce compteur vaut zéro, la moyenne devient "
            "zéro. Si le compteur est inconnu, cette règle ne modifie pas "
            "la moyenne. Le seuil de 15 est un ajustement imposé, "
            "pas une reconstitution du retard réel."
        )
    else:
        before = convert_dates(before)
        after = fix_cause_percentages(before)
        columns = ["gare_depart", "nb_train_retard_arrivee"]
        columns += percentage_causes
        st.write(
            "Avec des trains retardés, une somme inférieure à 90 % rend "
            "les six causes manquantes. Une somme de 95 % est conservée "
            "sans la ramener à 100 %. Zéro sans train retardé reste zéro. "
            "Les causes autres qu’externes valent zéro dans cet exemple."
        )

    # Keep technical IDs out of the example tables.
    labels = {
        "date": "Mois",
        "service": "Service",
        "gare_depart": "Cas / départ",
        "nb_train_prevu": "Trains prévus",
        "nb_train_retard_arrivee": "Trains en retard",
        "retard_moyen_arrivee": "Retard moyen (min)",
        "retard_moyen_tous_trains_arrivee": "Moyenne tous trains (min)",
        "retard_moyen_trains_retard_sup15": "Moyenne > 15 min (min)",
        "nb_train_retard_sup_15": "> 15 min",
        "nb_train_retard_sup_30": "> 30 min",
        "nb_train_retard_sup_60": "> 60 min",
        "commentaire_annulation": "Commentaire annulation",
        "commentaire_retards_depart": "Commentaire départ",
        "commentaires_retard_arrivee": "Commentaire arrivée",
        "prct_cause_externe": "Externe (%)",
        "prct_cause_infra": "Infrastructure (%)",
        "prct_cause_gestion_trafic": "Trafic (%)",
        "prct_cause_materiel_roulant": "Matériel (%)",
        "prct_cause_gestion_gare": "Gare (%)",
        "prct_cause_prise_en_charge_voyageurs": "Voyageurs (%)",
    }
    left, right = st.columns(2)
    for container, title, frame in (
        (left, "Avant", before),
        (right, "Après", after),
    ):
        with container:
            st.markdown(f"**{title}**")
            visible_columns = [c for c in columns if c in frame.columns]
            st.dataframe(
                frame[visible_columns].rename(columns=labels), hide_index=True
            )


def render_quality_dashboard() -> None:
    """Describe consistency findings and the decisions taken in the EDA."""
    st.subheader("3. Contrôler la cohérence, décider au cas par cas")
    st.write(
        "On vérifie que les compteurs sont positifs ou nuls, que les "
        "annulations ne dépassent pas les trains prévus et que les retards "
        "ne dépassent pas les trains ayant circulé. Les seuils doivent "
        "s’emboîter : > 60 min ≤ > 30 min ≤ > 15 min ≤ retards à l’arrivée. "
        "La durée moyenne du trajet doit être strictement positive. "
        "Le traitement contrôle aussi les moyennes négatives, les "
        "moyennes nulles associées à des trains retardés et les moyennes "
        "du champ > 15 min inférieures à ce seuil."
    )
    st.caption(
        "Bilan des contrôles sur l’export de référence, après fusion "
        "des doublons et avant "
        "traitement des anomalies. Une ligne peut enfreindre plusieurs "
        "règles : les nombres ci-dessous ne s’additionnent pas en un "
        "nombre de lignes distinctes."
    )
    with st.expander("Voir le bilan des contrôles"):
        st.dataframe(
            pd.DataFrame(
                {
                    "Règle enfreinte": [
                        "Compteur négatif",
                        "Aucun train prévu",
                        "Annulations > trains prévus",
                        "Retards au départ > trains ayant circulé",
                        "Retards à l’arrivée > trains ayant circulé",
                        "> 15 min > retards à l’arrivée",
                        "> 30 min > > 15 min",
                        "> 60 min > > 30 min",
                        "Durée moyenne nulle ou négative",
                        "Au moins une moyenne de retard négative",
                        "Moyenne des trains retardés nulle avec retards",
                        "Moyenne tous trains nulle avec retards",
                        "Moyenne > 15 min sous le seuil (zéros inclus)",
                    ],
                    "Lignes concernées": [
                        43,
                        73,
                        63,
                        64,
                        63,
                        31,
                        3,
                        354,
                        73,
                        277,
                        38,
                        1,
                        2174,
                    ],
                }
            ),
            hide_index=True,
        )

    with st.expander("2020 : préserver la période COVID"):
        st.write(
            "Les restrictions ont fortement perturbé les circulations. "
            "Les 73 lignes sans train prévu sont conservées pour documenter "
            "cette période ; elles sont exclues des calculs de taux. "
            "Le nettoyage ne supprime pas les observations exceptionnelles "
            "et ne résout pas toutes les incohérences : les calculs de "
            "taux écartent les volumes incompatibles avec leur définition."
        )

    with st.expander("Avant COVID : ajuster les compteurs d’arrivée"):
        st.write(
            "Sur 13 lignes de 2018–2019, le compteur > 15 min dépasse "
            "le total des retards à l’arrivée. Le nettoyage porte "
            "ce total au niveau du compteur > 15 min. Cette règle "
            "s’applique aux observations antérieures à mars 2020."
        )
        before, after = st.columns(2, border=True)
        before.metric("Taux national sans correction", "14,6583 %")
        after.metric("Taux national après ajustement", "14,6595 %")
        st.write(
            "L’écart est de 0,0012 point de pourcentage sur l’export étudié. "
            "Le test de sensibilité mesure cet effet avant que "
            "l’ajustement soit effectivement appliqué au jeu nettoyé."
        )

    with st.expander("2025 : rendre manquants les compteurs irrécupérables"):
        st.write(
            "À Tours → Paris Montparnasse en mars 2025, le compteur "
            "> 15 min est incohérent : 1 valeur devient manquante. "
            "354 valeurs du compteur > 30 min sont aussi rendues "
            "manquantes, car inférieures au compteur > 60 min. "
            "Les autres informations de ces lignes restent disponibles. "
            "Manquant signifie inconnu, jamais zéro retard."
        )

    with st.expander("Causes : distinguer zéro et absence d’information"):
        st.write(
            "Dans l’export étudié, 12 584 répartitions totalisent 100 % "
            "à ±0,1 point près ; 191 lignes ont zéro cause et aucun "
            "train retardé, ce qui est cohérent. En revanche, 80 lignes "
            "ont des retards sans cause renseignée et 3 ont une somme "
            "inférieure à 90 % : leurs six causes deviennent manquantes "
            "(83 lignes). Les 7 répartitions partielles proches de 100 % "
            "sont conservées sans renormalisation, pour ne pas attribuer "
            "une cause aux trains non classés."
        )

    with st.expander("Moyennes de retard : traiter les valeurs aberrantes"):
        st.write(
            "Pour les moyennes au départ et à l’arrivée, sur les trains "
            "retardés ou sur tous les trains, le nettoyage remplace les "
            "valeurs négatives par des valeurs manquantes. Il fait de "
            "même pour une moyenne nulle si le compteur correspondant "
            "indique au moins un train retardé. Sur l’export étudié, "
            "cela rend manquantes 40 moyennes des trains retardés "
            "à l’arrivée : 2 négatives et 38 nulles malgré des retards."
        )
        st.write(
            "Le champ de moyenne des retards > 15 min suit une autre "
            "règle : si le compteur > 15 min est positif, une moyenne "
            "inférieure à 15 est portée à 15 ; si ce compteur vaut zéro, "
            "la moyenne est fixée à zéro. Un compteur manquant ne "
            "déclenche aucun de ces deux ajustements."
        )
        st.caption(
            "Sur l’export de référence : 1 952 moyennes portées à 15 min "
            "et 16 remises à zéro. Le contrôle initial signale 2 174 "
            "moyennes sous 15 min, y compris des zéros sans train "
            "retardé au-delà de ce seuil : ce nombre ne représente "
            "donc pas le nombre de valeurs portées à 15."
        )
        st.write(
            "Le seuil imposé de 15 min ne restitue pas la moyenne réelle. "
            "Ce champ n’entre pas dans les indicateurs affichés. Pour "
            "le retard moyen à l’arrivée, les mois dont la moyenne est "
            "manquante sont exclus du calcul, ainsi que leurs poids. "
            "Le taux de retard peut rester disponible sur ces mêmes mois."
        )


def render_methodology_dashboard() -> None:
    """Explain indicator definitions, aggregation and interpretation limits."""
    st.subheader("4. Lire les indicateurs avec les bons repères")
    st.markdown(
        "- **Trains ayant circulé** = trains prévus − trains annulés.\n"
        "- **Taux d’annulation** = 100 × annulations / trains prévus.\n"
        "- **Taux de retard à l’arrivée** = 100 × trains en retard / "
        "trains ayant circulé.\n"
        "- **Retard moyen à l’arrivée** : moyenne des retards des seuls "
        "trains retardés, pondérée par leur nombre."
    )
    st.write(
        "Pour regrouper plusieurs mois ou liaisons, les taux sont calculés "
        "à partir des sommes des compteurs, et les retards moyens sont "
        "pondérés par les trains retardés. Un petit mois ne pèse donc pas "
        "autant qu’un mois très fréquenté. Si le dénominateur est nul ou "
        "les valeurs inutilisables, le résultat est indisponible."
    )

    with st.expander("Qu’est-ce qu’un train en retard pour la SNCF ?"):
        st.write(
            "La régularité composite utilise un seuil lié à la durée "
            "du trajet : 5 minutes pour moins de 1 h 30, 10 minutes "
            "de 1 h 30 à 3 h, et 15 minutes au-delà de 3 h. "
            "Le taux de retard à l’arrivée ne correspond donc pas "
            "systématiquement aux seuls retards de plus de 15 minutes."
        )

    with st.expander(
        "Comment les autres pages utilisent-elles l’historique ?"
    ):
        st.write(
            "Explorer une liaison : les dates choisies sélectionnent "
            "les saisons historiques correspondantes, toutes années "
            "confondues (hiver : décembre–février ; printemps : mars–mai ; "
            "été : juin–août ; automne : septembre–novembre). La courbe "
            "mensuelle montre tout l’historique de la liaison. "
            "Les causes sont pondérées par le nombre de trains retardés, "
            "sur les répartitions exploitables totalisant 90 à 100,1 %."
        )
        st.write(
            "Comparer les liaisons : le classement utilise l’historique "
            "disponible et le volume minimal sélectionné. Les valeurs les "
            "plus élevées apparaissent en premier ; la courbe recalcule "
            "ensuite chaque indicateur mois par mois."
        )

    with st.container(border=True):
        st.markdown("**À garder en tête**")
        st.write(
            "Ces données mensuelles décrivent un historique : elles ne "
            "prédisent pas le retard d’un train précis et ne donnent pas "
            "l’état du trafic en temps réel. Les mois atypiques restent "
            "présents, les causes manquantes limitent leur interprétation "
            "et la couverture des liaisons peut évoluer dans le temps."
        )
    with st.expander("Autres précautions de lecture"):
        st.write(
            "La présence d’un commentaire ne sert pas d’indicateur de "
            "fiabilité. Le champ de retard moyen des trains > 15 min "
            "est distinct du retard moyen à l’arrivée affiché : "
            "ses ajustements à 15 min ou à zéro n’entrent pas dans "
            "les indicateurs. La répartition déclarée des causes ne suffit "
            "pas à établir une relation de causalité."
        )
