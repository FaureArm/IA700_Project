# 🚆 TGV Punctuality — Data Exploration & Analysis

> **Exploring the punctuality of the French TGV network through data.**

This project is developed as part of the **RailInsight** project, whose goal is to build an interactive web application for exploring and understanding the punctuality of the French TGV network.

At this stage, we are in the **Data Exploration phase**: we are discovering, cleaning and understanding the dataset before defining the main question that will drive our analysis.

---

## 📌 Project Overview

The French railway operator **SNCF** publishes monthly open data describing the regularity of TGV services.

The dataset provides information about TGV connections, including:

* 🚄 Number of scheduled trains
* ❌ Number of cancelled trains
* 🕐 Delays at departure
* 🕐 Delays at arrival
* 📊 Average delay durations
* 🛠️ Causes of delays
* 🗺️ Origin and destination stations
* 📅 Monthly observations

The reported causes of delays include infrastructure issues, rolling stock, traffic management, station management, passenger handling, external causes and other operational factors.

Our objective is to turn this raw data into meaningful insights and, ultimately, an **interactive Streamlit web application** accessible to a general audience.

---

## 🔎 Current Phase — Data Exploration

We are currently **exploring the dataset before defining our research question**.

Our first step is to understand what the data contains and identify potentially interesting patterns.

### Current objectives

* Understand the structure of the dataset
* Inspect available variables
* Identify missing or inconsistent values
* Analyse the distribution of the main variables
* Explore relationships between delays, cancellations and connections
* Investigate how punctuality varies across routes and over time
* Understand the different causes of delays
* Identify promising directions for further analysis

At this point, **no final research question has been selected yet**.

The analysis will progressively guide us towards a relevant and data-driven research question.

---

## 💡 Possible Research Directions

The dataset offers several potential directions for investigation.

For example:

* Which TGV routes are the least reliable, and does their performance change over time?
* Is there a relationship between journey duration and the probability of delays or cancellations?
* Do the causes of delays vary depending on the season?
* Are some departure stations associated with a higher concentration of delays?
* Can TGV routes be grouped according to their punctuality profiles?
* Can we construct a reliability score combining cancellation rates and average delays?
* Can we predict whether a train will experience a significant delay based on the month and route?

These are **exploratory ideas rather than final research questions**. The final direction will be selected after investigating the data.

---

## 📊 Dataset

The project uses the SNCF open dataset:

**Régularité mensuelle TGV**

The dataset is available through the SNCF open data platform:

[SNCF Open Data — Régularité mensuelle TGV](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/?utm_source=chatgpt.com)

Each observation corresponds to a **month and a TGV connection** (departure station → arrival station), with information about scheduled services, cancellations, delays and delay causes.

---

## 🧪 Exploratory Data Analysis

Our exploration currently focuses on several questions:

### Dataset structure

Understanding:

* Number of observations
* Number of variables
* Data types
* Temporal coverage
* Number of unique routes and stations

### Data quality

Investigating:

* Missing values
* Duplicates
* Unexpected values
* Outliers
* Consistency between related variables

### Punctuality

Exploring:

* Departure delay rates
* Arrival delay rates
* Average delays
* Cancellation rates
* Differences between routes

### Delay causes

Studying the relative contribution of:

* Infrastructure
* Rolling stock
* Traffic management
* Station management
* Passenger handling
* External causes

### Temporal patterns

Looking for potential variations:

* Across months
* Across seasons
* Over longer periods

---

## 🏗️ Project Roadmap

The project will progressively evolve through the following stages:

```text
┌──────────────────────────┐
│  1. Data Exploration     │
│        CURRENT           │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  2. Research Question    │
│     & Analysis Strategy  │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  3. Data Analysis        │
│  & Statistical Insights  │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  4. Visualizations       │
│  & Data Storytelling     │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  5. Streamlit Web App    │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  6. Testing & CI/CD      │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  7. Documentation        │
│  & Deployment            │
└──────────────────────────┘
```

The final application is expected to combine data analysis with an accessible and interactive user experience, including visualizations and potentially interactive filters, maps or other widgets.

---

## 🖥️ Final Application

The final goal is to develop an interactive **Streamlit** web application that allows users to explore the punctuality of the French TGV network.

Depending on the direction selected during the analysis phase, the application may include:

* 📈 Interactive charts
* 🗺️ Interactive maps
* 🚄 Route-level exploration
* 📅 Time-period filters
* 🛠️ Delay-cause filters
* 📊 Key performance indicators
* 🔍 Data-driven insights

The exact features will be defined once the main research question has been established.

---

## 🛠️ Tech Stack

The project is built around the following technologies:

| Technology        | Purpose                                 |
| ----------------- | --------------------------------------- |
| 🐍 Python         | Data analysis & application development |
| 🐼 Pandas         | Data manipulation                       |
| 📊 Plotly         | Interactive visualizations              |
| 🎈 Streamlit      | Web application                         |
| 🧪 Pytest         | Unit testing                            |
| 📚 Sphinx         | Documentation                           |
| 🔄 GitHub Actions | CI/CD                                   |
| 🐙 Git & GitHub   | Version control & collaboration         |

The project requirements also include type hinting, PEP 8 compliance, exception handling, logging, testing and automated CI checks.

---

## 📁 Project Structure

The repository will progressively be organized around a modular Python architecture.

```text
.
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   └── ...
│
├── notebooks/
│   └── ...
│
├── tests/
│   └── ...
│
├── docs/
│   └── ...
│
├── app.py
├── pyproject.toml
├── README.md
└── .github/
    └── workflows/
```

The exact structure may evolve as the project progresses.

---

## 🚧 Project Status

**Current status: 🟡 Data Exploration**

| Stage                 |     Status     |
| --------------------- | :------------: |
| Project setup         |       🟢       |
| Dataset acquisition   |       🟢       |
| Data exploration      | 🟡 **Current** |
| Research question     |        ⚪       |
| Data analysis         |        ⚪       |
| Visualizations        |        ⚪       |
| Streamlit application |        ⚪       |
| Unit tests            |        ⚪       |
| CI/CD                 |        ⚪       |
| Documentation         |        ⚪       |
| Deployment            |        ⚪       |

> **Next step:** continue exploring the dataset and identify a research question that can be meaningfully answered with the available data.

---

## 🎯 Project Goals

Beyond producing an analysis, this project aims to demonstrate good practices in Python development and collaborative software engineering.

We will progressively work on:

* Clean and modular code
* Object-oriented programming where appropriate
* Type hints
* PEP 8 compliance
* Exception handling
* Logging
* Unit testing
* Test coverage
* Documentation
* Continuous integration
* Collaborative Git workflows
* Deployment

The project requirements target, among other things, automated tests and a **minimum 90% test coverage**.

---

## 🚀 Getting Started

Installation and usage instructions will be added as the project develops.

Once the application is ready, the expected workflow will be:

```bash
# Clone the repository
git clone <repository-url>

# Install dependencies
# ...

# Run the Streamlit application
streamlit run app.py
```

---

## 📖 Documentation

Project documentation will be generated using **Sphinx** and will cover the main components, classes, methods and functions of the project.

Documentation is part of the final project requirements.

---

## 🌐 Deployment

The final Streamlit application will be deployed so that it can be accessed publicly.

Potential deployment platforms include:

* Streamlit Cloud

The final deployment URL will be added here once available.

---

## 📌 Disclaimer

This project is developed for educational purposes as part of a data analysis and Python development project.

The research question, analytical methodology and final conclusions will be defined progressively as we explore the dataset.

---

<p align="center">
  🚆 <strong>Exploring TGV punctuality, one dataset at a time.</strong>
</p>
