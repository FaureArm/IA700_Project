# Datasheet — Régularité mensuelle TGV (AQST)

This datasheet documents the SNCF open dataset *Régularité mensuelle
TGV par liaisons (AQST)* as used by the RailInsight project (IA700,
Télécom Paris). It follows the question template of Gebru et al.,
*Datasheets for Datasets* (arXiv:1803.09010v8, 2021).

| Item | Value |
| --- | --- |
| Dataset | Régularité mensuelle TGV par liaisons (AQST) |
| Version used | CSV export retrieved in November 2026 |
| Raw size | 12,907 rows × 26 columns |
| Period covered | 2018-01 to 2026-09 |
| Cleaned size | 12,865 rows × 24 columns |
| Datasheet authors | RailInsight team (IA700 project) |
| Reference implementation | `notebooks/EDA.ipynb`, `src/ia700_project/cleaning.py` |

## 1. Motivation

**For what purpose was the dataset created?**
SNCF, the French national railway operator, publishes this dataset
monthly on its open data portal to document the regularity (on-time
performance) of its TGV services, as part of the AQST quality-of-
service reporting framework. In this project it is used to explore
and explain TGV punctuality, first through an EDA and cleaning
phase, then through an interactive Streamlit application.

**Who created the dataset and on behalf of which entity?**
SNCF, published on the SNCF open data portal
(ressources.data.sncf.com) and referenced on data.gouv.fr.

**Who funded the creation of the dataset?**
SNCF.

## 2. Composition

**What do the instances represent?**
One instance is one month × one directional TGV route (departure
station → arrival station), with a service label (National or
International). The same route appears once per month.

**How many instances are there?**
12,907 raw rows in the version used, covering January 2018 to
September 2026. After cleaning: 12,865 rows (11,339 National,
1,526 International).

**Is the dataset complete or a sample?**
It is not a sample: every commercial TGV route operated in a given
month appears in that month. Coverage therefore follows the actual
network (route openings/closures appear as rows starting or
stopping).

**What data does each instance consist of?**
Average journey duration; counts of scheduled, cancelled,
late-departing and late-arriving trains; counts of arrival delays
beyond 15, 30 and 60 minutes; average delays at departure and
arrival; the percentage breakdown of six delay causes (external,
infrastructure, traffic management, rolling stock, station
management, passenger handling); a free-text delay comment. Column
names stay in French for traceability with the source schema.

**Is there a label or target?**
No. The dataset is descriptive; no target variable is provided.

**Is any information missing?**
`commentaires_retard_arrivee` is missing on 94.6% of rows
(12,167/12,865 after cleaning). Comments exist only in 2018-2019
(698 rows) and publication stopped entirely from 2020 onwards: the
missingness is Missing Not At Random (MNAR), commented months being
markedly more severe. No imputation is performed, and the presence
of a comment must never be used as a variable.

**Are relationships between instances made explicit?**
Yes, through the key (date, departure station, arrival station),
which is unique after cleaning. Directional pairs (A→B vs B→A)
exist and are distinct observations.

**Are there recommended data splits?**
No predefined split. For any forecasting use, splits must be
chronological (train on the past, test on the future).

**Are there errors, noise or redundancies?**
Yes, all identified and documented during cleaning:
2 fully empty columns; 42 duplicated National/International pairs
(2025-07 to 2025-09); 13 pre-COVID rows violating the delay-counter
hierarchy; a 2025 SNCF publication bug affecting 354 values of the
>30 min counter; 1 row (2025-03) with an inconsistent >15 min
counter; 80 rows with delayed trains but no cause breakdown; 10 rows
with a partial cause breakdown. See section 4 for the treatment of
each.

**Is the dataset self-contained?**
Yes, a single CSV file. Refreshing it relies on the SNCF portal
export API, which is an external resource SNCF maintains.

**Confidential, offensive or sensitive data?**
None. The data is aggregate and operational; it contains no
personal data. The remaining questions of the template that apply
only to datasets relating to people are skipped.

## 3. Collection process

**How was the data associated with each instance acquired?**
Directly measured by SNCF operational systems. Arrival times are
determined by sensors detecting the train at the station entry
point (exceptionally by manual tracking); measurement precision is
one minute, rounded down.

**What mechanisms or procedures were used?**
Monthly aggregation per route from SNCF operational records, then
publication on the open data portal. A train counts as on time
("régularité composite") if its arrival delay is under 5 min for a
journey under 1h30, under 10 min between 1h30 and 3h, and under
15 min beyond 3h.

**Who was involved in the collection?**
SNCF operational and open data teams. No crowdworkers.

**Over what timeframe was the data collected?**
Publication is monthly and continuous since January 2018. The
version used here was exported in November 2026 and covers up to
September 2026.

**Ethical review processes?**
Not applicable (no personal data).

## 4. Preprocessing / cleaning

All decisions below were taken case by case in the reference
notebook (`notebooks/EDA.ipynb`) and ported to
`src/ia700_project/cleaning.py`. No row is ever deleted; every
correction is documented.

**Summary of operations:**
* Dropped the 2 columns with no value at all:
  `commentaire_annulation`, `commentaire_retards_depart`.
* `date` parsed as monthly datetime, rows sorted chronologically.
  No derived year/month columns (obtained on the fly with
  `df["date"].dt.year` / `.month`).
