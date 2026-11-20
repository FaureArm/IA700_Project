# RAILNSIGHT

<p align="center">
  <img src="https://img.shields.io/badge/RAILNSIGHT-RELIABILITY%20INTELLIGENCE-E60000?style=for-the-badge" alt="Railnsight">
  <img src="https://img.shields.io/badge/PYTHON-3.13-172B4D?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/STREAMLIT-APPLICATION-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/COVERAGE-95.13%25-16865B?style=for-the-badge" alt="Coverage">
</p>

<p align="center">
  <strong>DATA-DRIVEN INSIGHTS INTO FRENCH HIGH-SPEED RAIL RELIABILITY</strong>
</p>

<p align="center">
  An interactive analytics platform dedicated to exploring, understanding and comparing the historical performance of SNCF TGV connections.
</p>

<p align="center">
  <a href="https://github.com/FaureArm/IA700_Project">PROJECT REPOSITORY</a>
  &nbsp; | &nbsp;
  <a href="https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/">OFFICIAL SNCF DATASET</a>
  &nbsp; | &nbsp;
  <a href="datasheet.md">DATASET DATASHEET</a>
</p>

---

## 01 | PROJECT OVERVIEW

**Railnsight** is a data analytics web application developed as part of the Mastère Spécialisé® IA Multimodale & Autonome at Télécom Paris.

The platform transforms historical SNCF railway performance data into interactive visual insights. It provides travelers with a structured way to investigate the reliability of TGV connections, identify recurring disruptions and compare service performance across routes and periods.

### The Challenge

Railway reliability varies across connections and over time. Delays, cancellations and operational disruptions can significantly affect the passenger experience.

Railnsight addresses the following objective:

> Help travelers assess the reliability of a TGV connection based on their route and travel period, enabling them to better anticipate the risk of delays and cancellations.

### Our Approach

The application combines data collection, data cleaning, statistical analysis, historical performance indicators and geographic visualization to make railway reliability easier to understand.

---

## 02 | APPLICATION FEATURES

Railnsight is organized into seven dedicated analytical dashboards.

### 01. Network Overview

<sub>GEOGRAPHIC ANALYSIS</sub>

An interactive representation of the TGV network, providing a high-level view of railway connectivity and performance.

- Interactive geographic map of TGV connections.
- Color-coded representation of connection performance.
- Number of railway connections and stations.
- Network-level reliability indicators.

### 02. Journey Exploration

<sub>CONNECTION-LEVEL ANALYSIS</sub>

A detailed analysis of a selected railway connection over a chosen historical period.

- Selection of a specific TGV connection and travel period.
- Scheduled train volumes.
- Cancellation rate and delay rate.
- Average delay indicators.
- Historical performance evolution.
- Ranking and analysis of delay causes.

### 03. Connection Comparison

<sub>COMPARATIVE PERFORMANCE</sub>

A comparative view designed to identify differences in reliability across railway connections.

- Ranking of connections using performance indicators.
- Comparison of routes and stations.
- Historical performance trends.
- Identification of differences in service reliability.

### 04. Data Sources

<sub>DATA TRANSPARENCY</sub>

An overview of the datasets used throughout the application.

- Original SNCF data source.
- Dataset structure and characteristics.
- Information about the data used for analysis.

### 05. Data Cleaning

<sub>DATA PREPARATION</sub>

A dedicated environment for understanding and demonstrating the data preparation process.

- Identification of inconsistent records.
- Implementation of data consistency rules.
- Specific historical data corrections.
- Interactive examples illustrating cleaning operations.

### 06. Data Quality

<sub>DATA VALIDATION</sub>

An overview of the controls implemented to assess the consistency and reliability of the processed dataset.

- Data quality checks.
- Validation indicators.
- Detailed explanations of quality controls.

### 07. Methodology

<sub>ANALYTICAL FRAMEWORK</sub>

Documentation of the analytical concepts and indicators used throughout Railnsight.

- Definitions of delay and cancellation indicators.
- Explanation of performance metrics.
- Methodological choices and analytical principles.

---

## 03 | DATA SOURCE

The application uses data from the official SNCF Open Data platform.

**Dataset:** Monthly TGV Regularity (AQST)

[ACCESS THE OFFICIAL SNCF DATASET](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/)

The dataset provides historical monthly information on TGV regularity, including delays, cancellations and their reported causes.

All analytical outputs are based on available historical observations. They describe past performance and should not be interpreted as guaranteed predictions of future train punctuality.

---

## 04 | DATA COLLECTION & DATASHEET

Transparency and data traceability are essential to the Railnsight project.

Beyond the application itself, we documented the dataset acquisition process, its structure, its limitations and the preprocessing decisions applied before analysis.

The project includes a dedicated **Datasheet** describing the SNCF monthly TGV regularity dataset (AQST).

### Datasheet Documentation

The datasheet provides detailed information about:

| Section | Documentation |
|:--|:--|
| Motivation | Dataset purpose, original authors and funding source |
| Composition | Observations, attributes, coverage period and missing values |
| Collection Process | Data acquisition, aggregation and publication frequency |
| Preprocessing | Data cleaning rules, corrections and validation decisions |
| Uses | Analytical applications and potential future uses |
| Distribution | Dataset availability and distribution |
| Maintenance | Dataset updates and version information |

Particular attention is given to historical inconsistencies, COVID-period observations, SNCF publication anomalies, duplicated records and delay-cause percentages.

### Full Documentation

<p align="center">
  <a href="datasheet.md">
    <img src="https://img.shields.io/badge/READ%20THE-DATASET%20DATASHEET-E60000?style=for-the-badge&logo=readthedocs&logoColor=white" alt="Read the Datasheet">
  </a>
