# IA700_Project - Railnsight
Repository containing the Telecom Paris MS IA project for IA700

This project focuses on data analysis, through a webbapp, of SNCF monthly TGV regularity; available at this link: https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/

Problem tackled by this project: "Aider un voyageur à évaluer la fiabilité d’une liaison TGV selon son trajet et sa période de voyage, afin d’anticiper son risque de retard et/ou d'annulation."

To get the project running, simply run from root:
> streamlit run /ia700_project/streamlit_app.py

Je travaille sur **RailInsight**, un projet de cours IA702 Kit Big Data sur la régularité des TGV. Le dépôt s’appelle `IA700_Project` malgré le nom du cours. Le projet a peu avancé depuis plusieurs semaines. Je veux reprendre la partie Streamlit et obtenir une première page utilisable, avec une structure qui permette d’ajouter les analyses de l’équipe sans réécrire l’interface.

**Problématique proposée :** aider un voyageur à comprendre la fiabilité historique d’une liaison TGV selon son trajet et sa période de voyage. Présente les chiffres comme des observations historiques, pas comme une prédiction pour un train précis.

### Où trouver le projet

- Dépôt GitHub : https://github.com/FaureArm/IA700_Project
- Dépôt de travail sous **WSL Ubuntu** : `/home/armand/MS_IA/IA700/projet/IA700_Project`
- Environnement : Python 3.13, `uv`, `pyproject.toml` et `uv.lock`.
- Depuis la racine du dépôt sous WSL : `uv run streamlit run src/ia700_project/streamlit_app.py`, puis ouvrir `http://localhost:8501`.
- Le dossier Codex « Cours MS » est un miroir de référence ; le vrai dépôt est sous WSL. Les fichiers synchronisés dans `sources/` sont en lecture seule.
- L’énoncé est dans `C:\Users\arman\Downloads\enonce_projet_sncf (1).md`. Les supports sont les quatre PDF du même dossier sur l’environnement, la structure d’un projet Python, la qualité du code et la CI/CD avec Streamlit.

### État constaté le 6 novembre 2026 — à revérifier avant de modifier quoi que ce soit

- Sur GitHub, le dernier commit de `dev` était `8877c9b`, daté du 24 septembre. Le README de `dev` présente encore la problématique comme ouverte. Le notebook utile sur cette branche est `notebooks/eda_aks.ipynb`. Son `exploration_notebook.ipynb` contient surtout le chargement et des statistiques descriptives.
- Sur `exploration_armand`, `notebooks/exploration_notebook.ipynb` contient davantage de nettoyage, de distributions et de séries temporelles. Les deux branches d’exploration ont donc des apports différents.
- Sous WSL, la branche active était `feature/streamlit-creation`, avec le commit local `86feee1`, **un commit en avance** sur sa branche distante. `README.md` et `src/ia700_project/streamlit_utils.py` avaient aussi des modifications non committées. La branche a divergé de `dev`. Préserve le travail local et inspecte les écarts avant toute intégration. Évite de remplacer un notebook par l’autre sans regarder leur contenu.
- Le code Streamlit est déjà réparti entre `streamlit_app.py`, `pages.py`, `sidebar.py`, `dashboards.py`, `indicators.py`, `models.py` et `streamlit_utils.py`, dans `src/ia700_project/`. L’accueil a des filtres par période et par gares, des indicateurs et deux courbes : retard moyen à l’arrivée et taux d’annulation. `Test` affiche un point sur une carte ; `Data quality` est vide. La navigation actuelle est faite avec des boutons et `st.session_state`.
- Le chargement est dupliqué dans `streamlit_app.py` et `pages.py` ; c’est la version de `pages.py`, sans cache, qui est appelée par l’accueil. Plusieurs constantes sont aussi dupliquées. Le modèle `FilterSelection` existe déjà. La classe `LoadedData` est un brouillon avec des noms d’attributs incohérents. L’audit a lu le code de cette version ; il n’a pas relancé l’application après ces changements.

### Données et points à corriger avant d’afficher les résultats

