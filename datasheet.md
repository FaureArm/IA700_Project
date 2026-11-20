# Datasheet - Régularité mensuelle TGV (AQST)

This datasheet documents the SNCF open dataset *Régularité mensuelle
TGV par liaisons* as used by the Kit Big Data project. 

| Item | Value |
| --- | --- |
| Dataset | Régularité mensuelle TGV par liaisons |
| Version used | CSV export retrieved in November 2026 |
| Raw size | 12,907 rows × 26 columns |
| Period covered | 2018-01 to 2026-09 |
| Cleaned size | 12,865 rows × 24 columns |
| Datasheet authors | Faure Armand, Irbouh Aksil, Collard Florian, Donnadille Mathieu |
| Reference implementation | `notebooks/EDA.ipynb`, `src/ia700_project/cleaning.py` |

## 1. Motivation

**Purpose of the original dataset**
SNCF publishes this dataset monthly on its open data portal to document the regularity
 of its TGV services. In this project it is used to explore
and explain TGV punctuality through an interactive Streamlit application.

**Original Dataset Authors**
SNCF, published on the SNCF open data portal
(ressources.data.sncf.com) and referenced on data.gouv.fr.

**Funding source**
SNCF.

## 2. Composition

**Instances meaning**
One instance is one month × one directional TGV route (departure
station → arrival station). The same route appears once per month.

**Number of instances**
12,907 raw rows in the version used, covering January 2018 to
September 2026. After cleaning: 12,865 rows.

**Dataset Completeness**
It is a raw complet dataset, not a sample of it

**Attributes of Instances**
Average journey duration; counts of scheduled, cancelled,
late-departing and late-arriving trains; counts of arrival delays
beyond 15, 30 and 60 minutes; average delays at departure and
arrival; the percentage breakdown of six delay causes (external,
infrastructure, traffic management, rolling stock, station
management, passenger handling); a free-text delay comment.

**Labels and targets**
Instances have no labels and do not designate a target 

**Missing cells**
`commentaires_retard_arrivee` is missing on 94.6% of rows
(12,167/12,865 after cleaning). Comments exist only in 2018-2019
(698 rows) and publication stopped entirely from 2020 onwards. The
missingness is Missing Not At Random (MNAR), commented months being
markedly more severe.

**Relationship between instances**
Yes, through the key date, departure station, and arrival station,
Directional pairs (A→B vs B→A) exist and are distinct observations.

**Splits recommandation**
No predefined split.

**Errors, noises and redundancies**
- 2 fully empty columns
- 42 duplicated National/International pairs (2025-07 to 2025-09)
- 13 pre-COVID rows number of trains with a delay above 15 minutes was above the total number of trains delayed
- a 2025 SNCF publication bug affecting 354 values in the number of trains with a delay above 60 minutes above the number of trains with a delay above 30 minutes
- 1 row (2025-03) with more delays departure than operated trains  
- 80 rows with delayed trains but no cause breakdown
- 10 rows with a partial cause breakdown. 
See section 4 for the treatment of each.

**Dataset Self-Containment**
The dataset consist in a single CSV file.

**Confidentiality, Sensitive and Offensive Content in the Data**
None. 

## 3. Collection process

**Data acquisition**
Directly measured by SNCF.

**Data aggregation methods**
Monthly aggregation per route, then publication on the open data portal

**Data Collection Stakeholders**
SNCF.

**Timeframe**
Publication is monthly and continuous since January 2018. The
version used here was exported in November 2026 and covers up to
September 2026.


## 4. Preprocessing / cleaning

All decisions below were taken case by case in the reference
notebook (`notebooks/EDA.ipynb`) and ported to
`src/ia700_project/cleaning.py`

**Summary of operations:**
* Dropped the 2 columns with no value at all:
  `commentaire_annulation`, `commentaire_retards_depart`.
* `date` parsed as monthly datetime, rows sorted chronologically.
  No derived year/month columns (obtained on the fly with
  `df["date"].dt.year` / `.month`).
* Missing comments kept as is.
* Duplicates: 42 National/International pairs (same month and
  route, 2025-07 to 2025-09 only, linked to the opening of the
  French rail market to competition) merged into a single
  `National` row. counters summed, averages and percentages merged
  as train-volume weighted means, comments concatenated. This turns
  12,907 rows into 12,865 rows.
* COVID period (April-December 2020): 73 rows with 0 scheduled
  train kept.
* Pre-COVID anomalies: 13 rows (2018-01 to 2019-12) where the >15
  min counter exceeds the total arrival-delay counter. We decided 
  to apply an adjustment so that the total number of delayed trains 
  would not be less than the number of trains delayed by more than
  15 minutes. This makes these instances more consistent.  
* Post-COVID anomalies (2025): the row where more trains are
  delayed above 30 min than above 15 min. It is not possible to reconstruct or correct this metric.
   And given the number of items to correct, doing so would risk introducing 
   a significant bias into our analysis. We therefore prefer to replace
  these values with NaN values.
* Cause percentages: rows summing to 100 (±0.1 pt) are kept.
  Rows with delayed trains but a zero sum (80) and
  partial rows below 90% (3) are set to NaN; the 7 partial rows
  above 90% are kept.
* Average delay: `average_delay_all_departing_trains` and `average_delay_all_arriving_trains` have negative values (277). `average_delay_on_arrival` has two negative values. There are 38 instances where `average_delay_on_arrival` equals 0, even though `number_of_trains_with_delay_on_arrival` is not zero. Without any further information about the data, it is impossible for us to determine the average delay. We therefore treat every anomaly all-train average as an aberration. We replace all of them with NaN, as well as the single zero all-train mean with delayed trains. `retard_moyen_trains_retard_sup15` a des valeurs en dessous de 15 minutes et des valeurs non nulles alors que `nb_train_retard_arrivee` vaut zéro. The rows with trains delayed below 15 min are floored to 15, and the rows without any train delayed above 15 min should have a mean of 0, so they are replaced with 0.
* Outliers: none removed. Some extreme values are real documented events
  (heatwaves of July 2018, the December 2019 strike, the
  April 2020 lockdown)


**Cleaning data procedure**
With the reusable module `src/ia700_project/cleaning.py`.

## 5. Uses

**Dataset usage**
The project will next use it for punctuality analysis and a Streamlit
web application.

**Other possible usage**
Route reliability rankings, seasonal patterns of delays, delay
cause analysis, monthly punctuality, forecasting per route,
 clustering of routes by punctuality profile, composite reliability scores.


## 6. Distribution

**Dataset distribution**
The dataset is public:
https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/

**DOI**
None known 

## 7. Maintenance

**Dataset Maintenance**
SNCF, through its open data portal.

**Erratum**
None erratum published by SNCF. 

**Frequence of update**
SNCF publishes a new month roughly monthly

**Older dataset versions**
The portal exposes only the latest version