</p>

The datasheet provides the methodological foundation for understanding the processed dataset and the analytical decisions implemented in Railnsight.

---

## 05 | TECHNOLOGY STACK

The application is built around a Python-based data analytics stack.

| Technology | Role |
|:--|:--|
| Python 3.13 | Core programming language |
| Streamlit | Interactive application framework |
| Pandas | Data processing and analysis |
| PyDeck | Geographic visualization |
| uv | Dependency and environment management |
| Ruff | Code quality and formatting |
| Pytest | Automated testing |
| GitHub Actions | Continuous integration |

---

## 06 | INSTALLATION & EXECUTION

### Requirements

- Python 3.13
- uv package manager

Installation instructions: [uv documentation](https://docs.astral.sh/uv/)

### Step 01. Clone the repository

```bash
git clone https://github.com/FaureArm/IA700_Project.git
cd IA700_Project
```

### Step 02. Install dependencies

```bash
uv sync --locked
```

### Step 03. Launch Railnsight

```bash
uv run streamlit run src/ia700_project/streamlit_app.py
```

Once Streamlit has started, open the local application:

**http://localhost:8501**

---

## 07 | TESTING & CODE QUALITY

Code reliability is supported by an automated testing suite covering the main application components, data processing functions and analytical logic.

### Test Execution

Run the complete test suite:

```bash
uv run pytest
```

Generate a detailed coverage report:

```bash
uv run pytest --cov=ia700_project --cov-report=term-missing
```

### Static Analysis

Run Ruff lint checks:

```bash
uv run ruff check .
```

Verify code formatting:

```bash
uv run ruff format --check .
```

### Quality Report

<p align="center">
  <img src="https://img.shields.io/badge/UNIT_TESTS-168%20PASSED-16865B?style=for-the-badge" alt="168 tests passed">
  <img src="https://img.shields.io/badge/CODE_COVERAGE-95.13%25-16865B?style=for-the-badge" alt="95.13 percent coverage">
  <img src="https://img.shields.io/badge/RUFF-LINT%20PASSED-16865B?style=for-the-badge" alt="Ruff lint passed">
  <img src="https://img.shields.io/badge/FORMATTING-PASSED-16865B?style=for-the-badge" alt="Formatting passed">
</p>

| Metric | Latest Result |
|:--|--:|
| Automated tests | 168 passed |
| Overall code coverage | 95.13% |
| Required coverage threshold | 90% |
| Ruff linting | Passed |
| Ruff formatting | Passed |

<sub>Results obtained from the latest full local test execution.</sub>

---

## 08 | CONTINUOUS INTEGRATION

Railnsight uses GitHub Actions to automate code quality checks and test execution.

The CI workflow is triggered by:

- Pushes to the `dev` branch.
- Pull requests targeting the `dev` branch.

### Automated Pipeline

| Stage | Validation |
|:--|:--|
| 01 | Repository checkout |
| 02 | uv and Python 3.13 installation |
| 03 | Dependency installation using the lockfile |
| 04 | Ruff lint validation |
| 05 | Ruff formatting validation |
| 06 | Automated unit tests |

The pipeline provides a consistent validation process before changes are integrated into the development branch.

---

## 09 | REPOSITORY ARCHITECTURE

```text
IA700_Project/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── data/
│   └── map/
│
├── notebooks/
│   └── EDA.ipynb
│
├── src/
│   └── ia700_project/
│       ├── cleaning.py
│       ├── dashboards.py
│       ├── data.py
│       ├── indicators.py
│       ├── map_rates.py
│       ├── map_view.py
│       ├── methods_examples.py
│       ├── models.py
│       ├── pages.py
│       ├── sidebar.py
│       └── streamlit_app.py
│
├── unit_tests/
│   ├── test_cleaning.py
│   ├── test_dashboards.py
│   ├── test_data.py
│   ├── test_indicators.py
│   ├── test_map_rates.py
│   ├── test_map_view.py
│   ├── test_models.py
│   ├── test_pages.py
│   ├── test_sidebar.py
│   └── test_streamlit_app.py
│
├── datasheet.md
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 10 | PROJECT INFORMATION

### Academic Context

| | |
|:--|:--|
| Project | Railnsight |
| Institution | Télécom Paris |
| Programme | Mastère Spécialisé® IA Multimodale & Autonome |
| Course | Python for Production |
| Dataset | SNCF Monthly TGV Regularity (AQST) |
| Repository | [IA700_Project](https://github.com/FaureArm/IA700_Project) |

### Project Team

Railnsight was designed and developed collaboratively by:

| Team Member | GitHub Profile |
|:--|:--|
| **Armand FAURE** | [@FaureArm](https://github.com/FaureArm) |
| **Florian COLLARD** | [@Alreven](https://github.com/Alreven) |
| **Mathieu DONNADILLE** | [@mdonnadi](https://github.com/mdonnadi) |
| **Aksil IRBOUH** | [@Aksil-Irbouh](https://github.com/Aksil-Irbouh) |

---

<p align="center">
  <img src="https://img.shields.io/badge/RAILNSIGHT-172B4D?style=for-the-badge" alt="Railnsight">
</p>

<p align="center">
  <strong>TURNING RAILWAY DATA INTO MEANINGFUL INSIGHTS.</strong>
</p>

<p align="center">
  Developed at Télécom Paris as part of the Mastère Spécialisé® IA Multimodale & Autonome.

</p>

<p align="center">
  <sub>Independent academic project. Not affiliated with or endorsed by SNCF.</sub>
</p>