Le CSV local `data/regularite-mensuelle-tgv-aqst.csv` utilise `;` comme séparateur. Il contient **12 544 lignes, 26 colonnes et 130 liaisons orientées**, de janvier 2018 à juin 2026. Il fait environ 2,8 Mo et est ignoré par Git. Le script `download_data.py` existe, mais l’accès aux données depuis un clone propre et depuis l’hébergeur reste à régler.

- **Analyse par liaison :** `eda_aks.ipynb` calcule des classements, des taux et des tendances. Il moyenne les retards sans tenir compte du volume de trains, alors que Streamlit pondère le retard moyen par le nombre de circulations réalisées. Choisis une définition commune. Si on affiche « part des trains ayant circulé avec plus de 15 minutes de retard », le dénominateur est `prévus − annulés`. Le taux d’annulation se calcule par `somme(annulés) / somme(prévus)`. Pour agréger plusieurs lignes, calcule le rapport des sommes. Gère les dénominateurs nuls et les comptes incohérents ; l’audit a relevé 65 lignes où le nombre de retards de plus de 15 minutes dépasse le nombre de circulations réalisées.
- **Nettoyage :** le chargeur actuel garde 12 350 lignes et en écarte 194 avec ses critères. Il exclut notamment les lignes dont le retard moyen est négatif, même du calcul des annulations : vérifie quelles conditions sont nécessaires à chaque indicateur. Il existe 42 groupes mois–gare de départ–gare d’arrivée avec deux observations, chacune de type `Service` différent et avec des chiffres différents. Ne les déduplique pas sur les trois premières colonnes seules.
- **Notebook `exploration_armand` :** après filtrage, il réattribue les dates depuis le tableau brut, ce qui peut décaler les mois. Une correction du type de service peut aussi écraser toute la colonne au lieu de modifier uniquement les lignes concernées. Ne reprends pas ce nettoyage tel quel.
- **Saisonnalité :** les colonnes de causes sont déjà exprimées en pourcentage. Le notebook multiplie encore la moyenne pondérée par 100 et produit des valeurs comme 2 421,50 %. Son `taux_annulation` saisonnier est aussi un nombre brut. Corrige ces calculs avant toute publication de cette analyse ; la saisonnalité peut attendre la première page.

### Ce que je veux faire maintenant

**Priorité : livrer une page « Explorer une liaison » qui fonctionne de bout en bout.** Commence par vérifier l’état de Git et les fichiers, puis aide-moi à partir du code existant pour :

1. Réunir le travail Streamlit et l’EDA de `dev` sur une branche d’intégration en préservant mes changements locaux. Pas de push ni de déploiement sans demande explicite.
2. Centraliser le chargement et la validation du CSV. Faire en sorte que la sidebar fournisse une `FilterSelection`, que les calculs dans `indicators.py` restent indépendants de Streamlit et que le dashboard reçoive un tableau mensuel aux colonnes stables. Je préfère une fonction pour la sidebar et une dataclass pour les choix ; pas besoin de classes `Sidebar` ou `Title` sans raison concrète.
3. Afficher le **taux d’annulation** et la **part des trains ayant circulé avec plus de 15 minutes de retard**, avec les volumes, la période couverte et un message si les données manquent. Garde le retard moyen s’il apporte quelque chose au récit.
4. Vérifier un parcours réel, par exemple **Bordeaux Saint-Jean → Paris Montparnasse** : changer la période doit mettre à jour les graphiques et les chiffres doivent correspondre au tableau qui les alimente.

La suite : démarrer depuis un clone propre, fournir le CSV à l’application, mettre en ligne sur Streamlit Community Cloud et compléter le rendu du cours. L’échéance de l’énoncé est le **20 novembre à 23 h 59**. Le rendu demande notamment un dépôt GitHub public, une application déployée, des tests avec un seuil de couverture de 90 %, une CI GitHub Actions, une documentation Sphinx et des logs. L’intégration du déploiement dans la CI est optionnelle. La carte, le classement composite et une architecture générique de graphiques peuvent attendre.

Explique-moi les décisions en français, avec des exemples tirés du projet. Je veux comprendre le flux de données et pouvoir modifier moi-même les filtres et les graphiques ensuite.