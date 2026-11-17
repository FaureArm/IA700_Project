# IA700_Project - Railnsight
Repository containing the Telecom Paris MS IA project for IA700

This project focuses on data analysis, through a webbapp, of SNCF monthly TGV regularity; available at this link: https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/

Problem tackled by this project: "Aider un voyageur à évaluer la fiabilité d’une liaison TGV selon son trajet et sa période de voyage, afin d’anticiper son risque de retard et/ou d'annulation."

To get the project running, simply run from root:
> uv run streamlit run src/ia700_project/streamlit_app.py


Pages to do:


Main page: map showing summary, colour coded, key figures, etc
Exploration page: Select a specific liaison, dates, etc and prints back summary of perturbations, lateness, etc; timeline, extra analysis, etc
Comparer les liaisons: ranking of liaison, train stations, over timelines, volumes, etc to interpret and compare results
Données et méthodes: specify sources, definition, methods used, cleaning, etc