* Missing comments kept as is (MNAR, no imputation).
* Duplicates: 42 National/International pairs (same month and
  route, 2025-07 to 2025-09 only, linked to the opening of the
  French rail market to competition) merged into a single
  `National` row: counters summed, averages and percentages merged
  as train-volume weighted means, comments concatenated. This turns
  12,907 rows into 12,865 rows with a unique key.
* COVID period (April-December 2020): 73 rows with 0 scheduled
  train kept and documented; they must be excluded from rate
  computations (filter `nb_train_prevu > 0`).
* Pre-COVID anomalies: 13 rows (2018-01 to 2019-12) where the >15
  min counter exceeds the total arrival-delay counter. Left
  unchanged: a hypothetical correction would move the national
  delay rate only from 14.6583% to 14.6595%, changing no
  conclusion. The sensitivity check is part of the notebook.
* Post-COVID anomalies (2025): the row where more trains are
  delayed >30 min than >15 min (Tours → Paris Montparnasse,
  2025-03) gets `nb_train_retard_sup_15` set to NA; the 354 rows
  where more trains are delayed >60 min than >30 min (SNCF
  publication bug concentrated on 2025-01 to 2025-03) get
  `nb_train_retard_sup_30` set to NA. Both are unrecoverable: the
  true counters cannot be reconstructed.
* Cause percentages: rows summing to 100 (±0.1 pt) are kept
  (12,584); rows with no delayed train and a zero sum are coherent
  and kept (191); rows with delayed trains but a zero sum (80) and
  partial rows below 90% (3) are set to NaN; the 7 partial rows
  above 90% are kept and documented. Renormalizing to 100% was
  explicitly rejected: it would invent a cause for the unclassified
  trains. Total: 83 rows converted.
* Outliers: none removed. Extreme values are real documented events
  (heatwaves of July 2018 and 2022, the December 2019 strike, the
  April 2020 lockdown, the worst national month with 31.7% of
  trains delayed).

**Was the raw data saved in addition to the cleaned data?**
Yes. The raw export is kept in `data/raw/` (git-ignored) and the
cleaned data is exported to `data/processed/`.

**Is the cleaning software available?**
Yes: the reference notebook `notebooks/EDA.ipynb` and the reusable
module `src/ia700_project/cleaning.py`.

## 5. Uses

**Has the dataset been used for any tasks already?**
Yes: exploratory data analysis and cleaning (see section 4). The
project will next use it for punctuality analysis and a Streamlit
web application.

**What other tasks could the dataset be used for?**
Route reliability rankings, seasonal patterns of delays, delay
cause analysis (with the filtering rules below), monthly punctuality
forecasting per route, clustering of routes by punctuality profile,
composite reliability scores.

**What should a consumer know to avoid misuse?**
* The data is aggregated per month and route: it cannot support
  individual-train prediction or any real-time operational use.
* Never aggregate the `prct_cause_*` columns without filtering rows
  first (keep only rows where the causes sum to 100 or where no
  train was delayed).
* Do not build indicators on
  `retard_moyen_trains_retard_sup15`: its semantics are unreliable
  (about 15% of its values are below 15 min, minimum -2.4).
* Never use the presence of a comment as a variable (MNAR).
* Exclude rows with `nb_train_prevu == 0` from rate computations.
* "Delayed" follows SNCF's composite regularity definition
  (section 3); punctuality rates are not directly comparable with
  other networks or countries without harmonizing definitions.

**Are there tasks for which the dataset should not be used?**
Causal inference on delay causes (the breakdown is declarative and
partly missing), benchmarking against non-SNCF networks, legal or
regulatory claims, and any use targeting identifiable people
(the data contains none).

## 6. Distribution

**Will the dataset be distributed to third parties?**
The dataset is already public: SNCF distributes it as open data on
its portal (dataset page:
https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/),
with a CSV export API. It is also referenced on data.gouv.fr. The
project repository does not redistribute the CSV itself: `data/`
CSV files are git-ignored, so consumers download the export from
the portal.

**Under what license?**
The license terms are displayed on the dataset page of the SNCF
portal; consult that page for the current terms before reuse.

**Does the dataset have a DOI?**
None known to the authors of this datasheet.

**When is it distributed?**
Available now; the portal is updated monthly by SNCF.

## 7. Maintenance

**Who supports and maintains the dataset?**
SNCF, through its open data portal.

**How can the maintainer be contacted?**
Through the contact channels of the SNCF open data portal.

**Is there an erratum?**
None published by SNCF. The known quality issues (2025 counter bug,
hierarchy violations, missing cause breakdowns) are documented in
this datasheet and in the reference notebook.

**Will the dataset be updated?**
Yes: SNCF publishes a new month roughly monthly. This project pins
the November 2026 export (up to 2026-09). Re-running the cleaning
pipeline on a newer export may change the row counts and the
anomaly counts documented in section 4.

**Will older versions continue to be supported?**
The portal exposes only the latest version; the project keeps its
own pinned copy in `data/raw/` for reproducibility.

**Can others extend or contribute?**
Contributions to this datasheet and to the cleaning code are
welcome through GitHub issues and pull requests on the project
repository. Dataset-level corrections must be reported to SNCF.
