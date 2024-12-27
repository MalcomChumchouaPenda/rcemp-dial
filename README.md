# RCEMP-DIAL
Multi-Agent Based Scheduling Algorithm for Dialysis
RCEMP-DIAL (Regulator, Customer, Environment, Maintainers and Producers - Dialysis)

project/
├── data/
│   ├── raw/                # Données brutes collectées via SQL
│   ├── processed/          # Données nettoyées ou préparées pour les analyses
│   └── benchmarks.db       # Base de données SQLite ou autre (via SQLAlchemy)
├── notebooks/
│   ├── data_analysis.ipynb # Jupyter Notebooks pour l'analyse des données
│   ├── visualization.ipynb # Jupyter Notebooks pour la visualisation des résultats
│   └── experiments.ipynb   # Jupyter Notebooks pour vos expérimentations
├── src/
│   ├── agents/             # Code des agents dans Mesa
│   │   ├── __init__.py
│   │   └── agent.py        # Classe principale des agents
│   ├── environments/       # Code des environnements multi-agents
│   │   ├── __init__.py
│   │   └── environment.py  # Définition de l'environnement
│   ├── algorithms/         # Différents algorithmes d'ordonnancement
│   │   ├── __init__.py
│   │   ├── model1.py       # Algorithme d'ordonnancement modèle 1
│   │   ├── model2.py       # Algorithme d'ordonnancement modèle 2
│   │   └── base_model.py   # Classe de base pour les algorithmes
│   ├── database/           # Définition des schémas de base de données
│   │   ├── __init__.py
│   │   ├── models.py       # Définition des tables et ORM avec SQLAlchemy
│   │   └── seed_data.py    # Script pour peupler la base de données
│   ├── evaluation/         # Comparaison des algorithmes
│   │   ├── __init__.py
│   │   ├── metrics.py      # Métriques d'évaluation des algorithmes
│   │   └── comparer.py     # Comparaison des performances
│   └── utils/              # Fonctions utilitaires communes
│       ├── __init__.py
│       └── helpers.py
├── scripts/
│   ├── data_collection.py  # Scripts pour collecter et stocker les données
│   ├── run_simulation.py   # Script pour exécuter une simulation Mesa
│   └── compare_algorithms.py # Script pour comparer les algorithmes
├── tests/
│   ├── test_algorithms.py  # Tests unitaires pour les algorithmes
│   ├── test_database.py    # Tests unitaires pour les schémas SQLAlchemy
│   ├── test_agents.py      # Tests unitaires pour les agents
│   └── test_metrics.py     # Tests unitaires pour les métriques
├── requirements.txt        # Liste des dépendances (Mesa, SQLAlchemy, pandas, etc.)
├── README.md               # Documentation de base du projet
└── config.py               # Configuration globale (chemins, paramètres, etc.)
