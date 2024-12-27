# RCEMP-DIAL
Multi-Agent Based Scheduling Algorithm for Dialysis
RCEMP-DIAL (Regulator, Customer, Environment, Maintainers and Producers - Dialysis)

# Project Structure for Multi-Agent Scheduling Research

```plaintext
project/
├── algorithms/             # Différents algorithmes d'ordonnancement
│   ├── __init__.py
│   ├── base.py             # Classe de base pour les algorithmes
│   ├── rcemp/
│   │   ├── __init__.py
│   │   ├── agents.py       # Agents spécifiques à l'algorithme RCEMP
│   │   ├── env.py          # Environnement spécifique à l'algorithme RCEMP
│   │   └── model.py        # Logique de l'algorithme RCEMP
│   ├── rcemp_dial/
│   │   ├── __init__.py
│   │   ├── agents.py       # Agents spécifiques à l'algorithme RCEMP-DIAL
│   │   ├── env.py          # Environnement spécifique à l'algorithme RCEMP-DIAL
│   │   └── model.py        # Logique de l'algorithme RCEMP-DIAL
├── benchmarks/             # Définition des schémas de base de données
│   ├── __init__.py
│   ├── generators.py       # Script pour peupler la base de données
│   ├── metrics.py          # Métriques d'évaluation des algorithmes
│   └── models.py           # Définition des tables et ORM avec SQLAlchemy
├── data/
│   ├── benchmarks.db       # Base de données SQLite ou autre (via SQLAlchemy)
│   ├── processed/          # Données nettoyées ou préparées pour les analyses
│   └── raw/                # Données brutes collectées via SQL
├── notebooks/
│   ├── data_analysis.ipynb # Jupyter Notebooks pour l'analyse des données
│   ├── experiments.ipynb   # Jupyter Notebooks pour vos expérimentations
│   └── visualization.ipynb # Jupyter Notebooks pour la visualisation des résultats
├── scripts/
│   ├── compare_algorithms.py # Script pour comparer les algorithmes
│   ├── data_collection.py  # Scripts pour collecter et stocker les données
│   └── run_simulation.py   # Script pour exécuter une simulation Mesa
├── tests/
│   ├── test_agents.py      # Tests unitaires pour les agents
│   ├── test_algorithms.py  # Tests unitaires pour les algorithmes
│   ├── test_databases.py   # Tests unitaires pour les schémas SQLAlchemy
│   └── test_metrics.py     # Tests unitaires pour les métriques
├── utils/                  # Fonctions utilitaires communes
│   ├── __init__.py
│   └── helpers.py
├── config.py               # Configuration globale (chemins, paramètres, etc.)
├── README.md               # Documentation de base du projet
├── requirements.txt        # Liste des dépendances (Mesa, SQLAlchemy, pandas, etc.)
├── run.py                  # demarrage des scripts
```

## Key Components

### `data/`
- **benchmarks.db**: La base de données SQLite ou une autre base de données prise en charge par SQLAlchemy.
- **processed/**: Contient les données nettoyées ou transformées pour l'analyse.
- **raw/**: Stocke les données brutes collectées via SQL.

### `notebooks/`
- Regroupe des notebooks Jupyter pour l'analyse, la visualisation et les expérimentations.

### `algorithms/`
- Contient les modèles d'algorithmes d'ordonnancement, chacun avec ses propres agents, environnement et logique :
  - `rcemp/`: Dossier pour l'algorithme RCEMP.
    - `agents.py`: Définit les agents spécifiques.
    - `env.py`: Définit l'environnement spécifique.
    - `model.py`: Implémente la logique de l'algorithme.
  - `rcemp_dial/`: Dossier pour l'algorithme RCEMP-DIAL.
    - `agents.py`: Définit les agents spécifiques.
    - `env.py`: Définit l'environnement spécifique.
    - `model.py`: Implémente la logique de l'algorithme.
  - `base.py`: Fournit une classe de base pour standardiser les algorithmes.

### `benchmarks/`
- Gère les schémas de base de données et les scripts de peuplement.

### `utils/`
- Fonctions utilitaires communes.

### `scripts/`
- **compare_algorithms.py**: Compare les algorithmes d'ordonnancement sur des benchmarks.
- **data_collection.py**: Collecte et stocke les données dans la base de données.
- **run_simulation.py**: Exécute une simulation multi-agents.

### `tests/`
- Inclut des tests unitaires pour les différentes composantes du projet.

## Étapes Suivantes
1. Complétez `generators.py` pour initialiser la base de données.
2. Implémentez chaque algorithme comme une sous-classe de `base.py`.
3. Ajoutez des métriques personnalisées dans `metrics.py`.
4. Utilisez `compare_algorithms.py` pour exécuter les benchmarks et générer un rapport comparatif.
